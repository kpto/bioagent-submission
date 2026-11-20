"""Publish one row per ligand and kinase target pair."""

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

from pharos_kg.modules.row_operations import ligand_target_pairs
from pharos_kg.relation.derived.kinase_activity.relation import KinaseActivity

rows = KinaseActivity.row_source().custom_op(ligand_target_pairs)


class LigandTargetPair(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="ligand_target_pair",
        contract=Contract(
            definition=Definition(
                grain="one row per ligand_key and target_key",
                identity=("ligand_key", "target_key"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State what the release measures for one compound against one "
                    "kinase: the number of measurements, their central value and "
                    "spread, and the citations they carry.",
                    limitations=(
                        Limitation(
                            "A measurement is an assay result, not a statement of "
                            "cellular effect or clinical benefit."
                        ),
                        Limitation(
                            "Mean and spread mix assay types; the activity_types are "
                            "not separated by potency scale."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one compound-target pair."),
                    Claim("count is the number of non-null measurements."),
                    Claim("min/max/mean are over the pair's measurements."),
                ),
            ),
        ),
    )

    ligand_key = computed_field(
        rows.shape.ligand_key,
        definition=FieldDefinition("The Pharos ligand identity."),
        meaning=Omitted,
    )
    target_key = computed_field(
        rows.shape.target_key,
        definition=FieldDefinition("The UniProt accession of the kinase target."),
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
                Claim("One value per ligand_key, repeated on each of its pairs."),
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
    count = computed_field(
        rows.shape.count,
        definition=FieldDefinition("The number of measurements for the pair."),
        meaning=Omitted,
    )
    mean_p_activity = computed_field(
        rows.shape.mean_p_activity,
        definition=FieldDefinition(
            "The mean activity value over the pair's measurements, rounded to six decimals.",
            null_meaning="Absent when no measurement reports a value.",
        ),
        meaning=Omitted,
    )
    std = computed_field(
        rows.shape.std,
        definition=FieldDefinition(
            "The population standard deviation of the pair's activity values, rounded to six decimals.",
            null_meaning="Absent when no measurement reports a value.",
        ),
        meaning=Omitted,
    )
    min_p_activity = computed_field(
        rows.shape.min_p_activity,
        definition=FieldDefinition(
            "The smallest activity value among the pair's measurements.",
            null_meaning="Absent when no measurement reports a value.",
        ),
        meaning=Omitted,
    )
    max_p_activity = computed_field(
        rows.shape.max_p_activity,
        definition=FieldDefinition(
            "The largest activity value among the pair's measurements.",
            null_meaning="Absent when no measurement reports a value.",
        ),
        meaning=Omitted,
    )
    pmids = computed_field(
        rows.shape.pmids,
        definition=FieldDefinition(
            "The distinct PubMed identifiers the pair's measurements cite."
        ),
        meaning=Omitted,
    )
    references = computed_field(
        rows.shape.references,
        definition=FieldDefinition(
            "The distinct reference strings the pair's measurements cite."
        ),
        meaning=Omitted,
    )
