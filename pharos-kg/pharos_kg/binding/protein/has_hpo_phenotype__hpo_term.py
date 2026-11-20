"""Bind the protein_hpo_phenotype_pair relation to the kinase phenotype edge."""

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
from pharos_kg.graph.protein.has_hpo_phenotype__hpo_term import (
    HasHpoPhenotypeEdge,
)
from pharos_kg.relation.derived.protein_hpo_phenotype_pair.relation import (
    ProteinHpoPhenotypePair,
)


protein_hpo_phenotype_binding = edge_binding(
    target=HasHpoPhenotypeEdge,
    rows=ProteinHpoPhenotypePair.row_source(),
    bind=lambda row: EdgeValues(
        build_key=row.uniprot.prepend("PHAROS:")
        .append("::HAS_HPO_PHENOTYPE::")
        .append(row.hpo_id),
        source_build_key=row.uniprot.prepend("PHAROS:"),
        target_build_key=row.hpo_id,
        properties=HasHpoPhenotypeEdge(
            **unannotated(),
            recording_diseases=row.recording_diseases,
            annotation_count=row.annotation_count,
        ),
    ),
    name="has_hpo_phenotype",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The protein_hpo_phenotype_pair relation fulfils the HAS HPO "
                "PHENOTYPE use as the link from a kinase to what its variants "
                "produce: each row supplies one edge, keyed by the protein and the "
                "term.",
                limitations=(
                    Limitation(
                        "An edge is a recorded observation in a cohort, not a "
                        "penetrance estimate."
                    ),
                ),
            ),
            claims=(
                Claim("One protein_hpo_phenotype_pair row produces one edge."),
                Claim("The recording diseases are a property, not edges."),
            ),
        ),
    ),
)
