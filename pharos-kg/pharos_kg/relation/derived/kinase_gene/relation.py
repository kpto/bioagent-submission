"""Attach the HGNC locus the release records to each kinase protein."""

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
from pharos_kg.relation.source.gene_xref import GeneXref

rows = GeneXref.row_source().where(
    lambda row: row.xtype.alter_rows().drop_null().equals("HGNC")
).join(
    KinaseProtein.row_source(),
    on=lambda xref, kinase: (xref.protein_id, kinase.protein_id),
)

shape = cast(Any, rows.shape)


class KinaseGene(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="kinase_gene",
        contract=Contract(
            definition=Definition(
                grain="one row per HGNC locus and kinase protein",
                identity=("row_id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State which HGNC locus the release records for a kinase protein, "
                    "so that the gene a reader looks up is the one the release names.",
                    limitations=(
                        Limitation(
                            "A kinase whose protein carries no HGNC cross-reference "
                            "has no gene here; the absence is the release's."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one HGNC cross-reference of a kinase protein."),
                ),
            ),
        ),
    )

    row_id = computed_field(
        shape.left.extract(lambda value: value.id), meaning=Omitted
    )
    hgnc_value = computed_field(
        shape.left.extract(lambda value: value.value), meaning=Omitted
    )
    target_key = computed_field(
        shape.right.extract(lambda value: value.uniprot), meaning=Omitted
    )
    symbol = computed_field(
        shape.right.extract(lambda value: value.symbol), meaning=Omitted
    )
