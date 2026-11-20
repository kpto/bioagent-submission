"""A curated pathway a kinase is a member of."""

from kg_build_system import (
    Claim,
    Limitation,
    Meaning,
    Node,
    NodeLabel,
    NodeOptions,
    PropertySlot,
    Purpose,
    property,
)

from pharos_kg.graph.annotated import AnnotatedNode
from pharos_kg.graph.annotations import BiolinkClass, KeyPrefix


class PathwayNode(AnnotatedNode, Node):

    options = NodeOptions(
        name="pathway",
        annotations=(
            BiolinkClass("biolink:Pathway"),
            KeyPrefix(('Reactome:', 'WikiPathways:', 'KEGG:', 'PathwayCommons:', 'panther.pathway:',)),
            NodeLabel("Pathway"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the curated pathway when the question is which process a kinase "
                "takes part in according to a pathway database.",
                limitations=(
                    Limitation(
                        "Pathway membership is a database's curation, not an observed "
                        "physical interaction."
                    ),
                    Limitation(
                        "Different pathway databases describe overlapping biology with "
                        "different boundaries and names."
                    ),
                    Limitation(
                        "The release carries no pathway hierarchy, so a parent pathway "
                        "is not implied."
                    ),
                ),
            ),
            claims=(
                Claim(
                    "A pathway node is one pathway record from one source database."
                ),
                Claim(
                    "The same biology curated by two databases is two nodes, because "
                    "the release states no equivalence."
                ),
            ),
        ),
    )

    pathway_key: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim(
                    "The pathway identity as a CURIE, such as Reactome:R-HSA-164843."
                ),
                Claim("Use for graph identity."),
            ),
        ),
    )
    label: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The pathway name the source database states."),
                Claim("Use for display and search."),
            ),
        ),
    )
    source: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim(
                    "The database that curates the pathway, such as Reactome, KEGG or "
                    "WikiPathways."
                ),
                Claim("Use to separate database perspectives."),
            ),
        ),
    )
    source_id: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The identifier the source database uses."),
                Claim("Use to look the pathway up in its own database."),
            ),
        ),
    )
    url: PropertySlot[str | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The page the release links for the pathway."),
                Claim("Use for traceability; the target may move."),
            ),
        ),
    )
