"""Disease is-a assertions whose two endpoints the graph publishes."""

from typing import Any, cast

from kg_build_system import (
    Claim,
    Contract,
    Definition,
    DerivedRelation,
    DerivedRelationOptions,
    Limitation,
    Meaning,
    Omitted,
    Purpose,
    computed_field,
)

from pharos_kg.relation.derived.disease_label.relation import DiseaseLabel
from pharos_kg.relation.source.mondo_parent import MondoParent

first = MondoParent.row_source().join(
    DiseaseLabel.row_source(),
    on=lambda parent, disease: (parent.mondoid, disease.disease_key),
)
rows = first.join(
    DiseaseLabel.row_source(),
    on=lambda pair, disease: (
        pair.left.extract(lambda value: value.parentid), disease.disease_key,
    ),
)

shape = cast(Any, rows.shape)
pair = shape.left
right = shape.right


class DiseaseHierarchy(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="disease_hierarchy",
        contract=Contract(
            definition=Definition(
                grain="one row per published disease and one of its parents",
                identity=("child_key", "parent_key"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State that one disease is a kind of another, using only "
                    "assertions whose two endpoints the graph publishes, so that a "
                    "rare disease can be read through its class without a second "
                    "lookup.",
                    limitations=(
                        Limitation(
                            "The edge is the ontology's is-a statement, not a claim "
                            "about mechanism or co-occurrence."
                        ),
                        Limitation(
                            "A parent the release names but the kinase slice never "
                            "reaches is absent, so the published hierarchy is a "
                            "subgraph of the ontology."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one is-a assertion between two published "
                          "diseases."),
                    Claim("The assertion comes from the release, not the project."),
                ),
            ),
        ),
    )

    child_key = computed_field(
        pair.extract(lambda value: value.right).extract(
            lambda value: value.disease_key
        ),
        meaning=Omitted,
    )
    parent_key = computed_field(
        right.extract(lambda value: value.disease_key), meaning=Omitted
    )
