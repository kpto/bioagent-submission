"""Publish one label row per anatomical structure the kinase slice reaches."""

from kg_build_system import (
    Claim,
    Contract,
    Definition,
    DerivedRelation,
    DerivedRelationOptions,
    FieldDefinition,
    Limitation,
    Meaning,
    Omitted,
    Purpose,
    computed_field,
)

from pharos_kg.modules.row_operations import anatomy_labels
from pharos_kg.relation.derived.kinase_expression.relation import KinaseExpression

rows = KinaseExpression.row_source().custom_op(anatomy_labels)


class AnatomicalLabel(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="anatomical_label",
        contract=Contract(
            definition=Definition(
                grain="one row per anatomical_key",
                identity=("anatomical_key",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Name each anatomical structure in which the release detects a "
                    "kinase.",
                    limitations=(
                        Limitation(
                            "The release's label mixes organ, tissue and cell-type "
                            "granularity under one UBERON term; the label is one of "
                            "those strings."
                        ),
                        Limitation(
                            "A structure no kinase in the slice is detected in is "
                            "absent."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one UBERON term used by the kinase slice."),
                    Claim("label is a tissue string the release states."),
                ),
            ),
        ),
    )

    anatomical_key = computed_field(
        rows.shape.anatomical_key,
        definition=FieldDefinition("The UBERON term identity."),
        meaning=Omitted,
    )
    label = computed_field(
        rows.shape.label,
        definition=FieldDefinition(
            "The tissue label the release states for the structure.",
            null_meaning="Absent when the release states no label.",
        ),
        meaning=Omitted,
    )
