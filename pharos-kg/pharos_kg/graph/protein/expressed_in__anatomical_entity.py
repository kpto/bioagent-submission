"""A kinase is expressed in an anatomical structure."""

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

from pharos_kg.graph.anatomical_entity.node import AnatomicalEntityNode
from pharos_kg.graph.annotated import AnnotatedEdge
from pharos_kg.graph.annotations import BiolinkPredicate
from pharos_kg.graph.protein.node import ProteinNode


class ExpressedInEdge(AnnotatedEdge, Edge[ProteinNode, AnatomicalEntityNode]):

    options = EdgeOptions(
        name="expressed_in",
        annotations=(
            BiolinkPredicate("biolink:expressed_in"),
            EdgeLabel("EXPRESSED_IN"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the expression location when the question is where a kinase is "
                "detected.",
                limitations=(
                    Limitation(
                        "Expression is evidence of detection, not of function at that "
                        "site."
                    ),
                    Limitation(
                        "Only structures with strong or medium protein-level evidence "
                        "are edges; transcriptional evidence and weak detections are "
                        "not."
                    ),
                    Limitation(
                        "The observation is not stratified by developmental stage, "
                        "disease state or cell type beyond the release's label."
                    ),
                ),
            ),
            claims=(
                Claim(
                    "The edge is one kinase and one UBERON structure with strong or "
                    "medium protein-level detection."
                ),
                Claim("The level is the strongest the release reports for the pair."),
            ),
        ),
    )

    sources: PropertySlot[Array[str]] = property(
        meaning=Meaning(
            claims=(
                Claim(
                    "The expression resources that support the pair, such as HPA "
                    "Protein or HPM Protein."
                ),
                Claim("Use to see which resource observed the protein."),
            ),
        ),
    )
    level: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The strongest detection level, High or Medium."),
                Claim("Use to rank locations within a kinase."),
            ),
        ),
    )
    count: PropertySlot[int] = property(
        meaning=Meaning(
            claims=(
                Claim("The number of supporting expression rows."),
                Claim("Use to distinguish one observation from several."),
            ),
        ),
    )
