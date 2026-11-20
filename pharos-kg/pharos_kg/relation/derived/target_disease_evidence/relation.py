"""One row per target-disease data type, keyed by UniProt and disease CURIE."""

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

from pharos_kg.relation.source.ot_association import OtAssociation
from pharos_kg.relation.source.ot_target_protein import OtTargetProtein

rows = OtAssociation.row_source().join(
    OtTargetProtein.row_source(),
    on=lambda association, target: (association.ensembl_id, target.ensembl_id),
)
rows = rows.where(
    lambda joined: joined.right.extract(lambda value: value.source)
    .alter_rows()
    .drop_null()
    .equals("uniprot_swissprot")
)

shape = cast(Any, rows.shape)
left = shape.left
right = shape.right


class TargetDiseaseEvidence(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="target_disease_evidence",
        contract=Contract(
            definition=Definition(
                grain="one row per target, disease and data type",
                identity=("target_key", "disease_key", "datatype"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Attach a reviewed protein identity to each per-data-type "
                    "association the platform publishes, so that an evidence row "
                    "names the same target the rest of the graph names.",
                    limitations=(
                        Limitation(
                            "Only Swiss-Prot identifiers are kept; a target the "
                            "platform reaches only through TrEMBL or Ensembl protein "
                            "identifiers is unmapped here, not absent from biology."
                        ),
                        Limitation(
                            "A target that lists several Swiss-Prot accessions "
                            "produces one row per accession; the relation does not "
                            "choose between them."
                        ),
                        Limitation(
                            "The disease key is the platform's CURIE. A platform "
                            "disease in another ontology (EFO, HP, Orphanet) stays in "
                            "that ontology and does not match a MONDO graph key."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one data type for one target-disease pair."),
                    Claim("The score and count are the platform's, unchanged."),
                    Claim("No evidence row is filtered by score or by data type."),
                ),
            ),
        ),
    )

    target_key = computed_field(
        right.extract(lambda value: value.protein_id), meaning=Omitted
    )
    disease_key = computed_field(
        left.extract(lambda value: value.disease_id), meaning=Omitted
    )
    datatype = computed_field(
        left.extract(lambda value: value.datatype), meaning=Omitted
    )
    score = computed_field(left.extract(lambda value: value.score), meaning=Omitted)
    evidence_count = computed_field(
        left.extract(lambda value: value.evidence_count), meaning=Omitted
    )
    protein_source = computed_field(
        right.extract(lambda value: value.source), meaning=Omitted
    )
