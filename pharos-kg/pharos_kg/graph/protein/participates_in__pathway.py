"""A kinase is a member of a curated pathway."""

from kg_build_system import (
    Claim,
    Edge,
    EdgeLabel,
    EdgeOptions,
    Limitation,
    Meaning,
    PropertySlot,
    Purpose,
    property,
)

from pharos_kg.graph.annotated import AnnotatedEdge
from pharos_kg.graph.annotations import BiolinkPredicate
from pharos_kg.graph.pathway.node import PathwayNode
from pharos_kg.graph.protein.node import ProteinNode


class ParticipatesInPathwayEdge(AnnotatedEdge, Edge[ProteinNode, PathwayNode]):

    options = EdgeOptions(
        name="participates_in_pathway",
        annotations=(
            BiolinkPredicate("biolink:participates_in"),
            EdgeLabel("PARTICIPATES_IN_PATHWAY"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the pathway membership when the question is which curated "
                "process a kinase belongs to.",
                limitations=(
                    Limitation(
                        "Membership is a database's curation and does not state that "
                        "the kinase acts in the pathway in a particular cell or time."
                    ),
                    Limitation(
                        "Databases draw pathway boundaries differently, so the same "
                        "kinase can belong to several overlapping pathways."
                    ),
                    Limitation(
                        "No direction, complex member role or causal position is "
                        "carried."
                    ),
                ),
            ),
            claims=(
                Claim("The edge is one kinase in one source database's pathway."),
                Claim("The source database and its identifier are carried."),
            ),
        ),
    )

    source: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The database that curates the pathway."),
                Claim("Use to separate Reactome, KEGG, WikiPathways and PathwayCommons."),
            ),
        ),
    )
    url: PropertySlot[str | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The page the release links for the pathway."),
                Claim("Use for traceability."),
            ),
        ),
    )
    count: PropertySlot[int] = property(
        meaning=Meaning(
            claims=(
                Claim("The number of release rows asserting the membership."),
                Claim("Use to see repeated curation of the same pair."),
            ),
        ),
    )
