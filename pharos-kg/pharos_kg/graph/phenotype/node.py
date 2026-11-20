"""A phenotype observed for a kinase in a model system."""

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
from pharos_kg.graph.annotations import BiolinkClass, KeyPrefix, OntologyTerm


class PhenotypeNode(AnnotatedNode, Node):

    options = NodeOptions(
        name="phenotype",
        annotations=(
            BiolinkClass("biolink:PhenotypicFeature"),
            OntologyTerm("MP:0000001"),
            KeyPrefix(('MP:', 'MPATH:')),
            NodeLabel("Phenotype"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the observed phenotype when the question is what a model with a "
                "perturbed kinase looks like, rather than which disease it causes.",
                limitations=(
                    Limitation(
                        "The phenotype is observed in a model organism, usually the "
                        "mouse ortholog, not in the human protein."
                    ),
                    Limitation(
                        "A phenotype is not a disease and does not imply one."
                    ),
                    Limitation(
                        "The release carries no Mammalian Phenotype hierarchy, so a "
                        "parent term is not implied."
                    ),
                ),
            ),
            claims=(
                Claim(
                    "A phenotype node is a Mammalian Phenotype term, or a Mouse "
                    "Pathology term when the release reports a pathology finding."
                ),
                Claim(
                    "The top-level term is the release's coarser grouping, not a "
                    "parent inferred by this project."
                ),
            ),
        ),
    )

    phenotype_key: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The MP term identity, such as MP:0005385."),
                Claim("Use for graph identity."),
            ),
        ),
    )
    label: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The phenotype term name."),
                Claim("Use for display and search."),
            ),
        ),
    )
    top_level_key: PropertySlot[str | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The coarser MP term the release groups this one under."),
                Claim("Use to browse phenotypes by system."),
            ),
        ),
    )
    top_level_label: PropertySlot[str | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The name of the coarser MP term."),
                Claim("Use for display."),
            ),
        ),
    )
