"""Publish one label row per HGNC locus the kinase slice reaches."""

from kg_build_system import (
    Claim,
    Contract,
    Definition,
    DerivedRelation,
    DerivedRelationOptions,
    FieldDefinition,
    Limitation,
    Meaning,
    Omitted,
    Purpose,
    computed_field,
)

from pharos_kg.modules.row_operations import gene_labels
from pharos_kg.relation.derived.gene_keyed.relation import GeneKeyed

rows = GeneKeyed.row_source().custom_op(gene_labels)


class GeneLabel(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="gene_label",
        contract=Contract(
            definition=Definition(
                grain="one row per gene_key",
                identity=("gene_key",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Name each HGNC locus that encodes a kinase in the slice, using "
                    "the release's own identifier and symbol.",
                    limitations=(
                        Limitation(
                            "A locus that encodes no kinase in the slice is absent."
                        ),
                        Limitation(
                            "The symbol is the release's; aliases and previous "
                            "symbols are not carried."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one HGNC locus."),
                    Claim("protein_count is the number of kinase proteins it encodes."),
                ),
            ),
        ),
    )

    gene_key = computed_field(
        rows.shape.gene_key,
        definition=FieldDefinition("The HGNC identity."),
        meaning=Omitted,
    )
    symbol = computed_field(
        rows.shape.symbol,
        definition=FieldDefinition(
            "The symbol the release records for the locus.",
            null_meaning="Absent when the release states no symbol.",
        ),
        meaning=Omitted,
    )
    protein_count = computed_field(
        rows.shape.protein_count,
        definition=FieldDefinition(
            "The number of kinase proteins the locus encodes in the slice."
        ),
        meaning=Omitted,
    )
