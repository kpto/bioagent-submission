"""Bind the pathway_label relation to the pathway record."""

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
from pharos_kg.graph.pathway.node import PathwayNode
from pharos_kg.relation.derived.pathway_label.relation import PathwayLabel


pathway_binding = node_binding(
    target=PathwayNode,
    rows=PathwayLabel.row_source(),
    bind=lambda row: NodeValues(
        build_key=row.pathway_key,
        properties=PathwayNode(
            **unannotated(),
            pathway_key=row.pathway_key,
            label=row.label.default_to(row.pathway_key),
            source=row.source.default_to("unknown"),
            source_id=row.source_id.default_to(row.pathway_key),
            url=row.url,
        ),
    ),
    name="pathway",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The pathway_label relation fulfils the PATHWAY use as one curated "
                "pathway per identity: each row supplies one node, keyed by the "
                "database's CURIE, covering every pathway the slice's memberships "
                "name.",
                limitations=(
                    Limitation(
                        "A pathway record with no identifier or page cannot be keyed "
                        "and is absent."
                    ),
                ),
            ),
            claims=(
                Claim("One pathway_label row produces one pathway node."),
            ),
        ),
    ),
)
