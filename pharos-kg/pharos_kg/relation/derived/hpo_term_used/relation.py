"""Phenotype terms joined to the published disease edges that use them."""

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

from pharos_kg.relation.derived.disease_phenotype_graph.relation import (
    DiseasePhenotypeGraph,
)
from pharos_kg.relation.source.hpo_term import HpoTerm

rows = DiseasePhenotypeGraph.row_source().join(
    HpoTerm.row_source(),
    on=lambda phenotype, term: (phenotype.hpo_id, term.hpo_id),
)

shape = cast(Any, rows.shape)
left = shape.left
right = shape.right


class HpoTermUsed(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="hpo_term_used",
        contract=Contract(
            definition=Definition(
                grain="one row per published edge and its phenotype term",
                identity=("disease_key", "hpo_id"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Attach the ontology's label to every published phenotype edge, so "
                    "that the term a reader sees is the one the edge uses.",
                    limitations=(
                        Limitation(
                            "A row repeats for every published edge that uses the "
                            "term; the node list is the grouped relation."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one published edge with its term label."),
                    Claim("The label is the ontology's own name for the term."),
                ),
            ),
        ),
    )

    disease_key = computed_field(
        left.extract(lambda value: value.disease_key), meaning=Omitted
    )
    hpo_id = computed_field(
        left.extract(lambda value: value.hpo_id), meaning=Omitted
    )
    name = computed_field(
        right.extract(lambda value: value.name), meaning=Omitted
    )
