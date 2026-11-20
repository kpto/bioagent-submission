"""A kinase perturbation is associated with an observed phenotype."""

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
from pharos_kg.graph.phenotype.node import PhenotypeNode
from pharos_kg.graph.protein.node import ProteinNode


class HasPhenotypeEdge(AnnotatedEdge, Edge[ProteinNode, PhenotypeNode]):

    options = EdgeOptions(
        name="has_phenotype",
        annotations=(
            BiolinkPredicate("biolink:has_phenotype"),
            EdgeLabel("HAS_PHENOTYPE"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the phenotype association when the question is what a model with "
                "a perturbed kinase shows.",
                limitations=(
                    Limitation(
                        "The observation is in a model organism, so it is evidence "
                        "about the ortholog rather than about a human carrier."
                    ),
                    Limitation(
                        "A phenotype association is not a disease association and does "
                        "not establish a mechanism."
                    ),
                    Limitation(
                        "A missing phenotype is not evidence that the kinase is "
                        "phenotypically silent."
                    ),
                ),
            ),
            claims=(
                Claim(
                    "The edge is one kinase and one MP term, aggregated over the "
                    "release's phenotype rows."
                ),
                Claim("The p-value is the smallest the release reports for the pair."),
            ),
        ),
    )

    sources: PropertySlot[Array[str]] = property(
        meaning=Meaning(
            claims=(
                Claim(
                    "The contributing programs, such as IMPC, OMIM or a mouse "
                    "ortholog resource."
                ),
                Claim("Use to see whose observation the edge rests on."),
            ),
        ),
    )
    procedures: PropertySlot[Array[str]] = property(
        meaning=Meaning(
            claims=(
                Claim("The procedures the contributing rows name."),
                Claim("Use to judge how the phenotype was measured."),
            ),
        ),
    )
    min_p_value: PropertySlot[float | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The smallest p-value among the pair's rows."),
                Claim(
                    "The rows mix procedures, so the smallest value is a summary and "
                    "not a single test."
                ),
            ),
        ),
    )
    count: PropertySlot[int] = property(
        meaning=Meaning(
            claims=(
                Claim("The number of phenotype rows behind the pair."),
                Claim("Use to distinguish a single observation from a repeated one."),
            ),
        ),
    )
