"""Bind the genes relation to the gene record."""

from kg_build_system import (
    BindingOptions,
    Claim,
    Limitation,
    Meaning,
    NodeValues,
    Purpose,
    node_binding,
)

from pharos_kg.graph.annotated import unannotated
from pharos_kg.graph.gene.node import GeneNode
from pharos_kg.relation.derived.gene_label.relation import GeneLabel


gene_binding = node_binding(
    target=GeneNode,
    rows=GeneLabel.row_source(),
    bind=lambda row: NodeValues(
        build_key=row.gene_key,
        properties=GeneNode(
            **unannotated(),
            gene_key=row.gene_key,
            symbol=row.symbol.default_to("unknown"),
            hgnc_id=row.gene_key,
        ),
    ),
    name="gene",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The gene_label relation fulfils the GENE use as one gene record per "
                "HGNC accession: each row supplies one node, keyed by the gene key, "
                "covering every gene the extract names.",
                limitations=(
                    Limitation(
                        "A gene without an HGNC accession is absent from the graph."
                    ),
                ),
            ),
            claims=(
                Claim("One genes row produces one gene node."),
            ),
        ),
    ),
)
