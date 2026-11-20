"""Publish one label row per disease the kinase slice reaches."""

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

from pharos_kg.modules.row_operations import label_rows
from pharos_kg.relation.derived.target_disease_contribution.relation import (
    TargetDiseaseContribution,
)

rows = TargetDiseaseContribution.row_source().custom_op(label_rows)


class DiseaseLabel(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="disease_label",
        contract=Contract(
            definition=Definition(
                grain="one row per disease_key",
                identity=("disease_key",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Name each disease the kinase slice reaches, using the release's "
                    "own labels and identifiers, so that a disease node carries what "
                    "the sources wrote rather than a name the project chose.",
                    limitations=(
                        Limitation(
                            "A disease can be written differently by different "
                            "sources; this relation keeps the lexicographically "
                            "smallest name and does not claim it is preferred."
                        ),
                        Limitation(
                            "doid is present only when some contribution carried a "
                            "DOID; its absence is not evidence that the disease has "
                            "no DOID."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one disease_key."),
                    Claim("mondo_id and doid are source values, not derived mappings."),
                ),
            ),
        ),
    )

    disease_key = computed_field(
        rows.shape.disease_key,
        definition=FieldDefinition(
            "The disease identity used by every kinase relation."
        ),
        meaning=Omitted,
    )
    name = computed_field(
        rows.shape.name,
        definition=FieldDefinition(
            "The disease name the release states.",
            null_meaning="Absent when no contribution names the disease.",
        ),
        meaning=Omitted,
    )
    ncats_name = computed_field(
        rows.shape.ncats_name,
        definition=FieldDefinition(
            "The disease name after NCATS normalisation.",
            null_meaning="Absent when no contribution carries one.",
        ),
        meaning=Omitted,
    )
    mondo_id = computed_field(
        rows.shape.mondo_id,
        definition=FieldDefinition(
            "The MONDO identifier carried by some contribution.",
            null_meaning="Absent when no contribution carries a MONDO id.",
        ),
        meaning=Omitted,
    )
    doid = computed_field(
        rows.shape.doid,
        definition=FieldDefinition(
            "The DOID carried by some contribution.",
            null_meaning="Absent when no contribution carries a DOID.",
        ),
        meaning=Omitted,
    )
