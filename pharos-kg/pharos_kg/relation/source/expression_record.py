"""One row per expression observation, as the release stores it."""

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


class ExpressionRecord(SourceRelation[PharosDump]):

    options = SourceRelationOptions(
        name="expression_record",
        contract=Contract(
            definition=Definition(
                grain="one row per expression observation",
                identity=("id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the release's expression table as it stands: one row is one "
                    "resource's observation of a protein in one tissue or cell type.",
                    limitations=(
                        Limitation(
                            "Rows come from different resources and methods; a "
                            "transcript observation is not a protein observation."
                        ),
                        Limitation(
                            "A row states detection at the release's granularity, not "
                            "a concentration."
                        ),
                        Limitation(
                            "protein_id and uberon_id are source keys; the mapping to "
                            "a kinase and to an anatomical term is a declared step."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one expression row in Pharos 3.19."),
                    Claim("No row is filtered, joined or aggregated here."),
                ),
            ),
        ),
    )

    id: Field[int] = field(
        definition=FieldDefinition("The row's identifier in the release."),
        meaning=Omitted,
    )
    etype: Field[str] = field(
        definition=FieldDefinition(
            "The expression resource and method, such as HPA Protein or HPA RNA.",
        ),
        meaning=Omitted,
    )
    protein_id: Field[int] = field(
        definition=FieldDefinition("The release's protein key."),
        meaning=Omitted,
    )
    tissue: Field[str] = field(
        definition=FieldDefinition(
            "The tissue or cell-type label the resource states.",
            null_meaning="Absent when the resource states no structure.",
        ),
        meaning=Omitted,
    )
    qual_value: Field[str] = field(
        definition=FieldDefinition(
            "The qualitative detection level, such as High, Medium or Low.",
            null_meaning="Absent when the resource reports no level.",
        ),
        meaning=Omitted,
    )
    expressed: Field[int] = field(
        definition=FieldDefinition(
            "The release's expressed flag for the observation.",
            null_meaning="Absent when the resource states no flag.",
        ),
        meaning=Omitted,
    )
    evidence: Field[str] = field(
        definition=FieldDefinition(
            "The evidence status the resource states.",
            null_meaning="Absent when the resource states none.",
        ),
        meaning=Omitted,
    )
    uberon_id: Field[str] = field(
        definition=FieldDefinition(
            "The UBERON term for the structure.",
            null_meaning="Absent when the resource states no ontology term.",
        ),
        meaning=Omitted,
    )
