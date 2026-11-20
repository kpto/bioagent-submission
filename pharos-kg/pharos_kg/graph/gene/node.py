"""A protein-coding gene named by HGNC."""

from kg_build_system import (
    Claim,
    Limitation,
    Meaning,
    Node,
    NodeLabel,
    NodeOptions,
    PropertySlot,
    Purpose,
    property,
)

from pharos_kg.graph.annotated import AnnotatedNode
from pharos_kg.graph.annotations import BiolinkClass, KeyPrefix, OntologyTerm


class GeneNode(AnnotatedNode, Node):

    options = NodeOptions(
        name="gene",
        annotations=(
            BiolinkClass("biolink:Gene"),
            OntologyTerm("SO:0001217"),
            KeyPrefix(('HGNC:',)),
            NodeLabel("Gene"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the genomic locus when the question is about the gene or the "
                "gene-disease literature.",
                limitations=(
                    Limitation(
                        "The extract does not carry transcripts, alleles or genomic "
                        "coordinates."
                    ),
                    Limitation(
                        "Only kinases with an HGNC cross-reference are present."
                    ),
                ),
            ),
            claims=(
                Claim(
                    "A gene is identified by its HGNC accession, not by its symbol."
                ),
                Claim(
                    "The gene is the genomic entity; its protein product is a "
                    "separate node."
                ),
                Claim("A symbol is a label and may change between releases."),
            ),
        ),
    )

    gene_key: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The HGNC accession that identifies the gene."),
                Claim("Use for graph identity."),
            ),
        ),
    )
    symbol: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The HGNC gene symbol."),
                Claim("Use for display and search; a symbol is not an identity."),
            ),
        ),
    )
    hgnc_id: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The HGNC accession repeated as a property."),
                Claim("Use for cross-reference."),
            ),
        ),
    )
