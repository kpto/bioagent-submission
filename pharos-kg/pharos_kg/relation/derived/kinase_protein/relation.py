"""Publish the protein record for each kinase target-protein link."""

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

from pharos_kg.relation.derived.kinase_target_protein.relation import (
    KinaseTargetProtein,
)
from pharos_kg.relation.source.protein import Protein

rows = KinaseTargetProtein.row_source().join(
    Protein.row_source(),
    on=lambda link, record: (link.protein_id, record.id),
)

shape = cast(Any, rows.shape)
left = shape.left
right = shape.right


class KinaseProtein(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="kinase_protein",
        contract=Contract(
            definition=Definition(
                grain="one row per kinase target and its protein record",
                identity=("target_id", "protein_id"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Attach the release's protein record to each kinase link, so that "
                    "the UniProt accession and the symbol are the release's own values.",
                    limitations=(
                        Limitation(
                            "protein.family is the UniProt family prose, not the "
                            "release's IDG family facet; the slice comes from the target "
                            "table."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one kinase target-protein link with its protein "
                          "record."),
                    Claim("uniprot is carried through unchanged."),
                ),
            ),
        ),
    )

    target_id = computed_field(
        left.extract(lambda value: value.target_id), meaning=Omitted
    )
    tdl = computed_field(left.extract(lambda value: value.tdl), meaning=Omitted)
    protein_id = computed_field(
        left.extract(lambda value: value.protein_id), meaning=Omitted
    )
    uniprot = computed_field(
        right.extract(lambda value: value.uniprot), meaning=Omitted
    )
    symbol = computed_field(right.extract(lambda value: value.sym), meaning=Omitted)
    name = computed_field(right.extract(lambda value: value.name), meaning=Omitted)
    description = computed_field(
        right.extract(lambda value: value.description), meaning=Omitted
    )
    family = computed_field(
        right.extract(lambda value: value.family), meaning=Omitted
    )
