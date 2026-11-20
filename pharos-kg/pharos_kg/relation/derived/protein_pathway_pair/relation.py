"""Publish one row per kinase and pathway."""

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

from pharos_kg.modules.row_operations import protein_pathway_pairs
from pharos_kg.relation.derived.kinase_pathway.relation import KinasePathway

rows = KinasePathway.row_source().custom_op(protein_pathway_pairs)


class ProteinPathwayPair(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="protein_pathway_pair",
        contract=Contract(
            definition=Definition(
                grain="one row per target and pathway",
                identity=("target_key", "pathway_key"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State that a kinase belongs to a curated pathway, in which "
                    "database, under which identifier.",
                    limitations=(
                        Limitation(
                            "A membership is a database's curation, not an observed "
                            "interaction."
                        ),
                        Limitation(
                            "The identifier is derived from the release's source id or "
                            "page; a row with neither cannot be named and is absent."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one kinase in one source database's pathway."),
                    Claim("pathway_key is a CURIE in every row."),
                ),
            ),
        ),
    )

    target_key = computed_field(
        rows.shape.target_key,
        definition=FieldDefinition("The UniProt accession of the kinase."),
        meaning=Omitted,
    )
    pathway_key = computed_field(
        rows.shape.pathway_key,
        definition=FieldDefinition(
            "The pathway identity as a CURIE, such as Reactome:R-HSA-164843."
        ),
        meaning=Omitted,
    )
    source = computed_field(
        rows.shape.source,
        definition=FieldDefinition(
            "The database that curates the pathway.",
            null_meaning="Absent when no row states a database.",
        ),
        meaning=Omitted,
    )
    url = computed_field(
        rows.shape.url,
        definition=FieldDefinition(
            "The page the release links for the pathway.",
            null_meaning="Absent when no row links a page.",
        ),
        meaning=Omitted,
    )
    count = computed_field(
        rows.shape.count,
        definition=FieldDefinition(
            "The number of release rows asserting the membership."
        ),
        meaning=Omitted,
    )
