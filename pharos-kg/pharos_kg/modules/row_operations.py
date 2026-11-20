"""The project's relation operations: grouped target-disease rows.

These are the operations the competition graph needs from the framework's
relation-operation surface. Each names one operation, the exact shape of the
rows it produces and its grain; the SQL that computes them lives beside the
declaration, in the emitter the project supplies to the DuckDB engine.
"""

from __future__ import annotations

from kg_build_system import (
    Array,
    Nullable,
    RelationOperation,
    RelationOperationSpec,
    Selection,
    Shape,
)
from kg_build_system.distribution.languages.data.model.internal.dto import (
    RowOperationDTO,
)
from kg_build_system.distribution.modules.duckdb import RowSourceEmissionContext

PAIR_SQL = """
SELECT
  target_key AS target_key,
  coalesce(
    CASE WHEN mondo_id IS NULL OR mondo_id = '' THEN NULL
         WHEN strpos(mondo_id, ':') > 0 THEN mondo_id
         ELSE 'MONDO:' || mondo_id END,
    CASE WHEN did IS NOT NULL AND strpos(did, ':') > 0 THEN did END,
    'NAME:' || coalesce(
      nullif(trim(regexp_replace(
        lower(coalesce(nullif(ncats_name, ''), nullif(disease_name, ''), 'unknown')),
        '[^a-z0-9]+', '-', 'g'), '-'), ''),
      'unknown')
  ) AS disease_key,
  target_key || '|' || coalesce(
    CASE WHEN mondo_id IS NULL OR mondo_id = '' THEN NULL
         WHEN strpos(mondo_id, ':') > 0 THEN mondo_id
         ELSE 'MONDO:' || mondo_id END,
    CASE WHEN did IS NOT NULL AND strpos(did, ':') > 0 THEN did END,
    'NAME:' || coalesce(
      nullif(trim(regexp_replace(
        lower(coalesce(nullif(ncats_name, ''), nullif(disease_name, ''), 'unknown')),
        '[^a-z0-9]+', '-', 'g'), '-'), ''),
      'unknown')
  ) AS pair_key,
  count(*) AS evidence_count,
  CAST(max(conf) AS DOUBLE) AS max_conf,
  CAST(max(score) AS DOUBLE) AS max_score,
  coalesce(
    list(DISTINCT evidence_type ORDER BY evidence_type)
      FILTER (WHERE evidence_type IS NOT NULL), []) AS evidence_types,
  coalesce(
    list(DISTINCT evidence_source ORDER BY evidence_source)
      FILTER (WHERE evidence_source IS NOT NULL), []) AS sources
FROM {source}
GROUP BY target_key, disease_key
"""

LABEL_SQL = """
SELECT
  coalesce(
    CASE WHEN mondo_id IS NULL OR mondo_id = '' THEN NULL
         WHEN strpos(mondo_id, ':') > 0 THEN mondo_id
         ELSE 'MONDO:' || mondo_id END,
    CASE WHEN did IS NOT NULL AND strpos(did, ':') > 0 THEN did END,
    'NAME:' || coalesce(
      nullif(trim(regexp_replace(
        lower(coalesce(nullif(ncats_name, ''), nullif(disease_name, ''), 'unknown')),
        '[^a-z0-9]+', '-', 'g'), '-'), ''),
      'unknown')
  ) AS disease_key,
  min(nullif(disease_name, '')) AS name,
  min(nullif(ncats_name, '')) AS ncats_name,
  min(nullif(mondo_id, '')) AS mondo_id,
  min(CASE WHEN did LIKE 'DOID:%' THEN did END) AS doid
FROM {source}
GROUP BY disease_key
"""


INTERACTION_SQL = """
SELECT
  least(source_uniprot, target_uniprot) AS source_target_key,
  greatest(source_uniprot, target_uniprot) AS target_target_key,
  count(*) AS row_count,
  max(score) AS score,
  max(p_int) AS p_int,
  max(p_ni) AS p_ni,
  coalesce(
    list(DISTINCT ppitypes ORDER BY ppitypes)
      FILTER (WHERE ppitypes IS NOT NULL), []) AS sources,
  CASE WHEN max(CASE
      WHEN ppitypes IS NOT NULL
       AND trim(replace(replace(ppitypes, 'STRINGDB', ''), ',', '')) <> ''
      THEN 1 ELSE 0 END) = 1
    THEN 'experimental' ELSE 'predicted' END AS evidence_class
FROM {source}
WHERE source_uniprot <> target_uniprot
  -- No policy filter here: the candidate graph carries every reported pair
  -- with its score and sources. The admission decision is an annotator, and
  -- the pruned graph is the projection of the annotated one (CD-0006).
GROUP BY 1, 2
"""


LIGAND_KEY = "ligand_identifier"

LIGAND_TARGET_SQL = """
WITH pairs AS (
  SELECT
    'PHAROS:' || {key} AS ligand_key,
    target_key AS target_key,
    count(act_value) AS count,
    round(avg(act_value), 6) AS mean_p_activity,
    round(coalesce(stddev_pop(act_value), 0.0), 6) AS std,
    min(act_value) AS min_p_activity,
    max(act_value) AS max_p_activity,
    coalesce(list_sort(list_distinct(flatten(
      list(string_split(pubmed_ids, ','))))), []) AS pmids,
    coalesce(list_sort(list(DISTINCT reference)
      FILTER (WHERE reference IS NOT NULL)), []) AS references
  FROM {source}
  GROUP BY 1, 2
), per_ligand AS (
  SELECT ligand_key, count(*) AS target_count FROM pairs GROUP BY 1
)
-- Every measured pair is a candidate edge: the compound's target count is
-- carried as evidence, and the single-target exclusion is an annotator rule
-- (CD-0006). No ligand is dropped here.
SELECT p.ligand_key, p.target_key, l.target_count, p.count, p.mean_p_activity,
       p.std, p.min_p_activity, p.max_p_activity, p.pmids, p.references
FROM pairs p
JOIN per_ligand l ON l.ligand_key = p.ligand_key
"""

LIGAND_LABEL_SQL = """
WITH activity AS (
  SELECT
    'PHAROS:' || {key} AS ligand_key,
    target_key,
    compound_name,
    smiles,
    pubchem,
    isdrug,
    chembl
  FROM {source}
), per_ligand AS (
  SELECT ligand_key, count(DISTINCT target_key) AS target_count
  FROM activity
  GROUP BY 1
)
-- Every ligand the release names is a candidate node, with the number of
-- kinases it was measured against. Which compounds enter the graph is an
-- annotator decision, not a property of this relation.
SELECT
  a.ligand_key AS ligand_key,
  any_value(l.target_count) AS target_count,
  any_value(a.compound_name) AS name,
  any_value(a.smiles) AS smiles,
  max(try_cast(a.pubchem AS BIGINT)) AS pubchem_cid,
  CAST(any_value(a.isdrug) AS BOOLEAN) AS isdrug,
  any_value(a.chembl) AS chembl_id
FROM activity a
JOIN per_ligand l ON l.ligand_key = a.ligand_key
GROUP BY 1
"""


GENE_KEY_SQL = """
SELECT
  CASE WHEN strpos(hgnc_value, ':') > 0 THEN hgnc_value
       ELSE 'HGNC:' || hgnc_value END AS gene_key,
  target_key AS target_key,
  symbol AS symbol
FROM {source}
WHERE hgnc_value IS NOT NULL
"""

GENE_LABEL_SQL = """
SELECT
  gene_key AS gene_key,
  any_value(symbol) AS symbol,
  count(*) AS protein_count
FROM {source}
GROUP BY 1
"""


PROTEIN_GO_SQL = """
SELECT
  target_key AS target_key,
  go_key AS go_key,
  coalesce(evidence, 'unspecified') AS evidence,
  count(*) AS count,
  coalesce(list_sort(list(DISTINCT assigned_by)
    FILTER (WHERE assigned_by IS NOT NULL)), []) AS assigners
FROM {source}
GROUP BY 1, 2, 3
"""

GO_LABEL_SQL = """
SELECT
  go_key AS go_key,
  any_value(label) AS label,
  any_value(aspect) AS aspect
FROM {source}
GROUP BY 1
"""


PROTEIN_LABEL_SQL = """
SELECT
  uniprot AS uniprot,
  any_value(symbol) AS symbol,
  any_value(name) AS name,
  any_value(description) AS description,
  any_value(tdl) AS tdl,
  any_value(family) AS family,
  CAST(NULL AS DOUBLE) AS novelty
FROM {source}
GROUP BY 1
"""


PROTEIN_PHENOTYPE_SQL = """
SELECT
  target_key AS target_key,
  phenotype_key AS phenotype_key,
  coalesce(
    list(DISTINCT programme ORDER BY programme)
      FILTER (WHERE programme IS NOT NULL), []) AS sources,
  coalesce(
    list(DISTINCT procedure ORDER BY procedure)
      FILTER (WHERE procedure IS NOT NULL), []) AS procedures,
  min(p_value) AS min_p_value,
  count(*) AS count
FROM {source}
WHERE phenotype_key IS NOT NULL
GROUP BY 1, 2
"""

PHENOTYPE_LABEL_SQL = """
SELECT
  phenotype_key AS phenotype_key,
  min(label) AS label,
  min(top_level_key) AS top_level_key,
  min(top_level_label) AS top_level_label
FROM {source}
WHERE phenotype_key IS NOT NULL
GROUP BY 1
"""

PROTEIN_PATHWAY_SQL = """
SELECT target_key, pathway_key, min(source) AS source,
       min(url) AS url, count(*) AS count
FROM (
  SELECT
    target_key AS target_key,
    CASE
      WHEN source IN ('Reactome', 'WikiPathways') THEN source || ':' || source_id
      WHEN source = 'KEGG' THEN 'KEGG:' || replace(source_id, 'path:', '')
      WHEN url LIKE '%pathwaycommons.org%Pathway_%'
        THEN 'PathwayCommons:' || regexp_extract(
          url_decode(url), 'Pathway_([0-9a-f]+)', 1)
      WHEN url LIKE '%identifiers[.]org%'
        THEN regexp_extract(url_decode(url),
               'identifiers[.]org/([^/]+)/([^&]+)', 1)
             || ':' || regexp_extract(url_decode(url),
               'identifiers[.]org/([^/]+)/([^&]+)', 2)
    END AS pathway_key,
    source AS source,
    url AS url
  FROM {source}
) WHERE pathway_key IS NOT NULL
GROUP BY 1, 2
"""

PATHWAY_LABEL_SQL = """
SELECT pathway_key, min(label) AS label, min(source) AS source,
       min(source_id) AS source_id, min(url) AS url
FROM (
  SELECT
    CASE
      WHEN source IN ('Reactome', 'WikiPathways') THEN source || ':' || source_id
      WHEN source = 'KEGG' THEN 'KEGG:' || replace(source_id, 'path:', '')
      WHEN url LIKE '%pathwaycommons.org%Pathway_%'
        THEN 'PathwayCommons:' || regexp_extract(
          url_decode(url), 'Pathway_([0-9a-f]+)', 1)
      WHEN url LIKE '%identifiers[.]org%'
        THEN regexp_extract(url_decode(url),
               'identifiers[.]org/([^/]+)/([^&]+)', 1)
             || ':' || regexp_extract(url_decode(url),
               'identifiers[.]org/([^/]+)/([^&]+)', 2)
    END AS pathway_key,
    label AS label,
    source AS source,
    source_id AS source_id,
    url AS url
  FROM {source}
) WHERE pathway_key IS NOT NULL
GROUP BY 1
"""

PROTEIN_ANATOMY_SQL = """
SELECT target_key, anatomical_key,
       CASE rank WHEN 3 THEN 'High' ELSE 'Medium' END AS level,
       sources, count
FROM (
  SELECT
    target_key AS target_key,
    anatomical_key AS anatomical_key,
    max(CASE level WHEN 'High' THEN 3 WHEN 'Medium' THEN 2 ELSE 0 END) AS rank,
    coalesce(
      list(DISTINCT resource ORDER BY resource)
        FILTER (WHERE resource IS NOT NULL), []) AS sources,
    count(*) AS count
  FROM {source}
  WHERE expressed = 1 AND anatomical_key IS NOT NULL
    AND level IN ('High', 'Medium')
    AND (anatomical_key LIKE 'UBERON:%' OR anatomical_key LIKE 'CL:%')
  GROUP BY 1, 2
)
"""

ANATOMY_LABEL_SQL = """
SELECT
  anatomical_key AS anatomical_key,
  min(label) AS label
FROM {source}
WHERE anatomical_key IS NOT NULL
  AND (anatomical_key LIKE 'UBERON:%' OR anatomical_key LIKE 'CL:%')
GROUP BY 1
"""


class PairRow(Shape):
    target_key: Selection[str]
    disease_key: Selection[str]
    pair_key: Selection[str]
    evidence_count: Selection[int]
    max_conf: Selection[Nullable[float]]
    max_score: Selection[Nullable[float]]
    evidence_types: Selection[Array[str]]
    sources: Selection[Array[str]]


PAIR_ROWS = RelationOperationSpec(
    name="target_disease_pair",
    output=PairRow,
    grain="one_per_group",
)
pair_rows = RelationOperation(PAIR_ROWS)


class LabelRow(Shape):
    disease_key: Selection[str]
    name: Selection[Nullable[str]]
    ncats_name: Selection[Nullable[str]]
    mondo_id: Selection[Nullable[str]]
    doid: Selection[Nullable[str]]


LABEL_ROWS = RelationOperationSpec(
    name="disease_label",
    output=LabelRow,
    grain="one_per_group",
)
label_rows = RelationOperation(LABEL_ROWS)


class LigandTargetRow(Shape):
    ligand_key: Selection[str]
    target_key: Selection[str]
    target_count: Selection[int]
    count: Selection[int]
    mean_p_activity: Selection[Nullable[float]]
    std: Selection[Nullable[float]]
    min_p_activity: Selection[Nullable[float]]
    max_p_activity: Selection[Nullable[float]]
    pmids: Selection[Array[str]]
    references: Selection[Array[str]]


LIGAND_TARGET_PAIRS = RelationOperationSpec(
    name="ligand_target_pair",
    output=LigandTargetRow,
    grain="one_per_group",
)
ligand_target_pairs = RelationOperation(LIGAND_TARGET_PAIRS)


class LigandLabelRow(Shape):
    ligand_key: Selection[str]
    target_count: Selection[int]
    name: Selection[Nullable[str]]
    smiles: Selection[Nullable[str]]
    pubchem_cid: Selection[Nullable[int]]
    isdrug: Selection[Nullable[bool]]
    chembl_id: Selection[Nullable[str]]


LIGAND_LABELS = RelationOperationSpec(
    name="ligand_label",
    output=LigandLabelRow,
    grain="one_per_group",
)
ligand_labels = RelationOperation(LIGAND_LABELS)


class GeneKeyedRow(Shape):
    gene_key: Selection[str]
    target_key: Selection[str]
    symbol: Selection[Nullable[str]]


GENE_KEYS = RelationOperationSpec(
    name="gene_key",
    output=GeneKeyedRow,
    grain="one_per_input_row",
)
gene_keys = RelationOperation(GENE_KEYS)


class GeneLabelRow(Shape):
    gene_key: Selection[str]
    symbol: Selection[Nullable[str]]
    protein_count: Selection[int]


GENE_LABELS = RelationOperationSpec(
    name="gene_label",
    output=GeneLabelRow,
    grain="one_per_group",
)
gene_labels = RelationOperation(GENE_LABELS)


class ProteinLabelRow(Shape):
    uniprot: Selection[str]
    symbol: Selection[Nullable[str]]
    name: Selection[Nullable[str]]
    description: Selection[Nullable[str]]
    tdl: Selection[Nullable[str]]
    family: Selection[Nullable[str]]
    novelty: Selection[Nullable[float]]


PROTEIN_LABELS = RelationOperationSpec(
    name="protein_label",
    output=ProteinLabelRow,
    grain="one_per_group",
)
protein_labels = RelationOperation(PROTEIN_LABELS)


class ProteinGoRow(Shape):
    target_key: Selection[str]
    go_key: Selection[str]
    evidence: Selection[str]
    count: Selection[int]
    assigners: Selection[Array[str]]


PROTEIN_GO_PAIRS = RelationOperationSpec(
    name="protein_go_pair",
    output=ProteinGoRow,
    grain="one_per_group",
)
protein_go_pairs = RelationOperation(PROTEIN_GO_PAIRS)


class GoLabelRow(Shape):
    go_key: Selection[str]
    label: Selection[Nullable[str]]
    aspect: Selection[Nullable[str]]


GO_LABELS = RelationOperationSpec(
    name="go_label",
    output=GoLabelRow,
    grain="one_per_group",
)
go_labels = RelationOperation(GO_LABELS)


class ProteinPhenotypeRow(Shape):
    target_key: Selection[str]
    phenotype_key: Selection[str]
    sources: Selection[Array[str]]
    procedures: Selection[Array[str]]
    min_p_value: Selection[Nullable[float]]
    count: Selection[int]


PROTEIN_PHENOTYPE_PAIRS = RelationOperationSpec(
    name="protein_phenotype_pair",
    output=ProteinPhenotypeRow,
    grain="one_per_group",
)
protein_phenotype_pairs = RelationOperation(PROTEIN_PHENOTYPE_PAIRS)


class PhenotypeLabelRow(Shape):
    phenotype_key: Selection[str]
    label: Selection[Nullable[str]]
    top_level_key: Selection[Nullable[str]]
    top_level_label: Selection[Nullable[str]]


PHENOTYPE_LABELS = RelationOperationSpec(
    name="phenotype_label",
    output=PhenotypeLabelRow,
    grain="one_per_group",
)
phenotype_labels = RelationOperation(PHENOTYPE_LABELS)


class ProteinPathwayRow(Shape):
    target_key: Selection[str]
    pathway_key: Selection[str]
    source: Selection[Nullable[str]]
    url: Selection[Nullable[str]]
    count: Selection[int]


PROTEIN_PATHWAY_PAIRS = RelationOperationSpec(
    name="protein_pathway_pair",
    output=ProteinPathwayRow,
    grain="one_per_group",
)
protein_pathway_pairs = RelationOperation(PROTEIN_PATHWAY_PAIRS)


class PathwayLabelRow(Shape):
    pathway_key: Selection[str]
    label: Selection[Nullable[str]]
    source: Selection[Nullable[str]]
    source_id: Selection[Nullable[str]]
    url: Selection[Nullable[str]]


PATHWAY_LABELS = RelationOperationSpec(
    name="pathway_label",
    output=PathwayLabelRow,
    grain="one_per_group",
)
pathway_labels = RelationOperation(PATHWAY_LABELS)


class ProteinAnatomyRow(Shape):
    target_key: Selection[str]
    anatomical_key: Selection[str]
    level: Selection[str]
    sources: Selection[Array[str]]
    count: Selection[int]


PROTEIN_ANATOMY_PAIRS = RelationOperationSpec(
    name="protein_anatomy_pair",
    output=ProteinAnatomyRow,
    grain="one_per_group",
)
protein_anatomy_pairs = RelationOperation(PROTEIN_ANATOMY_PAIRS)


class AnatomyLabelRow(Shape):
    anatomical_key: Selection[str]
    label: Selection[Nullable[str]]


ANATOMY_LABELS = RelationOperationSpec(
    name="anatomical_label",
    output=AnatomyLabelRow,
    grain="one_per_group",
)
anatomy_labels = RelationOperation(ANATOMY_LABELS)


class InteractionPairRow(Shape):
    source_target_key: Selection[str]
    target_target_key: Selection[str]
    row_count: Selection[int]
    score: Selection[Nullable[float]]
    p_int: Selection[Nullable[float]]
    p_ni: Selection[Nullable[float]]
    sources: Selection[Array[str]]
    evidence_class: Selection[str]


INTERACTION_PAIRS = RelationOperationSpec(
    name="protein_interaction_pair",
    output=InteractionPairRow,
    grain="one_per_group",
)
interaction_pairs = RelationOperation(INTERACTION_PAIRS)


class PharosRowOperations:
    """Emit the SQL for every relation operation this project declares."""

    node_type = RowOperationDTO

    def emit(
        self, plan: RowOperationDTO, context: RowSourceEmissionContext,
    ) -> str:
        source = context.relation_for(plan.input)
        if plan.operation == PROTEIN_HPO_PHENOTYPES.name:
            return PROTEIN_HPO_SQL.format(source=source).strip()
        if plan.operation == DISEASE_PHENOTYPES.name:
            return DISEASE_PHENOTYPE_SQL.format(source=source).strip()
        if plan.operation == HP_TERM_LABELS.name:
            return HP_TERM_LABEL_SQL.format(source=source).strip()
        if plan.operation == EVIDENCE_CLASSES.name:
            return EVIDENCE_CLASS_SQL.format(source=source).strip()
        if plan.operation == PAIR_ROWS.name:
            return PAIR_SQL.format(source=source).strip()
        if plan.operation == LABEL_ROWS.name:
            return LABEL_SQL.format(source=source).strip()
        if plan.operation == INTERACTION_PAIRS.name:
            return INTERACTION_SQL.format(source=source).strip()
        if plan.operation == LIGAND_TARGET_PAIRS.name:
            return LIGAND_TARGET_SQL.format(
                source=source, key=LIGAND_KEY,
            ).strip()
        if plan.operation == PROTEIN_LABELS.name:
            return PROTEIN_LABEL_SQL.format(source=source).strip()
        if plan.operation == PROTEIN_GO_PAIRS.name:
            return PROTEIN_GO_SQL.format(source=source).strip()
        if plan.operation == GO_LABELS.name:
            return GO_LABEL_SQL.format(source=source).strip()
        if plan.operation == GENE_KEYS.name:
            return GENE_KEY_SQL.format(source=source).strip()
        if plan.operation == GENE_LABELS.name:
            return GENE_LABEL_SQL.format(source=source).strip()
        if plan.operation == LIGAND_LABELS.name:
            return LIGAND_LABEL_SQL.format(source=source, key=LIGAND_KEY).strip()
        if plan.operation == PROTEIN_PHENOTYPE_PAIRS.name:
            return PROTEIN_PHENOTYPE_SQL.format(source=source).strip()
        if plan.operation == PHENOTYPE_LABELS.name:
            return PHENOTYPE_LABEL_SQL.format(source=source).strip()
        if plan.operation == PROTEIN_PATHWAY_PAIRS.name:
            return PROTEIN_PATHWAY_SQL.format(source=source).strip()
        if plan.operation == PATHWAY_LABELS.name:
            return PATHWAY_LABEL_SQL.format(source=source).strip()
        if plan.operation == PROTEIN_ANATOMY_PAIRS.name:
            return PROTEIN_ANATOMY_SQL.format(source=source).strip()
        if plan.operation == ANATOMY_LABELS.name:
            return ANATOMY_LABEL_SQL.format(source=source).strip()
        raise ValueError(
            f"no SQL is declared for relation operation {plan.operation!r}"
        )


__all__ = [
    "PROTEIN_PHENOTYPE_PAIRS",
    "PHENOTYPE_LABELS",
    "ProteinPhenotypeRow",
    "PhenotypeLabelRow",
    "protein_phenotype_pairs",
    "phenotype_labels",
    "PROTEIN_PATHWAY_PAIRS",
    "PATHWAY_LABELS",
    "ProteinPathwayRow",
    "PathwayLabelRow",
    "protein_pathway_pairs",
    "pathway_labels",
    "PROTEIN_ANATOMY_PAIRS",
    "ANATOMY_LABELS",
    "ProteinAnatomyRow",
    "AnatomyLabelRow",
    "protein_anatomy_pairs",
    "anatomy_labels",
    "PROTEIN_LABELS",
    "ProteinLabelRow",
    "protein_labels",
    "GENE_KEYS",
    "GeneKeyedRow",
    "gene_keys",
    "GO_LABELS",
    "PROTEIN_GO_PAIRS",
    "GoLabelRow",
    "ProteinGoRow",
    "go_labels",
    "protein_go_pairs",
    "GENE_LABELS",
    "GeneLabelRow",
    "gene_labels",
    "INTERACTION_PAIRS",
    "LIGAND_LABELS",
    "LIGAND_TARGET_PAIRS",
    "LigandLabelRow",
    "LigandTargetRow",
    "ligand_labels",
    "ligand_target_pairs",
    "InteractionPairRow",
    "LABEL_ROWS",
    "interaction_pairs",
    "evidence_classes",
    "disease_phenotype_pairs",
    "protein_hpo_phenotypes",
    "hp_term_labels",
    "PAIR_ROWS",
    "LabelRow",
    "PairRow",
    "PharosRowOperations",
    "label_rows",
    "pair_rows",
]


EVIDENCE_CLASS_SQL = """
SELECT
  target_key || '|' || disease_key AS pair_key,
  CASE
    WHEN count(*) FILTER (
      WHERE datatype IN ('genetic_association', 'somatic_mutation',
                         'known_drug')) > 0 THEN 'high'
    WHEN count(*) FILTER (WHERE datatype IS NOT NULL) > 0 THEN 'literature_only'
    ELSE 'none'
  END AS evidence_class
FROM {source}
GROUP BY 1
"""


class EvidenceClassRow(Shape):
    pair_key: Selection[str]
    evidence_class: Selection[str]


EVIDENCE_CLASSES = RelationOperationSpec(
    name="ot_evidence_pair",
    output=EvidenceClassRow,
    grain="one_per_group",
)
evidence_classes = RelationOperation(EVIDENCE_CLASSES)


DISEASE_PHENOTYPE_SQL = """
SELECT
  disease_key AS disease_key,
  hpo_id AS hpo_id,
  max(evidence) AS evidence,
  coalesce(
    list(DISTINCT frequency ORDER BY frequency)
      FILTER (WHERE frequency IS NOT NULL), []) AS frequencies,
  count(*) AS annotation_count
FROM {source}
GROUP BY 1, 2
"""


class DiseasePhenotypeRow(Shape):
    disease_key: Selection[str]
    hpo_id: Selection[str]
    evidence: Selection[Nullable[str]]
    frequencies: Selection[Array[str]]
    annotation_count: Selection[int]


DISEASE_PHENOTYPES = RelationOperationSpec(
    name="disease_phenotype_pair",
    output=DiseasePhenotypeRow,
    grain="one_per_group",
)
disease_phenotype_pairs = RelationOperation(DISEASE_PHENOTYPES)


HP_TERM_LABEL_SQL = """
SELECT
  hpo_id AS hpo_id,
  max(name) AS name
FROM {source}
GROUP BY 1
"""


class HpoTermLabelRow(Shape):
    hpo_id: Selection[str]
    name: Selection[Nullable[str]]


HP_TERM_LABELS = RelationOperationSpec(
    name="hpo_term_label",
    output=HpoTermLabelRow,
    grain="one_per_group",
)
hp_term_labels = RelationOperation(HP_TERM_LABELS)


PROTEIN_HPO_SQL = """
SELECT
  uniprot AS uniprot,
  hpo_id AS hpo_id,
  coalesce(
    list(DISTINCT disease_id ORDER BY disease_id)
      FILTER (WHERE disease_id IS NOT NULL), []) AS recording_diseases,
  count(*) AS annotation_count
FROM {source}
GROUP BY 1, 2
"""


class ProteinHpoPhenotypeRow(Shape):
    uniprot: Selection[str]
    hpo_id: Selection[str]
    recording_diseases: Selection[Array[str]]
    annotation_count: Selection[int]


PROTEIN_HPO_PHENOTYPES = RelationOperationSpec(
    name="protein_hpo_phenotype_pair",
    output=ProteinHpoPhenotypeRow,
    grain="one_per_group",
)
protein_hpo_phenotypes = RelationOperation(PROTEIN_HPO_PHENOTYPES)
