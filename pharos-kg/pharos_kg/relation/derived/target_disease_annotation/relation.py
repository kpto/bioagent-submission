"""Each target-disease pair with the Open Targets evidence class it carries."""

from typing import Any, cast

from kg_build_system import (
    Array,
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

from pharos_kg.relation.derived.ot_evidence_pair.relation import OtEvidencePair
from pharos_kg.relation.derived.target_disease_pair.relation import TargetDiseasePair

rows = TargetDiseasePair.row_source().join(
    OtEvidencePair.row_source(),
    on=lambda pair, evidence: (pair.pair_key, evidence.pair_key),
    how="left",
)

shape = cast(Any, rows.shape)
left = shape.left
right = shape.right


class TargetDiseaseAnnotation(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="target_disease_annotation",
        contract=Contract(
            definition=Definition(
                grain="one row per target_key and disease_key",
                identity=("pair_key",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Carry each target-disease pair together with the evidence class "
                    "the platform reports for it, so that the graph edge states both "
                    "the release's own records and the independent second opinion.",
                    limitations=(
                        Limitation(
                            "A pair the platform does not list reads none; none is "
                            "the absence of a platform row, not of evidence."
                        ),
                        Limitation(
                            "The join is on UniProt and a disease CURIE, so a pair "
                            "the platform reports under another ontology reads none."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one target-disease pair."),
                    Claim("The pair fields are the target_disease_pair fields, "
                          "unchanged."),
                    Claim("evidence_class defaults to none when the platform lists "
                          "no row."),
                ),
            ),
        ),
    )

    pair_key = computed_field(
        left.extract(lambda value: value.pair_key), meaning=Omitted
    )
    target_key = computed_field(
        left.extract(lambda value: value.target_key), meaning=Omitted
    )
    disease_key = computed_field(
        left.extract(lambda value: value.disease_key), meaning=Omitted
    )
    evidence_count = computed_field(
        left.extract(lambda value: value.evidence_count), meaning=Omitted
    )
    max_conf = computed_field(
        left.extract(lambda value: value.max_conf), meaning=Omitted
    )
    max_score = computed_field(
        left.extract(lambda value: value.max_score), meaning=Omitted
    )
    evidence_types = computed_field(
        left.extract(lambda value: value.evidence_types), meaning=Omitted
    )
    sources = computed_field(
        left.extract(lambda value: value.sources), meaning=Omitted
    )
    evidence_class = computed_field(
        right.extract(lambda value: value.evidence_class).default_to("none"),
        definition=FieldDefinition(
            "The strongest independent evidence class the platform reports, or none."
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Say what kind of independent evidence stands behind the pair.",
                limitations=(
                    Limitation("The class is the strongest class present, not a "
                               "score."),
                    Limitation("none means the platform lists no row for the pair."),
                ),
            ),
            claims=(
                Claim("high means a genetic, somatic-mutation or known-drug row."),
                Claim("literature_only means any other platform data type."),
            ),
        ),
    )
