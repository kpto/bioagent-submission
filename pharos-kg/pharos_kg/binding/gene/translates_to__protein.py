"""Bind the translations relation to the translates_to edge."""

from kg_build_system import (
    BindingOptions,
    Claim,
    EdgeValues,
    Limitation,
    Meaning,
    Purpose,
    edge_binding,
)

from pharos_kg.graph.annotated import unannotated
from pharos_kg.graph.gene.translates_to__protein import TranslatesToEdge
from pharos_kg.relation.derived.gene_keyed.relation import GeneKeyed


translates_binding = edge_binding(
    target=TranslatesToEdge,
    rows=GeneKeyed.row_source(),
    bind=lambda row: EdgeValues(
        build_key=row.gene_key
        .append("::TRANSLATES_TO::")
        .append(row.target_key.prepend("PHAROS:")),
        source_build_key=row.gene_key,
        target_build_key=row.target_key.prepend("PHAROS:"),
        properties=TranslatesToEdge(**unannotated()),
    ),
    name="translates_to",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The gene_keyed relation fulfils the TRANSLATES TO use as the link "
                "from a gene to its protein: each row supplies one edge, keyed by "
                "the gene and target ids, covering every declared product.",
                limitations=(
                    Limitation(
                        "Alternative transcripts and isoforms are not modelled."
                    ),
                ),
            ),
            claims=(
                Claim("One translations row produces one translates_to edge."),
            ),
        ),
    ),
)
