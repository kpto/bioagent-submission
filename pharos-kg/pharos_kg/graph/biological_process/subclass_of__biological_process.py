"""One biological process is a kind of another."""

from kg_build_system import (
    Claim,
    Edge,
    EdgeLabel,
    EdgeOptions,
    Limitation,
    Meaning,
    Purpose,
)

from pharos_kg.graph.annotated import AnnotatedEdge
from pharos_kg.graph.annotations import BiolinkPredicate
from pharos_kg.graph.biological_process.node import BiologicalProcessNode


class ProcessSubclassEdge(AnnotatedEdge, Edge[BiologicalProcessNode, BiologicalProcessNode]):

    options = EdgeOptions(
        name="process_subclass_of",
        annotations=(
            BiolinkPredicate("biolink:subclass_of"),
            EdgeLabel("PROCESS_SUBCLASS_OF"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the edge when the question is how a specific process relates "
                "to a broader one, so that an annotation at a leaf term can be read "
                "at the level a question asks.",
                limitations=(
                    Limitation(
                        "The edge is the ontology's is-a statement; the build does "
                        "not propagate annotations along it."
                    ),
                    Limitation(
                        "Only terms the kinase slice reaches are present."
                    ),
                ),
            ),
            claims=(
                Claim("The edge is one parent assertion in the Gene Ontology."),
                Claim("The build does not propagate annotations along it."),
            ),
        ),
    )
