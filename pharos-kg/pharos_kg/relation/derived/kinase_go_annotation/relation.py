"""Attach the kinase protein to each GO annotation row."""

from typing import Any, cast

from kg_build_system import (
    Claim, Contract, Definition, DerivedRelation, DerivedRelationOptions,
    Limitation, Meaning, Omitted, Purpose, computed_field,
)

from pharos_kg.relation.derived.kinase_protein.relation import KinaseProtein
from pharos_kg.relation.source.go_annotation_record import GoAnnotationRecord

rows = GoAnnotationRecord.row_source().join(
    KinaseProtein.row_source(),
    on=lambda annotation, kinase: (annotation.protein_id, kinase.protein_id),
)

shape = cast(Any, rows.shape)


class KinaseGoAnnotation(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="kinase_go_annotation",
        contract=Contract(
            definition=Definition(
                grain="one row per GO annotation of a kinase protein",
                identity=("row_id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State which process, function or component the release "
                    "annotates a kinase with, and on what evidence.",
                    limitations=(
                        Limitation(
                            "An annotation whose protein is outside the slice is "
                            "absent."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one annotation of a kinase protein."),
                ),
            ),
        ),
    )

    row_id = computed_field(shape.left.extract(lambda value: value.id),
                            meaning=Omitted)
    target_key = computed_field(shape.right.extract(lambda value: value.uniprot),
                                meaning=Omitted)
    go_id = computed_field(shape.left.extract(lambda value: value.go_id),
                           meaning=Omitted)
    evidence = computed_field(shape.left.extract(lambda value: value.evidence),
                              meaning=Omitted)
    assigned_by = computed_field(
        shape.left.extract(lambda value: value.assigned_by), meaning=Omitted
    )
    go_type = computed_field(shape.left.extract(lambda value: value.go_type),
                             meaning=Omitted)
