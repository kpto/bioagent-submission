"""Resolve both endpoints of each kinase interaction row."""

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

from pharos_kg.relation.derived.kinase_interaction.relation import KinaseInteraction
from pharos_kg.relation.derived.kinase_protein.relation import KinaseProtein

rows = KinaseInteraction.row_source().join(
    KinaseProtein.row_source(),
    on=lambda one, other: (one.other_id, other.protein_id),
)

shape = cast(Any, rows.shape)


class KinaseInteractionPair(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="kinase_interaction_pair",
        contract=Contract(
            definition=Definition(
                grain="one row per interaction report between two kinases",
                identity=("row_id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Resolve the other side of an interaction row only when it is also "
                    "a kinase target, so that the graph never carries an interaction "
                    "whose far endpoint it does not hold.",
                    limitations=(
                        Limitation(
                            "An interaction between a kinase and a non-kinase target is "
                            "absent from the slice; absence is not evidence of no "
                            "interaction."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one interaction row with both endpoints kinases."),
                ),
            ),
        ),
    )

    row_id = computed_field(
        shape.left.extract(lambda value: value.row_id), meaning=Omitted
    )
    source_uniprot = computed_field(
        shape.left.extract(lambda value: value.uniprot), meaning=Omitted
    )
    target_uniprot = computed_field(
        shape.right.extract(lambda value: value.uniprot), meaning=Omitted
    )
    ppitypes = computed_field(
        shape.left.extract(lambda value: value.ppitypes), meaning=Omitted
    )
    score = computed_field(
        shape.left.extract(lambda value: value.score), meaning=Omitted
    )
    p_int = computed_field(
        shape.left.extract(lambda value: value.p_int), meaning=Omitted
    )
    p_ni = computed_field(
        shape.left.extract(lambda value: value.p_ni), meaning=Omitted
    )
