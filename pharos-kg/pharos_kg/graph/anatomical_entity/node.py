"""An anatomical structure in which a kinase is expressed."""

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


class AnatomicalEntityNode(AnnotatedNode, Node):

    options = NodeOptions(
        name="anatomical_entity",
        annotations=(
            BiolinkClass("biolink:AnatomicalEntity"),
            OntologyTerm("UBERON:0001062"),
            KeyPrefix(('UBERON:', 'CL:')),
            NodeLabel("Anatomical entity"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the anatomical structure when the question is where a kinase is "
                "expressed.",
                limitations=(
                    Limitation(
                        "The release's expression rows mix organ, tissue and cell-type "
                        "granularity under one UBERON identifier."
                    ),
                    Limitation(
                        "An anatomical entity is a location, not a function or a "
                        "disease."
                    ),
                    Limitation(
                        "The release carries no anatomy hierarchy, so a parent "
                        "structure is not implied."
                    ),
                ),
            ),
            claims=(
                Claim(
                    "An anatomical entity node is a UBERON term, or a Cell "
                    "Ontology term when the release states a cell type."
                ),
                Claim(
                    "The label is the release's tissue string, which may name a cell "
                    "type within the structure."
                ),
            ),
        ),
    )

    anatomical_key: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The UBERON term identity, such as UBERON:0001013."),
                Claim("Use for graph identity."),
            ),
        ),
    )
    label: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The tissue label the release states for the structure."),
                Claim("Use for display and search."),
            ),
        ),
    )
