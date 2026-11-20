"""Bind the target_disease_pair relation to the associated_with edge."""

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
from pharos_kg.graph.protein.associated_with__disease import AssociatedWithEdge
from pharos_kg.relation.derived.target_disease_annotation.relation import (
    TargetDiseaseAnnotation,
)


associated_binding = edge_binding(
    target=AssociatedWithEdge,
    rows=TargetDiseaseAnnotation.row_source(),
    bind=lambda row: EdgeValues(
        build_key=row.target_key.prepend("PHAROS:")
        .append("::ASSOCIATED_WITH::")
        .append(row.disease_key),
        source_build_key=row.target_key.prepend("PHAROS:"),
        target_build_key=row.disease_key,
        properties=AssociatedWithEdge(
            **unannotated(),
            evidence_types=row.evidence_types,
            sources=row.sources,
            max_conf=row.max_conf,
            max_score=row.max_score,
            evidence_count=row.evidence_count,
            evidence_class=row.evidence_class,
        ),
    ),
    name="associated_with",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The target_disease_annotation relation fulfils the ASSOCIATED WITH use as "
                "the link from a kinase target to a disease: each row supplies one "
                "edge, keyed by the target and disease identities, covering every "
                "pair the release reports for the kinase family.",
                limitations=(
                    Limitation(
                        "An association is not a treatment, a mechanism or a clinical "
                        "claim."
                    ),
                    Limitation(
                        "evidence_count is the number of contribution rows, so the "
                        "edge states how much a source wrote, not how strong the "
                        "association is."
                    ),
                ),
            ),
            claims=(
                Claim("One target_disease_pair row produces one associated_with edge."),
                Claim("No pair is dropped for having few contribution rows."),
            ),
        ),
    ),
)
