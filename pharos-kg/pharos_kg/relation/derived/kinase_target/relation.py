"""Publish the kinase slice of the release's target table."""

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

from pharos_kg.relation.source.target import Target

rows = Target.row_source().where(
    lambda row: row.fam.alter_rows().drop_null().equals("Kinase")
)


class KinaseTarget(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="kinase_target",
        contract=Contract(
            definition=Definition(
                grain="one row per kinase target",
                identity=("target_id",),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Select the targets the release places in the kinase family, so "
                    "that the graph's scope is a stated selection over the release "
                    "rather than a query parameter.",
                    limitations=(
                        Limitation(
                            "Kinase is the release's family facet; it is not a "
                            "re-derived classification."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one target whose family is Kinase."),
                    Claim("No target outside that facet is included."),
                ),
            ),
        ),
    )

    target_id = computed_field(rows.shape.id, meaning=Omitted)
    tdl = computed_field(rows.shape.tdl, meaning=Omitted)
