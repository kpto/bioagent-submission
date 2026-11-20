"""Publish one row per gene and kinase protein, with a normalised gene key."""

from kg_build_system import (
    Claim, Contract, Definition, DerivedRelation, DerivedRelationOptions,
    FieldDefinition, Meaning, Omitted, Purpose, computed_field,
)

from pharos_kg.modules.row_operations import gene_keys
from pharos_kg.relation.derived.kinase_gene.relation import KinaseGene

rows = KinaseGene.row_source().custom_op(gene_keys)


class GeneKeyed(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="gene_keyed",
        contract=Contract(
            definition=Definition(
                grain="one row per HGNC locus and kinase protein",
                identity=("gene_key", "target_key"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State which HGNC locus encodes which kinase protein, with the "
                    "locus written as a stable identifier rather than as a bare "
                    "number.",
                ),
                claims=(
                    Claim("One row is one locus-protein pair the release maps."),
                    Claim("gene_key is an HGNC CURIE in every row."),
                ),
            ),
        ),
    )

    gene_key = computed_field(
        rows.shape.gene_key,
        definition=FieldDefinition("The HGNC identity as a CURIE."),
        meaning=Omitted,
    )
    target_key = computed_field(
        rows.shape.target_key,
        definition=FieldDefinition("The UniProt accession of the kinase."),
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
