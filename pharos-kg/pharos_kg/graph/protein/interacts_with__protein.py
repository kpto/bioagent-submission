"""One reported interaction between two kinases."""

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
from pharos_kg.graph.protein.node import ProteinNode


class InteractsWithEdge(AnnotatedEdge, Edge[ProteinNode, ProteinNode]):

    options = EdgeOptions(
        name="interacts_with",
        annotations=(
            BiolinkPredicate("biolink:interacts_with"),
            EdgeLabel("INTERACTS_WITH"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the edge when the question is which kinases act together, at "
                "the confidence the project's threshold admits.",
                limitations=(
                    Limitation(
                        "An interaction is a reported physical or functional "
                        "association, not a mechanism and not a direction."
                    ),
                    Limitation(
                        "STRING below the project threshold is absent; absence is not "
                        "evidence of no interaction."
                    ),
                ),
            ),
            claims=(
                Claim("The edge is one unordered pair of kinases."),
                Claim("Every experimental source is kept and STRING only at or above "
                      "700."),
            ),
        ),
    )

    score: PropertySlot[float | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The largest score among the kept sources."),
                Claim("Scores come from different scales and are not comparable."),
            ),
        ),
    )
    sources: PropertySlot[Array[str] | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The sources that report the pair."),
                Claim("Use to judge independence."),
                Claim("A shared source does not make two pairs independent."),
            ),
        ),
    )
    p_int: PropertySlot[float | None] = property(
        meaning=Meaning(
            claims=(
                Claim("A source's probability that the pair interacts."),
                Claim("Use as a confidence weight."),
            ),
        ),
    )
    p_ni: PropertySlot[float | None] = property(
        meaning=Meaning(
            claims=(
                Claim("A source's probability that the pair does not interact."),
                Claim("Use as a confidence weight."),
            ),
        ),
    )
    evidence_class: PropertySlot[str | None] = property(
        meaning=Meaning(
            claims=(
                Claim("Whether any kept source is experimental rather than predicted."),
                Claim("Use to separate measured interactions from inferred ones."),
                Claim("The split is a property here, not a relation type."),
            ),
        ),
    )
