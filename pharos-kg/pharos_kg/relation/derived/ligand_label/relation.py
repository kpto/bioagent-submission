"""Publish one label row per ligand the kinase slice reaches."""

from kg_build_system import (
    Claim,
    Contract,
    Definition,
    DerivedRelation,
    DerivedRelationOptions,
    FieldDefinition,
    Limitation,
    Meaning,
    Omitted,
    Purpose,
    computed_field,
)

from pharos_kg.modules.row_operations import ligand_labels
from pharos_kg.relation.derived.kinase_activity.relation import KinaseActivity

rows = KinaseActivity.row_source().custom_op(ligand_labels)


class LigandLabel(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="ligand_label",
        contract=Contract(
            definition=Definition(
                grain="one row per ligand_key",
                identity=("ligand_key",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Name each compound that has a measurement against a kinase, so "
                    "that a ligand node carries a source name and structure rather "
                    "than an opaque hash.",
                    limitations=(
                        Limitation(
                            "Different sources name the same compound differently; "
                            "this relation keeps one name and does not claim it is "
                            "preferred."
                        ),
                        Limitation(
                            "The release states no approved-drug flag or ChEMBL "
                            "identity on these rows, so both are absent here."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one ligand_key."),
                    Claim("name and smiles are source values."),
                ),
            ),
        ),
    )

    ligand_key = computed_field(
        rows.shape.ligand_key,
        definition=FieldDefinition("The Pharos ligand identity."),
        meaning=Omitted,
    )
    target_count = computed_field(
        rows.shape.target_count,
        definition=FieldDefinition(
            "The number of distinct kinases the release measures this compound "
            "against.",
        ),
        meaning=Meaning(
            claims=(
                Claim("One value per ligand_key."),
                Claim(
                    "The value counts measured kinase targets in this extract, not "
                    "the compound's full target profile."
                ),
                Claim(
                    "A compound measured against one kinase here may bind others "
                    "outside the extract."
                ),
            ),
        ),
    )
    name = computed_field(
        rows.shape.name,
        definition=FieldDefinition(
            "A compound name the release states.",
            null_meaning="Absent when no measurement names the compound.",
        ),
        meaning=Omitted,
    )
    smiles = computed_field(
        rows.shape.smiles,
        definition=FieldDefinition(
            "A structure string the release states.",
            null_meaning="Absent when no measurement reports a structure.",
        ),
        meaning=Omitted,
    )
    pubchem_cid = computed_field(
        rows.shape.pubchem_cid,
        definition=FieldDefinition(
            "The PubChem compound identifier some measurement reports.",
            null_meaning="Absent when no measurement reports one.",
        ),
        meaning=Omitted,
    )
    isdrug = computed_field(
        rows.shape.isdrug,
        definition=FieldDefinition(
            "The approved-drug flag, which this source does not state.",
            null_meaning="Always absent on this source.",
        ),
        meaning=Omitted,
    )
    chembl_id = computed_field(
        rows.shape.chembl_id,
        definition=FieldDefinition(
            "The ChEMBL identity, which this source does not state.",
            null_meaning="Always absent on this source.",
        ),
        meaning=Omitted,
    )
