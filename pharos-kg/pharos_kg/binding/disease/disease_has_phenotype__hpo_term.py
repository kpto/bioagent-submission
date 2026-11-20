"""Bind the disease_phenotype_graph relation to the disease phenotype edge."""

from kg_build_system import (
    BindingOptions,
    Claim,
    EdgeValues,
    Limitation,
    Meaning,
    Purpose,
    edge_binding,
)

from pharos_kg.graph.annotated import unannotated
from pharos_kg.graph.disease.disease_has_phenotype__hpo_term import (
    DiseaseHasPhenotypeEdge,
)
from pharos_kg.relation.derived.disease_phenotype_graph.relation import (
    DiseasePhenotypeGraph,
)


disease_phenotype_binding = edge_binding(
    target=DiseaseHasPhenotypeEdge,
    rows=DiseasePhenotypeGraph.row_source(),
    bind=lambda row: EdgeValues(
        build_key=row.disease_key.append("::DISEASE_HAS_PHENOTYPE::").append(row.hpo_id),
        source_build_key=row.disease_key,
        target_build_key=row.hpo_id,
        properties=DiseaseHasPhenotypeEdge(
            **unannotated(),
            frequencies=row.frequencies,
            annotation_count=row.annotation_count,
            evidence=row.evidence,
        ),
    ),
    name="disease_has_phenotype",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The disease_phenotype_graph relation fulfils the HAS PHENOTYPE use "
                "from a disease to what it looks like: each row supplies one edge, "
                "keyed by the disease and the term, covering every annotated disease "
                "the graph publishes.",
                limitations=(
                    Limitation(
                        "An edge is a recorded observation, not a diagnostic "
                        "criterion."
                    ),
                ),
            ),
            claims=(
                Claim("One disease_phenotype_graph row produces one edge."),
            ),
        ),
    ),
)
