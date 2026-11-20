"""One row per target-disease evidence row, as Open Targets stores it."""

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

from pharos_kg.asset.opentargets import OpenTargets


class OtAssociation(SourceRelation[OpenTargets]):

    options = SourceRelationOptions(
        name="ot_association",
        contract=Contract(
            definition=Definition(
                grain="one row per disease, target and data type",
                identity=("disease_id", "ensembl_id", "datatype"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the platform's per-data-type association scores as they "
                    "stand, so that the graph can say which kind of evidence "
                    "supports a target-disease pair and how much of it there is.",
                    limitations=(
                        Limitation(
                            "A data type is one of the platform's own classes "
                            "(genetic association, somatic mutation, known drug, "
                            "literature, expression, pathway, animal model)."
                        ),
                        Limitation(
                            "The score is the platform's per-datatype aggregation, "
                            "not a probability and not comparable across data types."
                        ),
                        Limitation(
                            "The ensembl_id is a target key, not a protein; mapping "
                            "it to UniProt is a declared step in a derived relation."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one data-type row in the 26.09 release."),
                    Claim("No row is filtered, joined, renamed or aggregated here."),
                ),
            ),
        ),
    )

    disease_id: Field[str] = field(
        definition=FieldDefinition(
            "The disease identity as a CURIE, such as MONDO:0005148.",
            null_meaning="Absent when the release row names no disease.",
        ),
        meaning=Omitted,
    )
    ensembl_id: Field[str] = field(
        definition=FieldDefinition("The Ensembl gene identifier of the target."),
        meaning=Omitted,
    )
    datatype: Field[str] = field(
        definition=FieldDefinition("The platform's data-type class for the row."),
        meaning=Omitted,
    )
    score: Field[float] = field(
        definition=FieldDefinition(
            "The platform's association score for this data type.",
            null_meaning="Absent when the data type contributes no score.",
        ),
        meaning=Omitted,
    )
    evidence_count: Field[int] = field(
        definition=FieldDefinition(
            "The number of evidence items the data type contributed.",
            null_meaning="Absent when the data type reports no count.",
        ),
        meaning=Omitted,
    )
