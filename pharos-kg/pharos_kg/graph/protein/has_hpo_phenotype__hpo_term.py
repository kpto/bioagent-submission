"""A phenotype recorded for a kinase's variants."""

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
from pharos_kg.graph.hpo_term.node import HpoTermNode
from pharos_kg.graph.protein.node import ProteinNode


class HasHpoPhenotypeEdge(AnnotatedEdge, Edge[ProteinNode, HpoTermNode]):

    options = EdgeOptions(
        name="has_hpo_phenotype",
        annotations=(
            BiolinkPredicate("biolink:has_phenotype"),
            EdgeLabel("HAS_HPO_PHENOTYPE"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the edge when the question is what a kinase's variants produce "
                "in a patient, including kinases with no target-disease row.",
                limitations=(
                    Limitation(
                        "The edge states that the phenotype was recorded for the gene, "
                        "not that every variant produces it."
                    ),
                    Limitation(
                        "The annotation was recorded in a cohort with a disease; the "
                        "edge names that disease as context, not as a claim."
                    ),
                ),
            ),
            claims=(
                Claim("The edge is one kinase and one phenotype term, aggregated "
                      "from the release's gene annotation rows."),
                Claim("The recording diseases are kept as a property."),
            ),
        ),
    )

    recording_diseases: PropertySlot[Array[str]] = property(
        meaning=Meaning(
            claims=(
                Claim("The diseases the annotations were recorded in."),
                Claim("Use to judge whether a phenotype statement is disease-specific."),
                Claim("A recording disease is context, not a causal claim."),
            ),
        ),
    )
    annotation_count: PropertySlot[int] = property(
        meaning=Meaning(
            claims=(
                Claim("The number of annotation rows the edge aggregates."),
                Claim("Use to judge how well documented the statement is."),
            ),
        ),
    )
