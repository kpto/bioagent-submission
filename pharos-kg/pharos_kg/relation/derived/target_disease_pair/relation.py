"""Publish one row per kinase target and disease pair."""

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
    value_expression,
)

from pharos_kg.modules.row_operations import pair_rows
from pharos_kg.relation.derived.target_disease_contribution.relation import (
    TargetDiseaseContribution,
)

rows = TargetDiseaseContribution.row_source().custom_op(pair_rows)


class TargetDiseasePair(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="target_disease_pair",
        contract=Contract(
            definition=Definition(
                grain="one row per target_key and disease_key",
                identity=("target_key", "disease_key"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State what the release reports for one kinase and one disease: "
                    "the contributing methods, the largest confidence and score, and "
                    "the number of rows behind them.",
                    limitations=(
                        Limitation(
                            "The counts and maxima are over the release's rows, not "
                            "over the literature; a source that contributes many rows "
                            "weighs more than one that contributes few."
                        ),
                        Limitation(
                            "A name-derived disease key is a last resort and is less "
                            "stable than a CURIE."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one target-disease pair."),
                    Claim("evidence_count is the number of contribution rows, with no "
                          "cap."),
                    Claim("max_conf and max_score are maxima over those rows."),
                ),
            ),
        ),
    )

    target_key = computed_field(
        rows.shape.target_key,
        definition=FieldDefinition("The UniProt accession of the kinase target."),
        meaning=Omitted,
    )
    disease_key = computed_field(
        rows.shape.disease_key,
        definition=FieldDefinition(
            "The disease identity: a MONDO CURIE, a namespaced source identifier, "
            "or a name-derived key."
        ),
        meaning=Omitted,
    )
    pair_key = computed_field(
        rows.shape.pair_key,
        definition=FieldDefinition(
            "The target and disease keys as one string, so that another relation "
            "can join on the pair without repeating the key expressions."
        ),
        meaning=Omitted,
    )
    evidence_count = computed_field(
        rows.shape.evidence_count,
        definition=FieldDefinition(
            "The number of contribution rows the release holds for the pair."
        ),
        meaning=Omitted,
    )
    max_conf = computed_field(
        rows.shape.max_conf,
        definition=FieldDefinition(
            "The largest confidence among the pair's contribution rows.",
            null_meaning="Absent when no row reports a confidence.",
        ),
        meaning=Omitted,
    )
    max_score = computed_field(
        rows.shape.max_score,
        definition=FieldDefinition(
            "The largest score among the pair's contribution rows.",
            null_meaning="Absent when no row reports a score.",
        ),
        meaning=Omitted,
    )
    evidence_types = computed_field(
        rows.shape.evidence_types,
        definition=FieldDefinition(
            "The distinct contributing methods, sorted ascending.",
            null_meaning="Absent when no row names a method.",
        ),
        meaning=Omitted,
    )
    sources = computed_field(
        rows.shape.sources,
        definition=FieldDefinition(
            "The distinct contributing sources, sorted ascending.",
            null_meaning="Absent when no row names a source.",
        ),
        meaning=Omitted,
    )
