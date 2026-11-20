"""Publish one row per unordered kinase interaction pair."""

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

from pharos_kg.modules.row_operations import interaction_pairs
from pharos_kg.relation.derived.kinase_interaction_pair.relation import (
    KinaseInteractionPair,
)

rows = KinaseInteractionPair.row_source().custom_op(interaction_pairs)


class ProteinInteractionPair(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="protein_interaction_pair",
        contract=Contract(
            definition=Definition(
                grain="one row per unordered pair of kinase targets",
                identity=("source_target_key", "target_target_key"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State what the release reports for one unordered pair of "
                    "kinases: the reporting sources, the largest score and "
                    "probabilities, and the number of rows behind them.",
                    limitations=(
                        Limitation(
                            "Most reports carry no p_int; absence of a probability is "
                            "not evidence of a weak interaction."
                        ),
                        Limitation(
                            "A pair reported once by a predicted source and once by an "
                            "experimental source is one row here; the sources list "
                            "keeps both."
                        ),
                        Limitation(
                            "Self-interactions are excluded: the release's mock rows "
                            "report a protein against itself and are not edges."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one unordered kinase pair."),
                    Claim("Every reporting row for the pair contributes to row_count."),
                    Claim("score, p_int and p_ni are maxima over the pair's rows."),
                    Claim(
                        "evidence_class is experimental when any contributing row "
                        "names a source other than STRING, and predicted otherwise."
                    ),
                ),
            ),
        ),
    )

    source_target_key = computed_field(
        rows.shape.source_target_key,
        definition=FieldDefinition("The first UniProt accession in canonical order."),
        meaning=Omitted,
    )
    target_target_key = computed_field(
        rows.shape.target_target_key,
        definition=FieldDefinition("The second UniProt accession in canonical order."),
        meaning=Omitted,
    )
    row_count = computed_field(
        rows.shape.row_count,
        definition=FieldDefinition(
            "The number of interaction rows the release holds for the pair."
        ),
        meaning=Omitted,
    )
    score = computed_field(
        rows.shape.score,
        definition=FieldDefinition(
            "The largest reporting score among the pair's rows.",
            null_meaning="Absent when no row reports a score.",
        ),
        meaning=Omitted,
    )
    p_int = computed_field(
        rows.shape.p_int,
        definition=FieldDefinition(
            "The largest probability of interaction among the pair's rows.",
            null_meaning="Absent when no row reports one.",
        ),
        meaning=Omitted,
    )
    p_ni = computed_field(
        rows.shape.p_ni,
        definition=FieldDefinition(
            "The largest probability of no interaction among the pair's rows.",
            null_meaning="Absent when no row reports one.",
        ),
        meaning=Omitted,
    )
    sources = computed_field(
        rows.shape.sources,
        definition=FieldDefinition(
            "The distinct reporting source strings, sorted ascending."
        ),
        meaning=Omitted,
    )
    evidence_class = computed_field(
        rows.shape.evidence_class,
        definition=FieldDefinition(
            "Whether the pair has experimental support or only prediction."
        ),
        meaning=Omitted,
    )
