"""Publish the link between a kinase target and the protein it names."""

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

from pharos_kg.relation.derived.kinase_target.relation import KinaseTarget
from pharos_kg.relation.source.target_protein import TargetProtein

rows = KinaseTarget.row_source().join(
    TargetProtein.row_source(),
    on=lambda target, link: (target.target_id, link.target_id),
)

shape = cast(Any, rows.shape)
left = shape.left
right = shape.right


class KinaseTargetProtein(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="kinase_target_protein",
        contract=Contract(
            definition=Definition(
                grain="one row per kinase target and linked protein",
                identity=("target_id", "protein_id"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Join the kinase slice to the release's own target-protein link, "
                    "so that a target-scoped fact reaches a protein identity without "
                    "the project assuming which protein a target names.",
                    limitations=(
                        Limitation(
                            "A target can name more than one protein; every reported "
                            "link is kept rather than one being preferred."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one target-protein link for a kinase target."),
                    Claim("No link is chosen or deduplicated."),
                ),
            ),
        ),
    )

    target_id = computed_field(
        left.extract(lambda value: value.target_id), meaning=Omitted
    )
    tdl = computed_field(left.extract(lambda value: value.tdl), meaning=Omitted)
    protein_id = computed_field(
        right.extract(lambda value: value.protein_id), meaning=Omitted
    )
