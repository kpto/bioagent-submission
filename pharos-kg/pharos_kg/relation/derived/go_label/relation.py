"""Publish one label row per GO term the kinase slice uses."""

from kg_build_system import (
    Claim, Contract, Definition, DerivedRelation, DerivedRelationOptions,
    FieldDefinition, Limitation, Meaning, Omitted, Purpose, computed_field,
)

from pharos_kg.modules.row_operations import go_labels
from pharos_kg.relation.derived.kinase_go_term.relation import KinaseGoTerm

rows = KinaseGoTerm.row_source().custom_op(go_labels)


class GoLabel(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="go_label",
        contract=Contract(
            definition=Definition(
                grain="one row per go_key",
                identity=("go_key",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Name each process, function or component the release annotates "
                    "a kinase with, as the ontology names it.",
                    limitations=(
                        Limitation(
                            "A term no kinase in the slice is annotated with is "
                            "absent; the graph does not carry the whole ontology."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one GO term used by the kinase slice."),
                    Claim("label and aspect are the ontology's values."),
                ),
            ),
        ),
    )

    go_key = computed_field(
        rows.shape.go_key,
        definition=FieldDefinition("The GO term identifier."),
        meaning=Omitted,
    )
    label = computed_field(
        rows.shape.label,
        definition=FieldDefinition(
            "The term name the release records.",
            null_meaning="Absent when the release states no name.",
        ),
        meaning=Omitted,
    )
    aspect = computed_field(
        rows.shape.aspect,
        definition=FieldDefinition(
            "The term's aspect.",
            null_meaning="Absent when the release states none.",
        ),
        meaning=Omitted,
    )
