"""One row per target-disease pair, stating the strongest Open Targets evidence."""

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

from pharos_kg.modules.row_operations import evidence_classes
from pharos_kg.relation.derived.target_disease_evidence.relation import (
    TargetDiseaseEvidence,
)

rows = TargetDiseaseEvidence.row_source().custom_op(evidence_classes)


class OtEvidencePair(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="ot_evidence_pair",
        contract=Contract(
            definition=Definition(
                grain="one row per target-disease pair the platform reports",
                identity=("pair_key",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State, for one pair, which kinds of independent evidence the "
                    "platform reports and how strong the strongest kind is, so that "
                    "another relation can attach that statement without repeating "
                    "the mapping.",
                    limitations=(
                        Limitation(
                            "The class is the strongest class present, not a score; "
                            "one genetic row outweighs many literature rows."
                        ),
                        Limitation(
                            "A pair the platform does not list is absent from this "
                            "relation rather than reading none."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one pair the platform reports evidence for."),
                    Claim("The class follows the platform's data-type column."),
                ),
            ),
        ),
    )

    pair_key = computed_field(
        rows.shape.pair_key,
        definition=FieldDefinition("The target and disease keys as one string."),
        meaning=Omitted,
    )
    evidence_class = computed_field(
        rows.shape.evidence_class,
        definition=FieldDefinition(
            "high for a genetic, somatic-mutation or known-drug row, "
            "literature_only for any other data type."
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Separate evidence that a target is causally implicated from evidence "
                "that it was mentioned alongside the disease.",
                limitations=(
                    Limitation(
                        "The class summarises the platform's data types, not study "
                        "quality."
                    ),
                ),
            ),
            claims=(
                Claim("high requires at least one genetic, somatic-mutation or "
                      "known-drug row."),
                Claim("The class is the strongest class present for the pair."),
            ),
        ),
    )
