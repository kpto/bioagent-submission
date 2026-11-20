"""Bind the go_terms relation to the biological-process record."""

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
from pharos_kg.graph.biological_process.node import BiologicalProcessNode
from pharos_kg.relation.derived.go_label.relation import GoLabel


process_binding = node_binding(
    target=BiologicalProcessNode,
    rows=GoLabel.row_source(),
    bind=lambda row: NodeValues(
        build_key=row.go_key,
        properties=BiologicalProcessNode(
            **unannotated(),
            go_key=row.go_key,
            label=row.label.default_to(row.go_key),
            aspect=row.aspect.default_to("unknown"),
        ),
    ),
    name="biological_process",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The go_label relation fulfils the BIOLOGICAL PROCESS use as one GO "
                "term record per term identity: each row supplies one node, keyed by "
                "the GO accession, covering every term the annotations name.",
                limitations=(
                    Limitation(
                        "The extract does not include the GO hierarchy or obsolete "
                        "terms."
                    ),
                ),
            ),
            claims=(
                Claim("One go_terms row produces one biological-process node."),
            ),
        ),
    ),
)
