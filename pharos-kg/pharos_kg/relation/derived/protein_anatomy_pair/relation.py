"""Publish one row per kinase and anatomical structure."""

from kg_build_system import (
    Array,
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

from pharos_kg.modules.row_operations import protein_anatomy_pairs
from pharos_kg.relation.derived.kinase_expression.relation import KinaseExpression

rows = KinaseExpression.row_source().custom_op(protein_anatomy_pairs)


class ProteinAnatomyPair(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="protein_anatomy_pair",
        contract=Contract(
            definition=Definition(
                grain="one row per target and anatomical structure",
                identity=("target_key", "anatomical_key"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State that a kinase is detected in an anatomical structure with "
                    "strong or medium protein-level evidence, and by which resources.",
                    limitations=(
                        Limitation(
                            "Only protein-level High and Medium detections become "
                            "edges; transcript evidence and weak detections are not "
                            "asserted as locations."
                        ),
                        Limitation(
                            "Detection is not abundance and does not state function at "
                            "the site."
                        ),
                    ),
                ),
                claims=(
                    Claim(
                        "One row is one target and one UBERON structure with High or "
                        "Medium protein-level detection."
                    ),
                    Claim("level is the strongest detection the release reports."),
                ),
            ),
        ),
    )

    target_key = computed_field(
        rows.shape.target_key,
        definition=FieldDefinition("The UniProt accession of the kinase."),
        meaning=Omitted,
    )
    anatomical_key = computed_field(
        rows.shape.anatomical_key,
        definition=FieldDefinition("The UBERON term identity."),
        meaning=Omitted,
    )
    level = computed_field(
        rows.shape.level,
        definition=FieldDefinition("The strongest detection level, High or Medium."),
        meaning=Omitted,
    )
    sources = computed_field(
        rows.shape.sources,
        definition=FieldDefinition(
            "The supporting expression resources, sorted ascending."
        ),
        meaning=Omitted,
    )
    count = computed_field(
        rows.shape.count,
        definition=FieldDefinition(
            "The number of supporting expression rows."
        ),
        meaning=Omitted,
    )
