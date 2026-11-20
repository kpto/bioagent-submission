"""Bind the hpo_term_label relation to the HPO term record."""

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
from pharos_kg.graph.hpo_term.node import HpoTermNode
from pharos_kg.relation.derived.hpo_term_label.relation import HpoTermLabel


hpo_term_binding = node_binding(
    target=HpoTermNode,
    rows=HpoTermLabel.row_source(),
    bind=lambda row: NodeValues(
        build_key=row.hpo_id,
        properties=HpoTermNode(**unannotated(), hpo_id=row.hpo_id, name=row.name),
    ),
    name="hpo_term",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The hpo_term_label relation fulfils the HPO TERM use as one record "
                "per term a published disease edge reaches.",
                limitations=(
                    Limitation(
                        "A term no published disease uses is absent by design."
                    ),
                ),
            ),
            claims=(
                Claim("One hpo_term_label row produces one node."),
            ),
        ),
    ),
)
