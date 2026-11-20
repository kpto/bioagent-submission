"""Bind the phenotype_label relation to the phenotype record."""

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
from pharos_kg.graph.phenotype.node import PhenotypeNode
from pharos_kg.relation.derived.phenotype_label.relation import PhenotypeLabel


phenotype_binding = node_binding(
    target=PhenotypeNode,
    rows=PhenotypeLabel.row_source(),
    bind=lambda row: NodeValues(
        build_key=row.phenotype_key,
        properties=PhenotypeNode(
            **unannotated(),
            phenotype_key=row.phenotype_key,
            label=row.label.default_to(row.phenotype_key),
            top_level_key=row.top_level_key,
            top_level_label=row.top_level_label,
        ),
    ),
    name="phenotype",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The phenotype_label relation fulfils the PHENOTYPE use as one "
                "Mammalian Phenotype term per identity: each row supplies one node, "
                "keyed by the MP accession, covering every term the slice's "
                "observations name.",
                limitations=(
                    Limitation(
                        "The release carries no MP hierarchy, so only the release's "
                        "own top-level grouping is attached."
                    ),
                ),
            ),
            claims=(
                Claim("One phenotype_label row produces one phenotype node."),
            ),
        ),
    ),
)
