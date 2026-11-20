"""A ligand has measured binding activity against a kinase."""

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
from pharos_kg.graph.ligand.node import LigandNode
from pharos_kg.graph.protein.node import ProteinNode


class BindsEdge(AnnotatedEdge, Edge[LigandNode, ProteinNode]):

    options = EdgeOptions(
        name="binds",
        annotations=(
            BiolinkPredicate("biolink:molecularly_interacts_with"),
            EdgeLabel("BINDS"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the measured binding activity when the question is whether a "
                "ligand was measured against a kinase.",
                limitations=(
                    Limitation(
                        "The release normalises assay types; the original assay "
                        "context is not preserved."
                    ),
                    Limitation(
                        "A missing measurement is not evidence of no binding."
                    ),
                    Limitation(
                        "Potency is not selectivity, efficacy or clinical benefit."
                    ),
                ),
            ),
            claims=(
                Claim(
                    "The edge is one ligand-target pair with its measured activities."
                ),
                Claim("The mean activity is in -log10 molar units."),
            ),
        ),
    )

    mean_p_activity: PropertySlot[float | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The mean activity in -log10 molar units."),
                Claim("A larger value means a lower active concentration."),
                Claim(
                    "The mean may hide a wide or multimodal measurement distribution."
                ),
            ),
        ),
    )
    std: PropertySlot[float | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The standard deviation of the measurements."),
                Claim("Use to judge measurement spread."),
            ),
        ),
    )
    count: PropertySlot[int] = property(
        meaning=Meaning(
            claims=(
                Claim("The number of measurements aggregated into the pair."),
                Claim("Use to distinguish one assay from repeated measurements."),
            ),
        ),
    )
    target_count: PropertySlot[int] = property(
        meaning=Meaning(
            claims=(
                Claim(
                    "The number of kinases the release measures this ligand "
                    "against, repeated on every edge it has."
                ),
                Claim(
                    "Use to see whether the pair sits inside a multi-target or a "
                    "single-target compound."
                ),
                Claim(
                    "A compound with one measured kinase may bind others outside "
                    "the extract."
                ),
            ),
        ),
    )
    pmids: PropertySlot[Array[str] | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The PubMed identifiers named by the activity records."),
                Claim("Use for literature traceability."),
            ),
        ),
    )
    references: PropertySlot[Array[str] | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The references named by the activity records."),
                Claim("Use for traceability."),
            ),
        ),
    )
    min_p_activity: PropertySlot[float | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The weakest measured activity in the pair."),
                Claim("Use to see the measurement range."),
            ),
        ),
    )
    max_p_activity: PropertySlot[float | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The strongest measured activity in the pair."),
                Claim("Use to see the measurement range."),
            ),
        ),
    )
