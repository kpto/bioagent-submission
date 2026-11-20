"""One row per disease annotation, mapped to a MONDO disease key."""

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

from pharos_kg.relation.source.hpo_disease_phenotype import HpoDiseasePhenotype
from pharos_kg.relation.source.mondo_xref import MondoXref

rows = HpoDiseasePhenotype.row_source().join(
    MondoXref.row_source(),
    on=lambda annotation, xref: (annotation.disease_id, xref.source_id),
)
rows = rows.where(
    lambda joined: joined.left.extract(lambda value: value.qualifier)
    .default_to("")
    .equals("NOT")
    .not_()
)

shape = cast(Any, rows.shape)
left = shape.left
right = shape.right


class DiseasePhenotypeAnnotation(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="disease_phenotype_annotation",
        contract=Contract(
            definition=Definition(
                grain="one row per MONDO disease, phenotype and evidence",
                identity=("disease_key", "hpo_id", "evidence"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Carry each release annotation to the MONDO identity the graph "
                    "uses, keeping the reference it cites, so that a phenotype edge "
                    "can be traced to the annotation behind it.",
                    limitations=(
                        Limitation(
                            "An annotation whose disease is absent from MONDO's "
                            "cross-references is dropped by the join."
                        ),
                        Limitation(
                            "One source disease can map to several MONDO terms, so one "
                            "annotation can appear against more than one disease key."
                        ),
                        Limitation(
                            "NOT-qualified rows are removed here, not in the reader: "
                            "the release states an exclusion and the graph states a "
                            "presence."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one annotation, mapped to MONDO."),
                    Claim("The mapping is MONDO's own cross-reference."),
                ),
            ),
        ),
    )

    disease_key = computed_field(
        right.extract(lambda value: value.mondo_id), meaning=Omitted
    )
    hpo_id = computed_field(
        left.extract(lambda value: value.hpo_id), meaning=Omitted
    )
    evidence = computed_field(
        left.extract(lambda value: value.evidence), meaning=Omitted
    )
    frequency = computed_field(
        left.extract(lambda value: value.frequency), meaning=Omitted
    )
