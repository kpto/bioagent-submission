"""Gene-phenotype annotations for the kinase slice."""

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

from pharos_kg.relation.derived.gene_phenotype_protein.relation import (
    GenePhenotypeProtein,
)
from pharos_kg.relation.derived.kinase_protein.relation import KinaseProtein

rows = GenePhenotypeProtein.row_source().join(
    KinaseProtein.row_source(),
    on=lambda annotation, kinase: (annotation.uniprot, kinase.uniprot),
)

shape = cast(Any, rows.shape)
left = shape.left


class GenePhenotypeKinase(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="gene_phenotype_kinase",
        contract=Contract(
            definition=Definition(
                grain="one row per kinase, phenotype and recording disease",
                identity=("uniprot", "hpo_id", "disease_id"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Restrict the release's gene annotations to the kinases the graph "
                    "carries, so that a phenotype edge only ever attaches to a "
                    "protein a reader can open.",
                    limitations=(
                        Limitation(
                            "A kinase the protein table reaches through a non-kinase "
                            "target row is absent, by construction of the kinase "
                            "slice."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one annotation for a kinase in the graph."),
                    Claim("The kinase slice is the one the rest of the graph uses."),
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
    frequency = computed_field(
        left.extract(lambda value: value.frequency), meaning=Omitted
    )
    disease_id = computed_field(
        left.extract(lambda value: value.disease_id), meaning=Omitted
    )
