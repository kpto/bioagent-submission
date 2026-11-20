"""Gene-phenotype annotations carrying the UniProt accession of the gene."""

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

from pharos_kg.relation.source.hpo_gene_phenotype import HpoGenePhenotype
from pharos_kg.relation.source.protein import Protein

rows = HpoGenePhenotype.row_source().join(
    Protein.row_source(),
    on=lambda annotation, protein: (annotation.ncbi_gene_id, protein.geneid),
)

shape = cast(Any, rows.shape)
left = shape.left
right = shape.right


class GenePhenotypeProtein(DerivedRelation(rows)):
    options = DerivedRelationOptions(
        name="gene_phenotype_protein",
        contract=Contract(
            definition=Definition(
                grain="one row per UniProt accession, phenotype and recording disease",
                identity=("uniprot", "hpo_id", "disease_id"),
            ),
            meaning=Meaning(
                purpose=Purpose(
                    "Carry each gene annotation to the UniProt accession the graph "
                    "names, so that a phenotype can attach to a protein rather than "
                    "to a gene identifier.",
                    limitations=(
                        Limitation(
                            "The join is on the release's NCBI gene identifier; a gene "
                            "absent from the protein table is unmapped here."
                        ),
                        Limitation(
                            "A gene with several protein rows produces one row per "
                            "accession; the relation does not choose between them."
                        ),
                    ),
                ),
                claims=(
                    Claim("One row is one gene annotation with a UniProt accession."),
                    Claim("The gene to protein mapping is the release's own table."),
                ),
            ),
        ),
    )

    uniprot = computed_field(
        right.extract(lambda value: value.uniprot), meaning=Omitted
    )
    hpo_id = computed_field(
        left.extract(lambda value: value.hpo_id), meaning=Omitted
    )
    frequency = computed_field(
        left.extract(lambda value: value.frequency), meaning=Omitted
    )
    disease_id = computed_field(
        left.extract(lambda value: value.disease_id), meaning=Omitted
    )
