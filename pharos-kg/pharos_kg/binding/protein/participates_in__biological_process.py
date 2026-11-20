"""Bind the go_annotation relation to the participates_in edge."""

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
from pharos_kg.graph.protein.participates_in__biological_process import ParticipatesInEdge
from pharos_kg.relation.derived.protein_go_pair.relation import ProteinGoPair


participates_binding = edge_binding(
    target=ParticipatesInEdge,
    rows=ProteinGoPair.row_source(),
    bind=lambda row: EdgeValues(
        build_key=row.target_key.prepend("PHAROS:")
        .append("::PARTICIPATES_IN::")
        .append(row.go_key)
        .append("::")
        .append(row.evidence),
        source_build_key=row.target_key.prepend("PHAROS:"),
        target_build_key=row.go_key,
        properties=ParticipatesInEdge(**unannotated(), evidence=row.evidence),
    ),
    name="participates_in",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The protein_go_pair relation fulfils the PARTICIPATES IN use as an "
                "annotation link from a kinase to a GO term: each row supplies one "
                "edge, keyed by the target, term and evidence code, covering every "
                "annotation the extract names.",
                limitations=(
                    Limitation(
                        "The annotation is not a statement of causal mechanism."
                    ),
                ),
            ),
            claims=(
                Claim("One go_annotation row produces one participates_in edge."),
            ),
        ),
    ),
)
