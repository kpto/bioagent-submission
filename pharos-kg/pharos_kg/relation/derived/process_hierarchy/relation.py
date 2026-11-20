"""Gene Ontology is-a assertions between published processes."""

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

from pharos_kg.relation.derived.go_label.relation import GoLabel
from pharos_kg.relation.source.go_parent import GoParent

first = GoParent.row_source().join(
    GoLabel.row_source(),
    on=lambda parent, term: (parent.go_id, term.go_key),
)
rows = first.join(
    GoLabel.row_source(),
    on=lambda pair, term: (
        pair.left.extract(lambda value: value.parent_id), term.go_key,
    ),
)

shape = cast(Any, rows.shape)
pair = shape.left
right = shape.right


class ProcessHierarchy(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="process_hierarchy",
        contract=Contract(
            definition=Definition(
                grain="one row per published process and one of its parents",
                identity=("child_key", "parent_key"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State that one biological process is a kind of another, using "
                    "only assertions whose two endpoints the graph publishes, so that "
                    "an annotation at a specific term can be read at the level a "
                    "question asks.",
                    limitations=(
                        Limitation(
                            "The graph states the assertion and does not propagate "
                            "annotations along it; a reader or a model may."
                        ),
                        Limitation(
                            "A parent term the kinase slice never reaches is absent."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one is-a assertion between two published "
                          "processes."),
                    Claim("The assertion comes from the release, not the project."),
                ),
            ),
        ),
    )

    child_key = computed_field(
        pair.extract(lambda value: value.right).extract(lambda value: value.go_key),
        meaning=Omitted,
    )
    parent_key = computed_field(
        right.extract(lambda value: value.go_key), meaning=Omitted
    )
