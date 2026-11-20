"""Attach the kinase protein to each pathway membership."""

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
from pharos_kg.relation.source.pathway_record import PathwayRecord

rows = PathwayRecord.row_source().join(
    KinaseProtein.row_source(),
    on=lambda membership, kinase: (membership.protein_id, kinase.protein_id),
)

shape = cast(Any, rows.shape)


class KinasePathway(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="kinase_pathway",
        contract=Contract(
            definition=Definition(
                grain="one row per pathway membership of a kinase",
                identity=("row_id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State which pathway a kinase belongs to in each database that "
                    "curates one, with the identifier and page the release names.",
                    limitations=(
                        Limitation(
                            "A membership whose protein is outside the kinase slice is "
                            "absent."
                        ),
                        Limitation(
                            "A database row with no identifier and no page cannot be "
                            "named and is absent from the graph's pathway nodes."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one database membership of a kinase."),
                    Claim("No row is filtered by database or pathway size."),
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
    source = computed_field(
        shape.left.extract(lambda value: value.pwtype), meaning=Omitted
    )
    source_id = computed_field(
        shape.left.extract(lambda value: value.id_in_source), meaning=Omitted
    )
    label = computed_field(
        shape.left.extract(lambda value: value.name), meaning=Omitted
    )
    url = computed_field(
        shape.left.extract(lambda value: value.url), meaning=Omitted
    )
