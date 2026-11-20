"""One row per pathway membership, as the release stores it."""

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


class PathwayRecord(SourceRelation[PharosDump]):

    options = SourceRelationOptions(
        name="pathway_record",
        contract=Contract(
            definition=Definition(
                grain="one row per pathway membership",
                identity=("id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the release's pathway table as it stands: one row is one "
                    "pathway one target is a member of, as a database curates it.",
                    limitations=(
                        Limitation(
                            "A row is a database's membership statement, not an "
                            "observed interaction."
                        ),
                        Limitation(
                            "target_id and protein_id are source keys; the mapping to "
                            "a kinase and to a pathway CURIE is a declared step."
                        ),
                        Limitation(
                            "id_in_source is empty for some sources and the identifier "
                            "is then carried only in url."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one pathway row in Pharos 3.19."),
                    Claim("No row is filtered, joined or aggregated here."),
                ),
            ),
        ),
    )

    id: Field[int] = field(
        definition=FieldDefinition("The row's identifier in the release."),
        meaning=Omitted,
    )
    target_id: Field[int] = field(
        definition=FieldDefinition("The release's target key."),
        meaning=Omitted,
    )
    protein_id: Field[int] = field(
        definition=FieldDefinition(
            "The release's protein key the membership is stated for.",
            null_meaning="Absent when the row names no protein.",
        ),
        meaning=Omitted,
    )
    pwtype: Field[str] = field(
        definition=FieldDefinition(
            "The pathway database, such as Reactome, KEGG or WikiPathways.",
        ),
        meaning=Omitted,
    )
    id_in_source: Field[str] = field(
        definition=FieldDefinition(
            "The identifier the database uses.",
            null_meaning="Absent when the release carries the identifier only in url.",
        ),
        meaning=Omitted,
    )
    name: Field[str] = field(
        definition=FieldDefinition(
            "The pathway name the database states.",
            null_meaning="Absent when the row states no name.",
        ),
        meaning=Omitted,
    )
    url: Field[str] = field(
        definition=FieldDefinition(
            "The page the release links for the pathway.",
            null_meaning="Absent when the row links no page.",
        ),
        meaning=Omitted,
    )
