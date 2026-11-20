"""One row per ligand the release records, with its identity and names."""

from kg_build_system import (
    Claim, Contract, Definition, Field, FieldDefinition, Limitation, Meaning,
    Omitted, Purpose, SourceRelation, SourceRelationOptions, field,
)

from pharos_kg.asset.pharos_source import PharosDump


class NcatsLigand(SourceRelation[PharosDump]):

    options = SourceRelationOptions(
        name="ncats_ligand",
        contract=Contract(
            definition=Definition(
                grain="one row per ligand",
                identity=("id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the release's ligand register, so that a compound's identity, "
                    "name and stated drug status are the release's own.",
                    limitations=(
                        Limitation(
                            "A ligand is a chemical record the release aggregates; it "
                            "does not state that the compound is approved anywhere."
                        ),
                        Limitation(
                            "The cross-reference columns are strings as the release "
                            "writes them."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one ncats_ligands row in Pharos 3.19."),
                    Claim("identifier is the ligand identity the release publishes."),
                ),
            ),
        ),
    )

    id: Field[int] = field(
        definition=FieldDefinition("The release's ligand key."),
        meaning=Omitted,
    )
    identifier: Field[str] = field(
        definition=FieldDefinition("The published ligand identity."),
        meaning=Omitted,
    )
    name: Field[str] = field(
        definition=FieldDefinition(
            "The ligand name.",
            null_meaning="Absent when the release states none.",
        ),
        meaning=Omitted,
    )
    isdrug: Field[int] = field(
        name="isDrug",
        definition=FieldDefinition(
            "The release's drug flag for the ligand.",
            null_meaning="Absent when the release states none.",
        ),
        meaning=Omitted,
    )
    smiles: Field[str] = field(
        definition=FieldDefinition(
            "The structure string the release records.",
            null_meaning="Absent when the release states none.",
        ),
        meaning=Omitted,
    )
    pubchem: Field[str] = field(
        name="PubChem",
        definition=FieldDefinition(
            "The PubChem identifier the release records.",
            null_meaning="Absent when the release states none.",
        ),
        meaning=Omitted,
    )
    chembl: Field[str] = field(
        name="ChEMBL",
        definition=FieldDefinition(
            "The ChEMBL identifier the release records.",
            null_meaning="Absent when the release states none.",
        ),
        meaning=Omitted,
    )
