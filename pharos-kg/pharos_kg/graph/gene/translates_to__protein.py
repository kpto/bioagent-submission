"""The HGNC gene encodes the UniProt protein."""

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
from pharos_kg.graph.gene.node import GeneNode
from pharos_kg.graph.protein.node import ProteinNode


class TranslatesToEdge(AnnotatedEdge, Edge[GeneNode, ProteinNode]):

    options = EdgeOptions(
        name="translates_to",
        annotations=(
            BiolinkPredicate("biolink:translates_to"),
            EdgeLabel("TRANSLATES_TO"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the genomic-to-protein bridge: the HGNC gene encodes the "
                "UniProt protein.",
                limitations=(
                    Limitation(
                        "Alternative transcripts and isoforms are not modelled."
                    ),
                    Limitation(
                        "The edge is one-to-one in this slice; biology can be "
                        "many-to-many."
                    ),
                ),
            ),
            claims=(
                Claim(
                    "The edge asserts the canonical gene-product relation in this "
                    "release."
                ),
            ),
        ),
    )
