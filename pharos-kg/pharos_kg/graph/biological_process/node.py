"""A Gene Ontology term used by an annotation."""

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


class BiologicalProcessNode(AnnotatedNode, Node):

    options = NodeOptions(
        name="biological_process",
        annotations=(
            BiolinkClass("biolink:BiologicalProcess"),
            OntologyTerm("GO:0008150"),
            KeyPrefix(('GO:',)),
            NodeLabel("Biological process"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the GO term for functional context around a kinase.",
                limitations=(
                    Limitation(
                        "The extract carries no GO hierarchy and no obsolete-term flag."
                    ),
                    Limitation("An annotation does not establish a causal mechanism."),
                ),
            ),
            claims=(
                Claim("A process node is a GO term identity."),
                Claim("The aspect says which GO branch the term belongs to."),
            ),
        ),
    )

    go_key: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The GO term identity."),
                Claim("Use for graph identity."),
            ),
        ),
    )
    label: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The GO term label."),
                Claim("Use for display and search."),
            ),
        ),
    )
    aspect: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim(
                    "The GO branch: biological_process, molecular_function or "
                    "cellular_component."
                ),
                Claim("Use to separate process, function and location questions."),
            ),
        ),
    )
