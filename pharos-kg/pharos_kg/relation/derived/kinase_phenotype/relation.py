"""Attach the kinase protein to each phenotype observation."""

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
from pharos_kg.relation.source.phenotype_record import PhenotypeRecord

rows = PhenotypeRecord.row_source().join(
    KinaseProtein.row_source(),
    on=lambda observation, kinase: (observation.protein_id, kinase.protein_id),
)

shape = cast(Any, rows.shape)


class KinasePhenotype(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="kinase_phenotype",
        contract=Contract(
            definition=Definition(
                grain="one row per phenotype observation of a kinase",
                identity=("row_id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State which phenotype the release observes for a kinase, in which "
                    "programme and with which p-value.",
                    limitations=(
                        Limitation(
                            "An observation whose protein is outside the kinase slice "
                            "is absent."
                        ),
                        Limitation(
                            "The observation is in a model system, so the row speaks "
                            "about the ortholog."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one phenotype observation of a kinase."),
                    Claim("No observation is filtered by p-value or programme."),
                ),
            ),
        ),
    )

    row_id = computed_field(
        shape.left.extract(lambda value: value.id), meaning=Omitted
    )
    target_key = computed_field(
        shape.right.extract(lambda value: value.uniprot), meaning=Omitted
    )
    phenotype_key = computed_field(
        shape.left.extract(lambda value: value.term_id), meaning=Omitted
    )
    label = computed_field(
        shape.left.extract(lambda value: value.term_name), meaning=Omitted
    )
    top_level_key = computed_field(
        shape.left.extract(lambda value: value.top_level_term_id), meaning=Omitted
    )
    top_level_label = computed_field(
        shape.left.extract(lambda value: value.top_level_term_name), meaning=Omitted
    )
    programme = computed_field(
        shape.left.extract(lambda value: value.ptype), meaning=Omitted
    )
    procedure = computed_field(
        shape.left.extract(lambda value: value.procedure_name), meaning=Omitted
    )
    p_value = computed_field(
        shape.left.extract(lambda value: value.p_value), meaning=Omitted
    )
    gp_assoc = computed_field(
        shape.left.extract(lambda value: value.gp_assoc), meaning=Omitted
    )
