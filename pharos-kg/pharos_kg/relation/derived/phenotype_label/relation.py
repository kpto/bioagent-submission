"""Publish one label row per phenotype term the kinase slice reaches."""

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

from pharos_kg.modules.row_operations import phenotype_labels
from pharos_kg.relation.derived.kinase_phenotype.relation import KinasePhenotype

rows = KinasePhenotype.row_source().custom_op(phenotype_labels)


class PhenotypeLabel(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="phenotype_label",
        contract=Contract(
            definition=Definition(
                grain="one row per phenotype_key",
                identity=("phenotype_key",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Name each phenotype term the release observes for a kinase, with "
                    "the coarser term it groups under.",
                    limitations=(
                        Limitation(
                            "A term no kinase in the slice is observed with is absent."
                        ),
                        Limitation(
                            "The coarser term is the release's grouping, not a parent "
                            "inferred from the ontology."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one MP term used by the kinase slice."),
                    Claim("label and top-level term are the release's values."),
                ),
            ),
        ),
    )

    phenotype_key = computed_field(
        rows.shape.phenotype_key,
        definition=FieldDefinition("The MP term identity."),
        meaning=Omitted,
    )
    label = computed_field(
        rows.shape.label,
        definition=FieldDefinition(
            "The phenotype term name.",
            null_meaning="Absent when the release states no name.",
        ),
        meaning=Omitted,
    )
    top_level_key = computed_field(
        rows.shape.top_level_key,
        definition=FieldDefinition(
            "The coarser MP term the release groups the observation under.",
            null_meaning="Absent when the release states no grouping.",
        ),
        meaning=Omitted,
    )
    top_level_label = computed_field(
        rows.shape.top_level_label,
        definition=FieldDefinition(
            "The name of the coarser MP term.",
            null_meaning="Absent when the release states no grouping.",
        ),
        meaning=Omitted,
    )
