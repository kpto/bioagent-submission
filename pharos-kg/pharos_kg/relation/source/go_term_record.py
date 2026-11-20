"""One row per GO term, as the release stores it."""

from kg_build_system import (
    Claim, Contract, Definition, Field, FieldDefinition, Limitation, Meaning,
    Omitted, Purpose, SourceRelation, SourceRelationOptions, field,
)

from pharos_kg.asset.pharos_source import PharosDump


class GoTermRecord(SourceRelation[PharosDump]):

    options = SourceRelationOptions(
        name="go_term_record",
        contract=Contract(
            definition=Definition(
                grain="one row per GO term",
                identity=("go_id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the GO term table so that a process label and aspect are "
                    "the ontology's own rather than a name the project invented.",
                    limitations=(
                        Limitation(
                            "The term's parents are a separate table; this relation "
                            "states no hierarchy."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one go row in Pharos 3.19."),
                    Claim("The label is the release's term name, not a rephrasing."),
                ),
            ),
        ),
    )

    go_id: Field[str] = field(
        definition=FieldDefinition("The GO term identifier."),
        meaning=Omitted,
    )
    name: Field[str] = field(
        definition=FieldDefinition("The term's name."),
        meaning=Omitted,
    )
    namespace: Field[str] = field(
        definition=FieldDefinition(
            "The term's aspect.",
            null_meaning="Absent when the release records none.",
        ),
        meaning=Omitted,
    )
