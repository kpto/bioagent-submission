"""One row per disease the platform names."""

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

from pharos_kg.asset.opentargets import OpenTargets


class OtDisease(SourceRelation[OpenTargets]):

    options = SourceRelationOptions(
        name="ot_disease",
        contract=Contract(
            definition=Definition(
                grain="one row per disease identity",
                identity=("disease_id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the platform's disease labels so that an evidence row's "
                    "disease identity can be shown with the name the platform uses.",
                    limitations=(
                        Limitation(
                            "The platform names diseases in several ontologies "
                            "(MONDO, EFO, HP, Orphanet); a label does not imply a "
                            "cross-ontology equivalence."
                        ),
                        Limitation(
                            "The label is the platform's name, not necessarily the "
                            "ontology's preferred label."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one disease identity in the release."),
                    Claim("No row is filtered, joined or renamed here."),
                ),
            ),
        ),
    )

    disease_id: Field[str] = field(
        definition=FieldDefinition("The disease identity as a CURIE."),
        meaning=Omitted,
    )
    name: Field[str] = field(
        definition=FieldDefinition(
            "The disease name the platform publishes.",
            null_meaning="Absent when the release names no label.",
        ),
        meaning=Omitted,
    )
