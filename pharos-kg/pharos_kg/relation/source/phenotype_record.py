"""One row per phenotype observation, as the release stores it."""

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


class PhenotypeRecord(SourceRelation[PharosDump]):

    options = SourceRelationOptions(
        name="phenotype_record",
        contract=Contract(
            definition=Definition(
                grain="one row per phenotype observation",
                identity=("id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the release's phenotype table as it stands: one row is one "
                    "observation of a phenotype for a perturbed gene.",
                    limitations=(
                        Limitation(
                            "The observation is usually in a model organism; the "
                            "release states the ortholog's phenotype, not a human "
                            "carrier's."
                        ),
                        Limitation(
                            "protein_id and term_id are source keys; the mapping to "
                            "UniProt and to an MP term is a declared step."
                        ),
                        Limitation(
                            "ptype names the contributing programme, not the strength "
                            "of the observation."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one phenotype row in Pharos 3.19."),
                    Claim("No row is filtered, joined or aggregated here."),
                ),
            ),
        ),
    )

    id: Field[int] = field(
        definition=FieldDefinition("The row's identifier in the release."),
        meaning=Omitted,
    )
    ptype: Field[str] = field(
        definition=FieldDefinition(
            "The contributing programme, such as IMPC or OMIM.",
        ),
        meaning=Omitted,
    )
    protein_id: Field[int] = field(
        definition=FieldDefinition(
            "The release's protein key for the perturbed gene.",
            null_meaning="Absent when the row names no protein.",
        ),
        meaning=Omitted,
    )
    term_id: Field[str] = field(
        definition=FieldDefinition(
            "The MP term the observation is stated in.",
            null_meaning="Absent when the row states no term.",
        ),
        meaning=Omitted,
    )
    term_name: Field[str] = field(
        definition=FieldDefinition(
            "The MP term's name.",
            null_meaning="Absent when the row states no term.",
        ),
        meaning=Omitted,
    )
    top_level_term_id: Field[str] = field(
        definition=FieldDefinition(
            "The coarser MP term the release groups the observation under.",
            null_meaning="Absent when the release states no grouping.",
        ),
        meaning=Omitted,
    )
    top_level_term_name: Field[str] = field(
        definition=FieldDefinition(
            "The name of the coarser MP term.",
            null_meaning="Absent when the release states no grouping.",
        ),
        meaning=Omitted,
    )
    p_value: Field[float] = field(
        definition=FieldDefinition(
            "The p-value the row reports.",
            null_meaning="Absent when the row reports none.",
        ),
        meaning=Omitted,
    )
    procedure_name: Field[str] = field(
        definition=FieldDefinition(
            "The procedure the observation used.",
            null_meaning="Absent when the row names no procedure.",
        ),
        meaning=Omitted,
    )
    gp_assoc: Field[int] = field(
        definition=FieldDefinition(
            "The release's genotype-phenotype association flag.",
            null_meaning="Absent when the row states none.",
        ),
        meaning=Omitted,
    )
