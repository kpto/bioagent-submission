"""One row per reported protein interaction, as the release stores it."""

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


class ProteinInteraction(SourceRelation[PharosDump]):

    options = SourceRelationOptions(
        name="protein_interaction",
        contract=Contract(
            definition=Definition(
                grain="one row per reported protein interaction",
                identity=("id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read every protein-protein interaction row the release holds, with "
                    "the source mix, probabilities and evidence it reports, so that a "
                    "graph edge is a declared summary rather than a value chosen while "
                    "fetching.",
                    limitations=(
                        Limitation(
                            "The row is a reported interaction, not a functional effect; "
                            "direction and consequence are not part of it."
                        ),
                        Limitation(
                            "The same unordered pair can appear once per reporting "
                            "source, and most rows carry no p_int."
                        ),
                        Limitation(
                            "p_int, p_ni and p_wrong are the release's own probabilities "
                            "and are not calibrated by this project."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one ncats_ppi row in Pharos 3.19."),
                    Claim("No interaction is filtered or summed here."),
                ),
            ),
        ),
    )

    id: Field[int] = field(
        definition=FieldDefinition("The interaction row's identifier."),
        meaning=Omitted,
    )
    ppitypes: Field[str] = field(
        definition=FieldDefinition(
            "The reporting sources and interaction types, as the release writes them.",
            null_meaning="Absent when the row reports no type.",
        ),
        meaning=Omitted,
    )
    protein_id: Field[int] = field(
        definition=FieldDefinition("The release's protein key for one side."),
        meaning=Omitted,
    )
    other_id: Field[int] = field(
        definition=FieldDefinition("The release's protein key for the other side."),
        meaning=Omitted,
    )
    p_int: Field[float] = field(
        definition=FieldDefinition(
            "The release's probability that the pair interacts.",
            null_meaning="Absent when the release reports none.",
        ),
        meaning=Omitted,
    )
    p_ni: Field[float] = field(
        definition=FieldDefinition(
            "The release's probability that the pair does not interact.",
            null_meaning="Absent when the release reports none.",
        ),
        meaning=Omitted,
    )
    p_wrong: Field[float] = field(
        definition=FieldDefinition(
            "The release's probability that the report is wrong.",
            null_meaning="Absent when the release reports none.",
        ),
        meaning=Omitted,
    )
    evidence: Field[str] = field(
        definition=FieldDefinition(
            "The evidence text the reporting source gave.",
            null_meaning="Absent when the source states none.",
        ),
        meaning=Omitted,
    )
    interaction_type: Field[str] = field(
        definition=FieldDefinition(
            "The interaction type the row records.",
            null_meaning="Absent when the row records none.",
        ),
        meaning=Omitted,
    )
    score: Field[float] = field(
        definition=FieldDefinition(
            "The reporting source's score.",
            null_meaning="Absent when the source reports none.",
        ),
        meaning=Omitted,
    )
