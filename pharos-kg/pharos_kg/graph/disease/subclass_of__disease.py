"""One disease is a kind of another."""

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
from pharos_kg.graph.disease.node import DiseaseNode


class DiseaseSubclassEdge(AnnotatedEdge, Edge[DiseaseNode, DiseaseNode]):

    options = EdgeOptions(
        name="subclass_of",
        annotations=(
            BiolinkPredicate("biolink:subclass_of"),
            EdgeLabel("SUBCLASS_OF"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the edge when the question is what a disease belongs to, so "
                "that a rare disease can be understood through its class without a "
                "second lookup.",
                limitations=(
                    Limitation(
                        "The edge is the ontology's is-a statement; it does not imply "
                        "a shared mechanism or treatment."
                    ),
                    Limitation(
                        "Only classes the kinase slice reaches are present."
                    ),
                ),
            ),
            claims=(
                Claim("The edge is one parent assertion in the disease ontology."),
                Claim("The build does not propagate annotations along it."),
            ),
        ),
    )
