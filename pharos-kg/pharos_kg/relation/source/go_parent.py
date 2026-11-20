"""One row per Gene Ontology parent assertion."""

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


class GoParent(SourceRelation[PharosDump]):

    options = SourceRelationOptions(
        name="go_parent",
        contract=Contract(
            definition=Definition(
                grain="one row per term and one of its parents",
                identity=("go_id", "parent_id"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the Gene Ontology's parent assertions as the release stores "
                    "them, so that the graph can state that one process is a kind of "
                    "another without the project asserting the relation.",
                    limitations=(
                        Limitation(
                            "A parent assertion is the ontology's is-a edge, not a "
                            "subsumption the project verified."
                        ),
                        Limitation(
                            "Only terms and parents the release carries appear."
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

    go_id: Field[str] = field(
        definition=FieldDefinition("The child term identifier."),
        meaning=Omitted,
    )
    parent_id: Field[str] = field(
        definition=FieldDefinition("The parent term identifier."),
        meaning=Omitted,
    )
