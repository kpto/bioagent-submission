"""Bind the anatomical_label relation to the anatomical-entity record."""

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
from pharos_kg.graph.anatomical_entity.node import AnatomicalEntityNode
from pharos_kg.relation.derived.anatomical_label.relation import AnatomicalLabel


anatomical_binding = node_binding(
    target=AnatomicalEntityNode,
    rows=AnatomicalLabel.row_source(),
    bind=lambda row: NodeValues(
        build_key=row.anatomical_key,
        properties=AnatomicalEntityNode(
            **unannotated(),
            anatomical_key=row.anatomical_key,
            label=row.label.default_to(row.anatomical_key),
        ),
    ),
    name="anatomical_entity",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The anatomical_label relation fulfils the ANATOMICAL ENTITY use as "
                "one UBERON term per identity: each row supplies one node, keyed by "
                "the UBERON accession, covering every structure the slice's "
                "expression rows name.",
                limitations=(
                    Limitation(
                        "The release's label may name a cell type within the "
                        "structure, so the label is coarser or finer than the term."
                    ),
                ),
            ),
            claims=(
                Claim("One anatomical_label row produces one anatomical-entity node."),
            ),
        ),
    ),
)
