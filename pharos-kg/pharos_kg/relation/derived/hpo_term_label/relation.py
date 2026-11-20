"""The phenotype terms the published edges use, with their labels."""

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

from pharos_kg.modules.row_operations import hp_term_labels
from pharos_kg.relation.derived.hpo_term_used.relation import HpoTermUsed

rows = HpoTermUsed.row_source().custom_op(hp_term_labels)


class HpoTermLabel(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="hpo_term_label",
        contract=Contract(
            definition=Definition(
                grain="one row per phenotype term the graph uses",
                identity=("hpo_id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Publish only the phenotype terms a published disease edge reaches, "
                    "so the graph does not carry an ontology's unused terms as isolated "
                    "nodes.",
                    limitations=(
                        Limitation(
                            "A term no published disease uses is absent, so the graph "
                            "cannot be browsed as a phenotype ontology."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one phenotype term used by at least one edge."),
                    Claim("The name is the ontology's label."),
                ),
            ),
        ),
    )

    hpo_id = computed_field(rows.shape.hpo_id, meaning=Omitted)
    name = computed_field(
        rows.shape.name,
        definition=FieldDefinition(
            "The ontology's label for the term.",
            null_meaning="Absent when the release gives no label.",
        ),
        meaning=Omitted,
    )
