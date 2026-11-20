"""Bind the protein_interaction_pair relation to the interacts_with edge."""

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
from pharos_kg.graph.protein.interacts_with__protein import InteractsWithEdge
from pharos_kg.relation.derived.protein_interaction_pair.relation import (
    ProteinInteractionPair,
)


interacts_binding = edge_binding(
    target=InteractsWithEdge,
    rows=ProteinInteractionPair.row_source(),
    bind=lambda row: EdgeValues(
        build_key=row.source_target_key.prepend("PHAROS:")
        .append("::INTERACTS_WITH::")
        .append(row.target_target_key.prepend("PHAROS:")),
        source_build_key=row.source_target_key.prepend("PHAROS:"),
        target_build_key=row.target_target_key.prepend("PHAROS:"),
        properties=InteractsWithEdge(
            **unannotated(),
            score=row.score,
            sources=row.sources,
            p_int=row.p_int,
            p_ni=row.p_ni,
            evidence_class=row.evidence_class,
        ),
    ),
    name="interacts_with",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The protein_interaction_pair relation fulfils the INTERACTS WITH use "
                "as an unordered link between two kinases: each row supplies one edge, "
                "keyed by the canonical endpoint ids, covering every pair the project "
                "threshold admits.",
                limitations=(
                    Limitation(
                        "The experimental/predicted distinction is an edge property, "
                        "so a model that wants it as a relation type must expand the "
                        "property at export."
                    ),
                ),
            ),
            claims=(
                Claim("One protein_interaction_pair row produces one edge."),
                Claim("The evidence class is carried, not used to split the relation."),
            ),
        ),
    ),
)
