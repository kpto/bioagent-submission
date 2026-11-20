"""One row per target, as the release stores it."""

from kg_build_system import (
    Claim,
    Contract,
    Definition,
    Field,
    FieldDefinition,
    Limitation,
    Meaning,
    Omitted,
    Purpose,
    SourceRelation,
    SourceRelationOptions,
    field,
)

from pharos_kg.asset.pharos_source import PharosDump


class Target(SourceRelation[PharosDump]):

    options = SourceRelationOptions(
        name="target",
        contract=Contract(
            definition=Definition(
                grain="one row per target",
                identity=("id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the release's target table so that the family, development "
                    "level and identifier the release assigns are the ones the graph "
                    "selects on.",
                    limitations=(
                        Limitation(
                            "The release's target identity is not a protein identity; "
                            "the link between them is a declared join."
                        ),
                        Limitation(
                            "The development level is the release's curation status, "
                            "not a measure of biological importance."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one target row in Pharos 3.19."),
                    Claim("idg is the family facet the release publishes."),
                ),
            ),
        ),
    )

    id: Field[int] = field(
        definition=FieldDefinition("The release's target key."),
        meaning=Omitted,
    )
    name: Field[str] = field(
        definition=FieldDefinition("The target's name."),
        meaning=Omitted,
    )
    ttype: Field[str] = field(
        definition=FieldDefinition(
            "The target's type as the release states it.",
            null_meaning="Absent when the release records none.",
        ),
        meaning=Omitted,
    )
    description: Field[str] = field(
        definition=FieldDefinition(
            "The target's description.",
            null_meaning="Absent when the release records none.",
        ),
        meaning=Omitted,
    )
    tdl: Field[str] = field(
        definition=FieldDefinition(
            "The target development level.",
            null_meaning="Absent when the release records none.",
        ),
        meaning=Omitted,
    )
    idg: Field[str] = field(
        definition=FieldDefinition(
            "The IDG family facet.",
            null_meaning="Absent when the target has no IDG family.",
        ),
        meaning=Omitted,
    )
    fam: Field[str] = field(
        definition=FieldDefinition(
            "The family the release records.",
            null_meaning="Absent when the release records none.",
        ),
        meaning=Omitted,
    )
    famext: Field[str] = field(
        definition=FieldDefinition(
            "The extended family the release records.",
            null_meaning="Absent when the release records none.",
        ),
        meaning=Omitted,
    )
