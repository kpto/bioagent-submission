"""Bind the protein_phenotype_pair relation to the has_phenotype edge."""

from kg_build_system import (
    BindingOptions,
    Claim,
    EdgeValues,
    Limitation,
    Meaning,
    Purpose,
    edge_binding,
)

from pharos_kg.graph.annotated import unannotated
from pharos_kg.graph.protein.has_phenotype__phenotype import HasPhenotypeEdge
from pharos_kg.relation.derived.protein_phenotype_pair.relation import (
    ProteinPhenotypePair,
)


has_phenotype_binding = edge_binding(
    target=HasPhenotypeEdge,
    rows=ProteinPhenotypePair.row_source(),
    bind=lambda row: EdgeValues(
        build_key=row.target_key.prepend("PHAROS:")
        .append("::HAS_PHENOTYPE::")
        .append(row.phenotype_key),
        source_build_key=row.target_key.prepend("PHAROS:"),
        target_build_key=row.phenotype_key,
        properties=HasPhenotypeEdge(
            **unannotated(),
            sources=row.sources,
            procedures=row.procedures,
            min_p_value=row.min_p_value,
            count=row.count,
        ),
    ),
    name="has_phenotype",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The protein_phenotype_pair relation fulfils the HAS PHENOTYPE use as "
                "an observation link from a kinase to an MP term: each row supplies "
                "one edge, keyed by target and term, covering every phenotype "
                "observation the slice reaches.",
                limitations=(
                    Limitation(
                        "The observation is about a model organism's ortholog, so the "
                        "edge is not a claim about a human carrier."
                    ),
                    Limitation(
                        "A phenotype direction, such as increased or decreased, is "
                        "not carried by this edge."
                    ),
                ),
            ),
            claims=(
                Claim("One protein_phenotype_pair row produces one edge."),
            ),
        ),
    ),
)
