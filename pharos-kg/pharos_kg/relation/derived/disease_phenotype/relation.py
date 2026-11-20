"""One row per published disease and phenotype term."""

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

from pharos_kg.modules.row_operations import disease_phenotype_pairs
from pharos_kg.relation.derived.disease_phenotype_annotation.relation import (
    DiseasePhenotypeAnnotation,
)

rows = DiseasePhenotypeAnnotation.row_source().custom_op(disease_phenotype_pairs)


class DiseasePhenotype(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="disease_phenotype",
        contract=Contract(
            definition=Definition(
                grain="one row per MONDO disease and phenotype term",
                identity=("disease_key", "hpo_id"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State which phenotypes a disease is recorded with, once per "
                    "phenotype, so that a graph edge is one clinical statement rather "
                    "than one row per paper.",
                    limitations=(
                        Limitation(
                            "The edge states that the phenotype was recorded for the "
                            "disease, not that every patient has it; frequency is the "
                            "release's text, not a probability."
                        ),
                        Limitation(
                            "Co-occurrence of two phenotypes in one disease is not "
                            "evidence of a shared mechanism."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one disease and one phenotype term."),
                    Claim("annotation_count states how many rows the pair aggregates."),
                ),
            ),
        ),
    )

    disease_key = computed_field(
        rows.shape.disease_key, meaning=Omitted
    )
    hpo_id = computed_field(rows.shape.hpo_id, meaning=Omitted)
    evidence = computed_field(
        rows.shape.evidence,
        definition=FieldDefinition(
            "A reference or evidence code for the annotations.",
            null_meaning="Absent when no annotation cites evidence.",
        ),
        meaning=Omitted,
    )
    frequencies = computed_field(
        rows.shape.frequencies,
        definition=FieldDefinition(
            "The distinct frequencies the annotations state, sorted ascending.",
            null_meaning="Absent when no annotation states a frequency.",
        ),
        meaning=Omitted,
    )
    annotation_count = computed_field(
        rows.shape.annotation_count, meaning=Omitted
    )
