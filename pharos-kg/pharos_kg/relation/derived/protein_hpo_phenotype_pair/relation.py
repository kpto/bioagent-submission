"""One row per kinase and HPO phenotype term."""

from kg_build_system import (
    Array,
    Claim,
    Contract,
    Definition,
    DerivedRelation,
    DerivedRelationOptions,
    FieldDefinition,
    Limitation,
    Meaning,
    Omitted,
    Purpose,
    computed_field,
)

from pharos_kg.modules.row_operations import protein_hpo_phenotypes
from pharos_kg.relation.derived.gene_phenotype_graph.relation import (
    GenePhenotypeGraph,
)

rows = GenePhenotypeGraph.row_source().custom_op(protein_hpo_phenotypes)


class ProteinHpoPhenotypePair(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="protein_hpo_phenotype_pair",
        contract=Contract(
            definition=Definition(
                grain="one row per kinase and phenotype term",
                identity=("uniprot", "hpo_id"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State which phenotypes a kinase's variants are recorded with, "
                    "once per phenotype, so the edge is one statement rather than one "
                    "row per cohort.",
                    limitations=(
                        Limitation(
                            "The edge states the phenotype was recorded for the gene, "
                            "not that every variant produces it."
                        ),
                        Limitation(
                            "The recording diseases are context; the edge does not "
                            "claim the kinase causes them."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one kinase and one phenotype term."),
                    Claim("annotation_count states how many rows the pair aggregates."),
                ),
            ),
        ),
    )

    uniprot = computed_field(rows.shape.uniprot, meaning=Omitted)
    hpo_id = computed_field(rows.shape.hpo_id, meaning=Omitted)
    recording_diseases = computed_field(
        rows.shape.recording_diseases,
        definition=FieldDefinition(
            "The distinct diseases the annotations were recorded in.",
            null_meaning="Absent when no annotation names a disease.",
        ),
        meaning=Omitted,
    )
    annotation_count = computed_field(
        rows.shape.annotation_count, meaning=Omitted
    )
