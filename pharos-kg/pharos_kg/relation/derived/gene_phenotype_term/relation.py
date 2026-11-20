"""Kinase phenotype annotations with the ontology's label for the term."""

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

from pharos_kg.relation.derived.gene_phenotype_kinase.relation import (
    GenePhenotypeKinase,
)
from pharos_kg.relation.source.hpo_term import HpoTerm

rows = GenePhenotypeKinase.row_source().join(
    HpoTerm.row_source(),
    on=lambda annotation, term: (annotation.hpo_id, term.hpo_id),
)

shape = cast(Any, rows.shape)
left = shape.left
right = shape.right


class GenePhenotypeTerm(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="gene_phenotype_term",
        contract=Contract(
            definition=Definition(
                grain="one row per kinase, phenotype term and recording disease",
                identity=("uniprot", "hpo_id", "disease_id"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Attach the ontology's label to each kinase phenotype, so that a "
                    "protein's phenotype edge reads as a term name and not only as an "
                    "accession.",
                    limitations=(
                        Limitation(
                            "The row repeats per recording disease; the edge binding "
                            "aggregates it."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one kinase annotation with its term label."),
                    Claim("The label is the ontology's own name for the term."),
                ),
            ),
        ),
    )

    uniprot = computed_field(
        left.extract(lambda value: value.uniprot), meaning=Omitted
    )
    hpo_id = computed_field(
        left.extract(lambda value: value.hpo_id), meaning=Omitted
    )
    name = computed_field(
        right.extract(lambda value: value.name), meaning=Omitted
    )
    disease_id = computed_field(
        left.extract(lambda value: value.disease_id), meaning=Omitted
    )
