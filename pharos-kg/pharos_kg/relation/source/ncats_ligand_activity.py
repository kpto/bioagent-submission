"""One row per ligand activity measurement, as the release records it."""

from kg_build_system import (
    Claim, Contract, Definition, Field, FieldDefinition, Limitation, Meaning,
    Omitted, Purpose, SourceRelation, SourceRelationOptions, field,
)

from pharos_kg.asset.pharos_source import PharosDump


class NcatsLigandActivity(SourceRelation[PharosDump]):

    options = SourceRelationOptions(
        name="ncats_ligand_activity",
        contract=Contract(
            definition=Definition(
                grain="one row per ligand activity measurement",
                identity=("id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the activity measurements the release records against a "
                    "target, so that a ligand-target edge states what was measured "
                    "rather than what a query returned.",
                    limitations=(
                        Limitation(
                            "A measurement is one report, not a statement of "
                            "selectivity, efficacy or safety."
                        ),
                        Limitation(
                            "Activity values are as the source stated them; assay "
                            "types differ and are not converted."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one ncats_ligand_activity row in Pharos 3.19."),
                    Claim("No measurement is filtered or averaged here."),
                ),
            ),
        ),
    )

    id: Field[int] = field(
        definition=FieldDefinition("The measurement's identifier."),
        meaning=Omitted,
    )
    ncats_ligand_id: Field[int] = field(
        definition=FieldDefinition("The release's ligand key."),
        meaning=Omitted,
    )
    target_id: Field[int] = field(
        definition=FieldDefinition(
            "The release's target key.",
            null_meaning="Absent when the measurement names no target.",
        ),
        meaning=Omitted,
    )
    act_value: Field[float] = field(
        definition=FieldDefinition(
            "The measured activity value.",
            null_meaning="Absent when the source reports no value.",
        ),
        meaning=Omitted,
    )
    act_type: Field[str] = field(
        definition=FieldDefinition(
            "The activity type, for example IC50 or Ki.",
            null_meaning="Absent when the source states no type.",
        ),
        meaning=Omitted,
    )
    reference: Field[str] = field(
        definition=FieldDefinition(
            "The source's citation for the measurement.",
            null_meaning="Absent when the source cites none.",
        ),
        meaning=Omitted,
    )
    pubmed_ids: Field[str] = field(
        definition=FieldDefinition(
            "The PubMed identifiers the source reports, as it writes them.",
            null_meaning="Absent when the source reports none.",
        ),
        meaning=Omitted,
    )
