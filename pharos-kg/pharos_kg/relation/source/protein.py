"""One row per protein, as the release stores it."""

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


class Protein(SourceRelation[PharosDump]):

    options = SourceRelationOptions(
        name="protein",
        contract=Contract(
            definition=Definition(
                grain="one row per protein",
                identity=("id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the release's protein table so that the graph's protein "
                    "identity is the accession the release itself records.",
                    limitations=(
                        Limitation(
                            "The amino-acid sequence and several cross-reference "
                            "columns are not read; this relation exposes the columns "
                            "the graph uses."
                        ),
                        Limitation(
                            "A protein row is not a claim that the protein is "
                            "druggable or studied."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one protein row in Pharos 3.19."),
                    Claim("uniprot is the accession the release records, not a "
                          "re-derived identity."),
                ),
            ),
        ),
    )

    id: Field[int] = field(
        definition=FieldDefinition("The release's protein key."),
        meaning=Omitted,
    )
    name: Field[str] = field(
        definition=FieldDefinition("The protein's name."),
        meaning=Omitted,
    )
    description: Field[str] = field(
        definition=FieldDefinition(
            "The protein's description.",
            null_meaning="Absent when the release records none.",
        ),
        meaning=Omitted,
    )
    uniprot: Field[str] = field(
        definition=FieldDefinition("The UniProt accession."),
        meaning=Omitted,
    )
    up_version: Field[str] = field(
        definition=FieldDefinition(
            "The UniProt release the accession was read from.",
            null_meaning="Absent when the release records none.",
        ),
        meaning=Omitted,
    )
    geneid: Field[int] = field(
        definition=FieldDefinition(
            "The NCBI gene identifier.",
            null_meaning="Absent when the release records none.",
        ),
        meaning=Omitted,
    )
    sym: Field[str] = field(
        definition=FieldDefinition("The gene symbol."),
        meaning=Omitted,
    )
    family: Field[str] = field(
        definition=FieldDefinition(
            "The protein family the release records.",
            null_meaning="Absent when the release records none.",
        ),
        meaning=Omitted,
    )
    preferred_symbol: Field[str] = field(
        definition=FieldDefinition(
            "The preferred symbol the release records.",
            null_meaning="Absent when the release records none.",
        ),
        meaning=Omitted,
    )
