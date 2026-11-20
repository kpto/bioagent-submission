"""Attach the kinase protein identity to one side of each interaction row."""

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

from pharos_kg.relation.derived.kinase_protein.relation import KinaseProtein
from pharos_kg.relation.source.protein_interaction import ProteinInteraction

rows = KinaseProtein.row_source().join(
    ProteinInteraction.row_source(),
    on=lambda kinase, row: (kinase.protein_id, row.protein_id),
)

shape = cast(Any, rows.shape)


class KinaseInteraction(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="kinase_interaction",
        contract=Contract(
            definition=Definition(
                grain="one row per interaction and kinase endpoint",
                identity=("protein_id", "row_id"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Name the kinase on one side of an interaction row, so that the "
                    "other side can be resolved and the pair summarised.",
                    limitations=(
                        Limitation(
                            "A row whose protein is not a kinase target is absent; this "
                            "relation does not carry interactions outside the slice."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one interaction row whose protein_id is a kinase."),
                ),
            ),
        ),
    )

    row_id = computed_field(
        shape.right.extract(lambda value: value.id), meaning=Omitted
    )
    protein_id = computed_field(
        shape.left.extract(lambda value: value.protein_id), meaning=Omitted
    )
    uniprot = computed_field(
        shape.left.extract(lambda value: value.uniprot), meaning=Omitted
    )
    other_id = computed_field(
        shape.right.extract(lambda value: value.other_id), meaning=Omitted
    )
    ppitypes = computed_field(
        shape.right.extract(lambda value: value.ppitypes), meaning=Omitted
    )
    score = computed_field(
        shape.right.extract(lambda value: value.score), meaning=Omitted
    )
    p_int = computed_field(
        shape.right.extract(lambda value: value.p_int), meaning=Omitted
    )
    p_ni = computed_field(
        shape.right.extract(lambda value: value.p_ni), meaning=Omitted
    )
