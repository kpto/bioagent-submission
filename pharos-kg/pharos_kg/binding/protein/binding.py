"""Bind the targets relation to the protein record."""

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
from pharos_kg.graph.protein.node import ProteinNode
from pharos_kg.relation.derived.protein_label.relation import ProteinLabel


protein_binding = node_binding(
    target=ProteinNode,
    rows=ProteinLabel.row_source(),
    bind=lambda row: NodeValues(
        build_key=row.uniprot.prepend("PHAROS:"),
        properties=ProteinNode(
            **unannotated(),
            target_key=row.uniprot.prepend("PHAROS:"),
            symbol=row.symbol.default_to("unknown"),
            uniprot=row.uniprot,
            name=row.name.default_to(row.symbol.default_to("unknown")),
            description=row.description,
            tdl=row.tdl.default_to("unknown"),
            family=row.family.default_to("Other"),
            novelty=row.novelty,
        ),
    ),
    name="protein",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The protein_label relation fulfils the PROTEIN use as one kinase record "
                "per UniProt accession: each row supplies one node, keyed by "
                "PHAROS:<UniProt>, covering every target in the kinase family "
                "extract.",
                limitations=(
                    Limitation(
                        "A target without a UniProt accession cannot be keyed and is "
                        "excluded upstream."
                    ),
                ),
            ),
            claims=(
                Claim("One targets row produces one protein node."),
            ),
        ),
    ),
)
