"""One row per GO annotation, as the release stores it."""

from kg_build_system import (
    Claim, Contract, Definition, Field, FieldDefinition, Limitation, Meaning,
    Omitted, Purpose, SourceRelation, SourceRelationOptions, field,
)

from pharos_kg.asset.pharos_source import PharosDump


class GoAnnotationRecord(SourceRelation[PharosDump]):

    options = SourceRelationOptions(
        name="go_annotation_record",
        contract=Contract(
            definition=Definition(
                grain="one row per GO annotation",
                identity=("id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read every GO annotation the release holds, with its evidence "
                    "code and assigner, so that a protein's process membership is a "
                    "declared summary of annotations.",
                    limitations=(
                        Limitation(
                            "An annotation is a curator or pipeline assertion about a "
                            "protein, not a statement about a disease."
                        ),
                        Limitation(
                            "Evidence codes differ in strength; this relation keeps "
                            "them apart rather than weighting them."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one goa row in Pharos 3.19."),
                    Claim("No annotation is filtered by evidence code here."),
                ),
            ),
        ),
    )

    id: Field[int] = field(
        definition=FieldDefinition("The annotation's identifier."),
        meaning=Omitted,
    )
    protein_id: Field[int] = field(
        definition=FieldDefinition("The release's protein key."),
        meaning=Omitted,
    )
    go_id: Field[str] = field(
        definition=FieldDefinition("The GO term identifier."),
        meaning=Omitted,
    )
    evidence: Field[str] = field(
        definition=FieldDefinition(
            "The evidence code the annotation reports.",
            null_meaning="Absent when the annotation reports none.",
        ),
        meaning=Omitted,
    )
    assigned_by: Field[str] = field(
        definition=FieldDefinition(
            "The group that made the annotation.",
            null_meaning="Absent when the annotation names none.",
        ),
        meaning=Omitted,
    )
    go_type: Field[str] = field(
        definition=FieldDefinition(
            "The GO aspect the annotation reports.",
            null_meaning="Absent when the annotation states none.",
        ),
        meaning=Omitted,
    )
