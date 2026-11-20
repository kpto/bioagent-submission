"""Attach the kinase protein to each expression observation."""

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
from pharos_kg.relation.source.expression_record import ExpressionRecord

rows = ExpressionRecord.row_source().join(
    KinaseProtein.row_source(),
    on=lambda observation, kinase: (observation.protein_id, kinase.protein_id),
)

shape = cast(Any, rows.shape)


class KinaseExpression(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="kinase_expression",
        contract=Contract(
            definition=Definition(
                grain="one row per expression observation of a kinase",
                identity=("row_id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State where the release detects a kinase, which resource observed "
                    "it and at which stated level.",
                    limitations=(
                        Limitation(
                            "An observation whose protein is outside the kinase slice "
                            "is absent."
                        ),
                        Limitation(
                            "Rows mix transcript and protein evidence and are not "
                            "comparable without the resource and level."
                        ),
                        Limitation(
                            "The rows state detection, not abundance."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one expression observation of a kinase."),
                    Claim("No row is filtered by detection flag or level here."),
                ),
            ),
        ),
    )

    row_id = computed_field(
        shape.left.extract(lambda value: value.id), meaning=Omitted
    )
    target_key = computed_field(
        shape.right.extract(lambda value: value.uniprot), meaning=Omitted
    )
    resource = computed_field(
        shape.left.extract(lambda value: value.etype), meaning=Omitted
    )
    anatomical_key = computed_field(
        shape.left.extract(lambda value: value.uberon_id), meaning=Omitted
    )
    label = computed_field(
        shape.left.extract(lambda value: value.tissue), meaning=Omitted
    )
    expressed = computed_field(
        shape.left.extract(lambda value: value.expressed), meaning=Omitted
    )
    level = computed_field(
        shape.left.extract(lambda value: value.qual_value), meaning=Omitted
    )
