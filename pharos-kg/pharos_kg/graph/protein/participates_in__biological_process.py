"""A kinase is annotated to a GO term."""

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
from pharos_kg.graph.biological_process.node import BiologicalProcessNode
from pharos_kg.graph.protein.node import ProteinNode


class ParticipatesInEdge(AnnotatedEdge, Edge[ProteinNode, BiologicalProcessNode]):

    options = EdgeOptions(
        name="participates_in",
        annotations=(
            BiolinkPredicate("biolink:participates_in"),
            EdgeLabel("PARTICIPATES_IN"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the annotation assertion when the question is which GO term a "
                "kinase is annotated to and on what evidence.",
                limitations=(
                    Limitation(
                        "The annotation does not state a causal role or a direction."
                    ),
                    Limitation(
                        "The extract carries no GO hierarchy, so a parent term is not "
                        "implied."
                    ),
                ),
            ),
            claims=(
                Claim("The edge is one target-GO-evidence triple."),
                Claim(
                    "The evidence code is the GO evidence code reported by the "
                    "release."
                ),
            ),
        ),
    )

    evidence: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The GO evidence code, such as IDA or IEA."),
                Claim("Use to judge the annotation's basis."),
                Claim(
                    "The code describes the evidence method, not the strength of the "
                    "claim."
                ),
            ),
        ),
    )
