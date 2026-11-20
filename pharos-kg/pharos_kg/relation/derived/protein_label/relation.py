"""Publish one label row per kinase protein."""

from kg_build_system import (
    Claim, Contract, Definition, DerivedRelation, DerivedRelationOptions,
    FieldDefinition, Limitation, Meaning, Omitted, Purpose, computed_field,
)

from pharos_kg.modules.row_operations import protein_labels
from pharos_kg.relation.derived.kinase_protein.relation import KinaseProtein

rows = KinaseProtein.row_source().custom_op(protein_labels)


class ProteinLabel(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="protein_label",
        contract=Contract(
            definition=Definition(
                grain="one row per UniProt accession",
                identity=("uniprot",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Name each kinase protein the slice holds, with the symbol, "
                    "development level and family the release records for it.",
                    limitations=(
                        Limitation(
                            "Novelty is not carried by this source, so the field is "
                            "absent rather than guessed."
                        ),
                        Limitation(
                            "The family is the release's family string, not a "
                            "re-derived classification."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one UniProt accession in the kinase slice."),
                    Claim("symbol, name, tdl and family are source values."),
                ),
            ),
        ),
    )

    uniprot = computed_field(
        rows.shape.uniprot,
        definition=FieldDefinition("The UniProt accession."),
        meaning=Omitted,
    )
    symbol = computed_field(
        rows.shape.symbol,
        definition=FieldDefinition(
            "The gene symbol the release records.",
            null_meaning="Absent when the release states none.",
        ),
        meaning=Omitted,
    )
    name = computed_field(
        rows.shape.name,
        definition=FieldDefinition(
            "The protein name the release records.",
            null_meaning="Absent when the release states none.",
        ),
        meaning=Omitted,
    )
    description = computed_field(
        rows.shape.description,
        definition=FieldDefinition(
            "The protein description the release records.",
            null_meaning="Absent when the release states none.",
        ),
        meaning=Omitted,
    )
    tdl = computed_field(
        rows.shape.tdl,
        definition=FieldDefinition(
            "The target development level.",
            null_meaning="Absent when the release states none.",
        ),
        meaning=Omitted,
    )
    family = computed_field(
        rows.shape.family,
        definition=FieldDefinition(
            "The family the release records.",
            null_meaning="Absent when the release states none.",
        ),
        meaning=Omitted,
    )
    novelty = computed_field(
        rows.shape.novelty,
        definition=FieldDefinition(
            "The novelty score, which this source does not carry.",
            null_meaning="Always absent on this source.",
        ),
        meaning=Omitted,
    )
