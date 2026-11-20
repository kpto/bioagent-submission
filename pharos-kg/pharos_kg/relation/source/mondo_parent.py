"""One row per MONDO parent assertion."""

from kg_build_system import (
    Field,
    FieldDefinition,
    Claim,
    Contract,
    Definition,
    Limitation,
    Meaning,
    Omitted,
    Purpose,
    SourceRelation,
    SourceRelationOptions,
    field,
)

from pharos_kg.asset.pharos_source import PharosDump


class MondoParent(SourceRelation[PharosDump]):

    options = SourceRelationOptions(
        name="mondo_parent",
        contract=Contract(
            definition=Definition(
                grain="one row per disease and one of its parents",
                identity=("mondoid", "parentid"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the disease ontology's parent assertions as the release "
                    "stores them, so that the graph can state that one disease is a "
                    "kind of another without the project asserting the relation.",
                    limitations=(
                        Limitation(
                            "A parent assertion is the ontology's is-a edge, not a "
                            "claim that one disease causes or contains another."
                        ),
                        Limitation(
                            "The table only covers identifiers the release carries; a "
                            "parent outside the release is absent."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one parent assertion in the release."),
                    Claim("No row is filtered, joined or renamed here."),
                ),
            ),
        ),
    )

    mondoid: Field[str] = field(
        definition=FieldDefinition("The child disease identifier."),
        meaning=Omitted,
    )
    parentid: Field[str] = field(
        definition=FieldDefinition("The parent disease identifier."),
        meaning=Omitted,
    )
