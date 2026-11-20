"""A target-disease association reported by Pharos."""

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
from pharos_kg.graph.protein.node import ProteinNode


class AssociatedWithEdge(AnnotatedEdge, Edge[ProteinNode, DiseaseNode]):

    options = EdgeOptions(
        name="associated_with",
        annotations=(
            BiolinkPredicate("biolink:associated_with"),
            EdgeLabel("ASSOCIATED_WITH"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the edge with its evidence types and sources when the question "
                "is whether the release associates a kinase with a disease.",
                limitations=(
                    Limitation(
                        "An association is not a treatment, a mechanism or a clinical "
                        "claim."
                    ),
                    Limitation(
                        "The extract keeps at most five association details per pair."
                    ),
                    Limitation(
                        "A missing pair is not evidence of no association."
                    ),
                ),
            ),
            claims=(
                Claim(
                    "The edge is one target-disease pair aggregated from the release's "
                    "association records."
                ),
                Claim(
                    "The score and confidence are evidence weights, not probabilities "
                    "of causation."
                ),
            ),
        ),
    )

    evidence_types: PropertySlot[Array[str] | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The association types returned for the pair."),
                Claim("Use to see what kind of evidence supports the edge."),
            ),
        ),
    )
    sources: PropertySlot[Array[str] | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The data sources named by the association records."),
                Claim("Use to judge independence and coverage."),
                Claim(
                    "Source names are release labels, not a guarantee of "
                    "independence."
                ),
            ),
        ),
    )
    max_conf: PropertySlot[float | None] = property(
        meaning=Meaning(
            claims=(
                Claim(
                    "The largest confidence value among the pair's association "
                    "records."
                ),
                Claim("Use as a release-specific weight."),
                Claim("The scale is source-specific and not a probability."),
            ),
        ),
    )
    max_score: PropertySlot[float | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The largest score among the pair's association records."),
                Claim("Use as a release-specific weight."),
                Claim(
                    "The score is not comparable across sources or releases."
                ),
            ),
        ),
    )
    evidence_class: PropertySlot[str] = property(
        meaning=Meaning(
            purpose=Purpose(
                "Say what kind of independent evidence stands behind the edge, so "
                "that a genetic association and a literature co-mention are not read "
                "as the same claim.",
                limitations=(
                    Limitation(
                        "The class is the strongest class the platform reports, not a "
                        "score and not a count of papers."
                    ),
                    Limitation(
                        "none means the platform lists no row for the pair, which is "
                        "not evidence of no association."
                    ),
                ),
            ),
            claims=(
                Claim("high means a genetic, somatic-mutation or known-drug row."),
                Claim("literature_only means any other platform data type."),
                Claim("The class is a second source's statement, not the release's."),
            ),
        ),
    )
    evidence_count: PropertySlot[int] = property(
        meaning=Meaning(
            claims=(
                Claim(
                    "The number of association records aggregated into the edge."
                ),
                Claim("Use to distinguish a single report from repeated evidence."),
                Claim(
                    "The extract caps the detail list, so the count may exceed the "
                    "visible evidence rows."
                ),
            ),
        ),
    )
