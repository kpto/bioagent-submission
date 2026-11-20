"""One row per cross-reference the release records for a protein."""

from kg_build_system import (
    Claim,
    Contract,
    Definition,
    Field,
    FieldDefinition,
    Limitation,
    Meaning,
    Omitted,
    Purpose,
    SourceRelation,
    SourceRelationOptions,
    field,
)

from pharos_kg.asset.pharos_source import PharosDump


class GeneXref(SourceRelation[PharosDump]):

    options = SourceRelationOptions(
        name="gene_xref",
        contract=Contract(
            definition=Definition(
                grain="one row per protein cross-reference",
                identity=("id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the cross-references the release records for a protein, so "
                    "that a gene locus is the identifier the release states rather "
                    "than a symbol matched by name.",
                    limitations=(
                        Limitation(
                            "A cross-reference is a mapping the release asserts; it "
                            "does not state that the mapping is reviewed."
                        ),
                        Limitation(
                            "A protein can carry several cross-references of the same "
                            "kind."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one xref row in Pharos 3.19."),
                    Claim("No cross-reference is preferred or translated here."),
                ),
            ),
        ),
    )

    id: Field[int] = field(
        definition=FieldDefinition("The cross-reference row's identifier."),
        meaning=Omitted,
    )
    protein_id: Field[int] = field(
        definition=FieldDefinition("The release's protein key."),
        meaning=Omitted,
    )
    xtype: Field[str] = field(
        definition=FieldDefinition(
            "The cross-reference kind, for example HGNC.",
            null_meaning="Absent when the release states no kind.",
        ),
        meaning=Omitted,
    )
    value: Field[str] = field(
        definition=FieldDefinition(
            "The cross-reference value in its own namespace.",
            null_meaning="Absent when the release states no value.",
        ),
        meaning=Omitted,
    )
