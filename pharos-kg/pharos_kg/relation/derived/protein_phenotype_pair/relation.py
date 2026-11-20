"""Publish one row per kinase and phenotype term."""

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

from pharos_kg.modules.row_operations import protein_phenotype_pairs
from pharos_kg.relation.derived.kinase_phenotype.relation import KinasePhenotype

rows = KinasePhenotype.row_source().custom_op(protein_phenotype_pairs)


class ProteinPhenotypePair(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="protein_phenotype_pair",
        contract=Contract(
            definition=Definition(
                grain="one row per target and phenotype term",
                identity=("target_key", "phenotype_key"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "State that a kinase perturbation is associated with a phenotype "
                    "term, which programmes report it and how small the reported "
                    "p-value is.",
                    limitations=(
                        Limitation(
                            "The association is observed in a model system, not in "
                            "human carriers."
                        ),
                        Limitation(
                            "The smallest p-value across mixed procedures is a "
                            "summary, not a single test."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one target and one MP term."),
                    Claim("sources and procedures are the distinct values behind the "
                          "pair."),
                ),
            ),
        ),
    )

    target_key = computed_field(
        rows.shape.target_key,
        definition=FieldDefinition("The UniProt accession of the kinase."),
        meaning=Omitted,
    )
    phenotype_key = computed_field(
        rows.shape.phenotype_key,
        definition=FieldDefinition("The MP term identity."),
        meaning=Omitted,
    )
    sources = computed_field(
        rows.shape.sources,
        definition=FieldDefinition(
            "The contributing programmes, sorted ascending."
        ),
        meaning=Omitted,
    )
    procedures = computed_field(
        rows.shape.procedures,
        definition=FieldDefinition("The distinct procedures, sorted ascending."),
        meaning=Omitted,
    )
    min_p_value = computed_field(
        rows.shape.min_p_value,
        definition=FieldDefinition(
            "The smallest p-value the release reports for the pair.",
            null_meaning="Absent when no row reports a p-value.",
        ),
        meaning=Omitted,
    )
    count = computed_field(
        rows.shape.count,
        definition=FieldDefinition("The number of rows behind the pair."),
        meaning=Omitted,
    )
