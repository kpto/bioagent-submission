"""Publish one label row per pathway the kinase slice reaches."""

from kg_build_system import (
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

from pharos_kg.modules.row_operations import pathway_labels
from pharos_kg.relation.derived.kinase_pathway.relation import KinasePathway

rows = KinasePathway.row_source().custom_op(pathway_labels)


class PathwayLabel(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="pathway_label",
        contract=Contract(
            definition=Definition(
                grain="one row per pathway_key",
                identity=("pathway_key",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Name each pathway a kinase belongs to, with the database that "
                    "curates it and the identifier it uses.",
                    limitations=(
                        Limitation(
                            "A pathway no kinase in the slice belongs to is absent; "
                            "the graph does not carry a pathway catalogue."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one pathway used by the kinase slice."),
                    Claim("label, source and source_id are the database's values."),
                ),
            ),
        ),
    )

    pathway_key = computed_field(
        rows.shape.pathway_key,
        definition=FieldDefinition("The pathway identity as a CURIE."),
        meaning=Omitted,
    )
    label = computed_field(
        rows.shape.label,
        definition=FieldDefinition(
            "The pathway name the source database states.",
            null_meaning="Absent when the release states no name.",
        ),
        meaning=Omitted,
    )
    source = computed_field(
        rows.shape.source,
        definition=FieldDefinition(
            "The database that curates the pathway.",
            null_meaning="Absent when the release states no database.",
        ),
        meaning=Omitted,
    )
    source_id = computed_field(
        rows.shape.source_id,
        definition=FieldDefinition(
            "The identifier the source database uses.",
            null_meaning="Absent when the identifier is carried only in the page.",
        ),
        meaning=Omitted,
    )
    url = computed_field(
        rows.shape.url,
        definition=FieldDefinition(
            "The page the release links for the pathway.",
            null_meaning="Absent when the release links no page.",
        ),
        meaning=Omitted,
    )
