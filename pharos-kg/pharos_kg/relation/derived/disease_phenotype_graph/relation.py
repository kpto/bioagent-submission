"""Disease phenotypes restricted to the diseases the graph publishes."""

from typing import Any, cast

from kg_build_system import (
    Array,
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

from pharos_kg.relation.derived.disease_label.relation import DiseaseLabel
from pharos_kg.relation.derived.disease_phenotype.relation import DiseasePhenotype

rows = DiseasePhenotype.row_source().join(
    DiseaseLabel.row_source(),
    on=lambda phenotype, disease: (phenotype.disease_key, disease.disease_key),
)

shape = cast(Any, rows.shape)
left = shape.left


class DiseasePhenotypeGraph(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="disease_phenotype_graph",
        contract=Contract(
            definition=Definition(
                grain="one row per published disease and phenotype term",
                identity=("disease_key", "hpo_id"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Publish the release's disease annotations only for diseases the "
                    "graph already carries, so every phenotype edge reaches a record "
                    "a reader can open.",
                    limitations=(
                        Limitation(
                            "A disease the release annotates but the kinase slice "
                            "never reaches is absent; the graph is scoped to the slice."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one published disease and one phenotype term."),
                    Claim("The join is on the disease identity, not on a name."),
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
    evidence = computed_field(
        left.extract(lambda value: value.evidence), meaning=Omitted
    )
    frequencies = computed_field(
        left.extract(lambda value: value.frequencies), meaning=Omitted
    )
    annotation_count = computed_field(
        left.extract(lambda value: value.annotation_count), meaning=Omitted
    )
