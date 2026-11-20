"""Publish one row per kinase disease contribution."""

from typing import Any, cast

from kg_build_system import (
    Claim,
    Contract,
    Definition,
    DerivedRelation,
    DerivedRelationOptions,
    Limitation,
    Meaning,
    Omitted,
    Purpose,
    computed_field,
)

from pharos_kg.relation.derived.kinase_protein.relation import KinaseProtein
from pharos_kg.relation.source.disease_evidence import DiseaseEvidence

rows = DiseaseEvidence.row_source().join(
    KinaseProtein.row_source(),
    on=lambda contribution, protein: (
        contribution.protein_id, protein.protein_id,
    ),
)

shape = cast(Any, rows.shape)
left = shape.left
right = shape.right


class TargetDiseaseContribution(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="target_disease_contribution",
        contract=Contract(
            definition=Definition(
                grain="one row per kinase disease contribution",
                identity=("contribution_id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Attach the kinase protein identity to each disease contribution "
                    "the release holds, so that grouping and labelling read one row "
                    "per source record rather than one row per pair.",
                    limitations=(
                        Limitation(
                            "A target-disease pair appears as many rows as the "
                            "release's sources contributed; this relation does not "
                            "group them."
                        ),
                        Limitation(
                            "mondo_id and did are the row's own values; a row can "
                            "carry neither."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one disease contribution for a kinase target."),
                    Claim("No contribution is filtered by type, source or score."),
                ),
            ),
        ),
    )

    contribution_id = computed_field(
        left.extract(lambda value: value.id), meaning=Omitted
    )
    target_id = computed_field(
        right.extract(lambda value: value.target_id), meaning=Omitted
    )
    tdl = computed_field(right.extract(lambda value: value.tdl), meaning=Omitted)
    target_key = computed_field(
        right.extract(lambda value: value.uniprot), meaning=Omitted
    )
    target_symbol = computed_field(
        right.extract(lambda value: value.symbol), meaning=Omitted
    )
    protein_name = computed_field(
        right.extract(lambda value: value.name), meaning=Omitted
    )
    disease_name = computed_field(
        left.extract(lambda value: value.name), meaning=Omitted
    )
    ncats_name = computed_field(
        left.extract(lambda value: value.ncats_name), meaning=Omitted
    )
    mondo_id = computed_field(
        left.extract(lambda value: value.mondoid), meaning=Omitted
    )
    did = computed_field(left.extract(lambda value: value.did), meaning=Omitted)
    evidence_type = computed_field(
        left.extract(lambda value: value.dtype), meaning=Omitted
    )
    evidence_source = computed_field(
        left.extract(lambda value: value.source), meaning=Omitted
    )
    evidence = computed_field(
        left.extract(lambda value: value.evidence), meaning=Omitted
    )
    reference = computed_field(
        left.extract(lambda value: value.reference), meaning=Omitted
    )
    conf = computed_field(left.extract(lambda value: value.conf), meaning=Omitted)
    score = computed_field(left.extract(lambda value: value.score), meaning=Omitted)
