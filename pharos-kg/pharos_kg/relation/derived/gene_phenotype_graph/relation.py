"""Kinase phenotypes restricted to terms the disease layer publishes."""

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

from pharos_kg.relation.derived.gene_phenotype_term.relation import (
    GenePhenotypeTerm,
)
from pharos_kg.relation.derived.hpo_term_label.relation import HpoTermLabel

rows = GenePhenotypeTerm.row_source().join(
    HpoTermLabel.row_source(),
    on=lambda annotation, term: (annotation.hpo_id, term.hpo_id),
)

shape = cast(Any, rows.shape)
left = shape.left


class GenePhenotypeGraph(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="gene_phenotype_graph",
        contract=Contract(
            definition=Definition(
                grain="one row per kinase, published phenotype term and disease",
                identity=("uniprot", "hpo_id", "disease_id"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Publish a kinase's recorded phenotypes only against terms the "
                    "graph already carries, so every phenotype edge reaches a node.",
                    limitations=(
                        Limitation(
                            "A term only a gene annotation uses, and no published "
                            "disease annotation, is absent; the graph states one "
                            "phenotype vocabulary, not two."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one kinase annotation for a published term."),
                    Claim("The term set is the one the disease layer publishes."),
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
        left.extract(lambda value: value.name), meaning=Omitted
    )
    disease_id = computed_field(
        left.extract(lambda value: value.disease_id), meaning=Omitted
    )
