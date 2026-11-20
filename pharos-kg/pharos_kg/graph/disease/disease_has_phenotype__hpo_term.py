"""A phenotype recorded for a disease."""

from kg_build_system import (
    Array,
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
from pharos_kg.graph.disease.node import DiseaseNode
from pharos_kg.graph.hpo_term.node import HpoTermNode


class DiseaseHasPhenotypeEdge(AnnotatedEdge, Edge[DiseaseNode, HpoTermNode]):

    options = EdgeOptions(
        name="disease_has_phenotype",
        annotations=(
            BiolinkPredicate("biolink:has_phenotype"),
            EdgeLabel("DISEASE_HAS_PHENOTYPE"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the edge when the question is what a disease looks like in a "
                "patient, including diseases no target in the graph reaches.",
                limitations=(
                    Limitation(
                        "The edge states that the phenotype was recorded for the "
                        "disease, not that every patient has it."
                    ),
                    Limitation(
                        "Annotation coverage is uneven: rare diseases are annotated "
                        "densely and common diseases barely."
                    ),
                ),
            ),
            claims=(
                Claim("The edge is one disease and one phenotype term, aggregated "
                      "from the release's annotation rows."),
                Claim("The frequency is the release's text, not a probability."),
            ),
        ),
    )

    frequencies: PropertySlot[Array[str] | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The distinct frequencies the release states for the pair."),
                Claim("Use to separate an occasional finding from a hallmark."),
                Claim("A frequency is a cohort observation, not a probability."),
            ),
        ),
    )
    annotation_count: PropertySlot[int] = property(
        meaning=Meaning(
            claims=(
                Claim("The number of annotation rows the pair aggregates."),
                Claim("Use to judge how well documented the statement is."),
            ),
        ),
    )
    evidence: PropertySlot[str | None] = property(
        meaning=Meaning(
            claims=(
                Claim("A reference or evidence code cited by the annotations."),
                Claim("Use to trace one statement back to a source."),
                Claim("Only one of the cited references is kept."),
            ),
        ),
    )
