"""Bind the disease_label relation to the disease record."""

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
from pharos_kg.graph.disease.node import DiseaseNode
from pharos_kg.relation.derived.disease_label.relation import DiseaseLabel


disease_binding = node_binding(
    target=DiseaseNode,
    rows=DiseaseLabel.row_source(),
    bind=lambda row: NodeValues(
        build_key=row.disease_key,
        properties=DiseaseNode(
            **unannotated(),
            disease_key=row.disease_key,
            name=row.name.default_to(row.ncats_name.default_to(row.disease_key)),
            mondo_id=row.mondo_id,
            doid=row.doid,
        ),
    ),
    name="disease",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The disease_label relation fulfils the DISEASE use as one disease "
                "record per disease identity: each row supplies one node, keyed by "
                "the disease key, covering every disease the kinase slice reaches.",
                limitations=(
                    Limitation(
                        "A name-derived key is a last resort and is less stable than "
                        "a CURIE."
                    ),
                    Limitation(
                        "The label is one of the names the sources wrote, not a "
                        "preferred name."
                    ),
                ),
            ),
            claims=(
                Claim("One disease_label row produces one disease node."),
            ),
        ),
    ),
)
