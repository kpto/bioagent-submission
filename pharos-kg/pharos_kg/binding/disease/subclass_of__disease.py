"""Bind the disease_hierarchy relation to the subclass_of edge."""

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
from pharos_kg.graph.disease.subclass_of__disease import DiseaseSubclassEdge
from pharos_kg.relation.derived.disease_hierarchy.relation import DiseaseHierarchy


disease_hierarchy_binding = edge_binding(
    target=DiseaseSubclassEdge,
    rows=DiseaseHierarchy.row_source(),
    bind=lambda row: EdgeValues(
        build_key=row.child_key.append("::SUBCLASS_OF::").append(row.parent_key),
        source_build_key=row.child_key,
        target_build_key=row.parent_key,
        properties=DiseaseSubclassEdge(**unannotated()),
    ),
    name="subclass_of",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The disease_hierarchy relation fulfils the SUBCLASS OF use between "
                "diseases: each row supplies one edge, keyed by the child and the "
                "parent, covering every assertion whose endpoints the graph "
                "publishes.",
                limitations=(
                    Limitation(
                        "An edge is an ontology assertion, not a clinical claim."
                    ),
                ),
            ),
            claims=(
                Claim("One disease_hierarchy row produces one edge."),
            ),
        ),
    ),
)
