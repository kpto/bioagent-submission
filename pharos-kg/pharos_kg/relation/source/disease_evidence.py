"""One row per disease-association contribution, as the release stores it."""

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


class DiseaseEvidence(SourceRelation[PharosDump]):

    options = SourceRelationOptions(
        name="disease_evidence",
        contract=Contract(
            definition=Definition(
                grain="one row per disease contribution",
                identity=("id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the release's disease table as it stands: one row is one "
                    "source's contribution to a target-disease association.",
                    limitations=(
                        Limitation(
                            "A target-disease pair can have many rows; this relation "
                            "does not group them."
                        ),
                        Limitation(
                            "protein_id and did are source keys, not graph keys; the "
                            "mapping to UniProt and to a disease identifier is a "
                            "declared step, not a property of this relation."
                        ),
                        Limitation(
                            "dtype names the contributing method, not the strength of "
                            "the association."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one disease row in Pharos 3.19."),
                    Claim("No row is filtered, joined, renamed or aggregated here."),
                ),
            ),
        ),
    )

    id: Field[int] = field(
        definition=FieldDefinition("The row's identifier in the release."),
        meaning=Omitted,
    )
    dtype: Field[str] = field(
        definition=FieldDefinition(
            "The contributing method, naming a disease_type row.",
        ),
        meaning=Omitted,
    )
    protein_id: Field[int] = field(
        definition=FieldDefinition(
            "The release's protein key for the target.",
            null_meaning="Absent when the row names no protein.",
        ),
        meaning=Omitted,
    )
    nhprotein_id: Field[int] = field(
        definition=FieldDefinition(
            "The release's non-human protein key, when the contribution came "
            "from another organism.",
            null_meaning="Absent for human contributions.",
        ),
        meaning=Omitted,
    )
    name: Field[str] = field(
        definition=FieldDefinition("The disease name as the source states it."),
        meaning=Omitted,
    )
    ncats_name: Field[str] = field(
        definition=FieldDefinition("The disease name after NCATS normalisation."),
        meaning=Omitted,
    )
    did: Field[str] = field(
        definition=FieldDefinition(
            "The source's disease identifier, for example MIM:219500.",
            null_meaning="Absent when the source names no identifier.",
        ),
        meaning=Omitted,
    )
    evidence: Field[str] = field(
        definition=FieldDefinition(
            "The source's evidence text for this contribution.",
            null_meaning="Absent when the source states none.",
        ),
        meaning=Omitted,
    )
    zscore: Field[float] = field(
        definition=FieldDefinition(
            "The source's z-score for this contribution.",
            null_meaning="Absent for sources that report none.",
        ),
        meaning=Omitted,
    )
    conf: Field[float] = field(
        definition=FieldDefinition(
            "The source's confidence for this contribution.",
            null_meaning="Absent for sources that report none.",
        ),
        meaning=Omitted,
    )
    description: Field[str] = field(
        definition=FieldDefinition(
            "The source's description of the disease.",
            null_meaning="Absent when the source states none.",
        ),
        meaning=Omitted,
    )
    reference: Field[str] = field(
        definition=FieldDefinition(
            "The source's citation for this contribution.",
            null_meaning="Absent when the source cites none.",
        ),
        meaning=Omitted,
    )
    drug_name: Field[str] = field(
        definition=FieldDefinition(
            "The drug named by a drug-indication contribution.",
            null_meaning="Absent for non-drug contributions.",
        ),
        meaning=Omitted,
    )
    log2foldchange: Field[float] = field(
        name="log2foldchange",
        definition=FieldDefinition(
            "The expression log2 fold change reported for this contribution.",
            null_meaning="Absent for non-expression contributions.",
        ),
        meaning=Omitted,
    )
    pvalue: Field[str] = field(
        definition=FieldDefinition(
            "The reported p-value, kept as the source wrote it.",
            null_meaning="Absent when the source reports none.",
        ),
        meaning=Omitted,
    )
    score: Field[float] = field(
        definition=FieldDefinition(
            "The source's association score for this contribution.",
            null_meaning="Absent for sources that report none.",
        ),
        meaning=Omitted,
    )
    source: Field[str] = field(
        definition=FieldDefinition(
            "The data source that contributed this row.",
            null_meaning="Absent when the row names no source.",
        ),
        meaning=Omitted,
    )
    o2s: Field[float] = field(
        name="O2S",
        definition=FieldDefinition(
            "The release's object-to-subject score for this contribution.",
            null_meaning="Absent for sources that report none.",
        ),
        meaning=Omitted,
    )
    s2o: Field[float] = field(
        name="S2O",
        definition=FieldDefinition(
            "The release's subject-to-object score for this contribution.",
            null_meaning="Absent for sources that report none.",
        ),
        meaning=Omitted,
    )
    mondoid: Field[str] = field(
        definition=FieldDefinition(
            "The MONDO identifier recorded on the row.",
            null_meaning="Absent when the row was not mapped to MONDO.",
        ),
        meaning=Omitted,
    )
    updated: Field[int] = field(
        definition=FieldDefinition(
            "The release's update flag for this row.",
            null_meaning="Absent when the release states none.",
        ),
        meaning=Omitted,
    )
