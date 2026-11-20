"""Bind the process_hierarchy relation to the process subclass edge."""

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
from pharos_kg.graph.biological_process.subclass_of__biological_process import (
    ProcessSubclassEdge,
)
from pharos_kg.relation.derived.process_hierarchy.relation import ProcessHierarchy


process_hierarchy_binding = edge_binding(
    target=ProcessSubclassEdge,
    rows=ProcessHierarchy.row_source(),
    bind=lambda row: EdgeValues(
        build_key=row.child_key.append("::SUBCLASS_OF::").append(row.parent_key),
        source_build_key=row.child_key,
        target_build_key=row.parent_key,
        properties=ProcessSubclassEdge(**unannotated()),
    ),
    name="process_subclass_of",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The process_hierarchy relation fulfils the SUBCLASS OF use between "
                "processes: each row supplies one edge, keyed by the child and the "
                "parent, covering every assertion whose endpoints the graph "
                "publishes.",
                limitations=(
                    Limitation(
                        "An edge is an ontology assertion, and the build does not "
                        "propagate annotations along it."
                    ),
                ),
            ),
            claims=(
                Claim("One process_hierarchy row produces one edge."),
            ),
        ),
    ),
)
