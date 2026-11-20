"""Attach the GO term's label and aspect to each kinase annotation."""

from typing import Any, cast

from kg_build_system import (
    Claim, Contract, Definition, DerivedRelation, DerivedRelationOptions,
    Limitation, Meaning, Omitted, Purpose, computed_field,
)

from pharos_kg.relation.derived.kinase_go_annotation.relation import (
    KinaseGoAnnotation,
)
from pharos_kg.relation.source.go_term_record import GoTermRecord

rows = KinaseGoAnnotation.row_source().join(
    GoTermRecord.row_source(),
    on=lambda annotation, term: (annotation.go_id, term.go_id),
)

shape = cast(Any, rows.shape)


class KinaseGoTerm(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="kinase_go_term",
        contract=Contract(
            definition=Definition(
                grain="one row per GO annotation of a kinase, with its term",
                identity=("row_id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State the term a kinase annotation refers to, as the ontology "
                    "names it, so that the process a reader sees is the annotated one.",
                    limitations=(
                        Limitation(
                            "An annotation whose term is absent from the term table "
                            "is absent here."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one annotation joined to its GO term."),
                ),
            ),
        ),
    )

    row_id = computed_field(shape.left.extract(lambda value: value.row_id),
                            meaning=Omitted)
    target_key = computed_field(
        shape.left.extract(lambda value: value.target_key), meaning=Omitted
    )
    go_key = computed_field(shape.left.extract(lambda value: value.go_id),
                            meaning=Omitted)
    label = computed_field(shape.right.extract(lambda value: value.name),
                           meaning=Omitted)
    aspect = computed_field(shape.right.extract(lambda value: value.namespace),
                            meaning=Omitted)
    evidence = computed_field(shape.left.extract(lambda value: value.evidence),
                              meaning=Omitted)
    assigned_by = computed_field(
        shape.left.extract(lambda value: value.assigned_by), meaning=Omitted
    )
