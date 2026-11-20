"""Bind the protein_anatomy_pair relation to the expressed_in edge."""

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
from pharos_kg.graph.protein.expressed_in__anatomical_entity import ExpressedInEdge
from pharos_kg.relation.derived.protein_anatomy_pair.relation import (
    ProteinAnatomyPair,
)


expressed_in_binding = edge_binding(
    target=ExpressedInEdge,
    rows=ProteinAnatomyPair.row_source(),
    bind=lambda row: EdgeValues(
        build_key=row.target_key.prepend("PHAROS:")
        .append("::EXPRESSED_IN::")
        .append(row.anatomical_key),
        source_build_key=row.target_key.prepend("PHAROS:"),
        target_build_key=row.anatomical_key,
        properties=ExpressedInEdge(
            **unannotated(),
            sources=row.sources,
            level=row.level,
            count=row.count,
        ),
    ),
    name="expressed_in",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The protein_anatomy_pair relation fulfils the EXPRESSED IN use as a "
                "detection link from a kinase to an anatomical structure: each row "
                "supplies one edge, keyed by target and structure, covering every "
                "strong or medium protein-level detection the slice reaches.",
                limitations=(
                    Limitation(
                        "Transcript evidence and weak detections are excluded by the "
                        "relation's policy, so a location supported only by RNA is "
                        "not an edge."
                    ),
                ),
            ),
            claims=(
                Claim("One protein_anatomy_pair row produces one edge."),
            ),
        ),
    ),
)
