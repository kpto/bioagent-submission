"""One row per gene-phenotype annotation, as the release stores it."""

from kg_build_system import (
    Claim,
    Contract,
    Definition,
    Field,
    FieldDefinition,
    Limitation,
    Meaning,
    Omitted,
    Purpose,
    SourceRelation,
    SourceRelationOptions,
    field,
)

from pharos_kg.asset.hpo import Hpo


class HpoGenePhenotype(SourceRelation[Hpo]):

    options = SourceRelationOptions(
        name="hpo_gene_phenotype",
        contract=Contract(
            definition=Definition(
                grain="one row per gene, phenotype and recording disease",
                identity=("ncbi_gene_id", "hpo_id", "disease_id"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Read the release's gene annotations as they stand, so that a "
                    "target can state the phenotypes its variants were recorded with "
                    "even when no target-disease row reaches that disease.",
                    limitations=(
                        Limitation(
                            "The gene identifier is NCBI's; mapping it to a UniProt "
                            "accession is a declared join."
                        ),
                        Limitation(
                            "The disease column names the disease the annotation was "
                            "recorded in, so a row can restate a target-disease "
                            "association the graph already holds."
                        ),
                        Limitation(
                            "A phenotype recorded for a gene is not a phenotype every "
                            "variant of that gene produces."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one gene annotation in the release."),
                    Claim("No row is filtered by frequency or by disease."),
                ),
            ),
        ),
    )

    ncbi_gene_id: Field[int] = field(
        definition=FieldDefinition("The NCBI gene identifier of the gene."),
        meaning=Omitted,
    )
    hpo_id: Field[str] = field(
        definition=FieldDefinition("The phenotype term's accession."),
        meaning=Omitted,
    )
    frequency: Field[str] = field(
        definition=FieldDefinition(
            "The frequency as the release states it.",
            null_meaning="Absent when the release states no frequency.",
        ),
        meaning=Omitted,
    )
    disease_id: Field[str] = field(
        definition=FieldDefinition(
            "The disease the annotation was recorded in.",
            null_meaning="Absent when the release names no disease.",
        ),
        meaning=Omitted,
    )
