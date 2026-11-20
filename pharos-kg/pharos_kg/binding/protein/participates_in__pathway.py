"""Bind the protein_pathway_pair relation to the participates_in_pathway edge."""

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
from pharos_kg.graph.protein.participates_in__pathway import (
    ParticipatesInPathwayEdge,
)
from pharos_kg.relation.derived.protein_pathway_pair.relation import (
    ProteinPathwayPair,
)


pathway_binding = edge_binding(
    target=ParticipatesInPathwayEdge,
    rows=ProteinPathwayPair.row_source(),
    bind=lambda row: EdgeValues(
        build_key=row.target_key.prepend("PHAROS:")
        .append("::PARTICIPATES_IN_PATHWAY::")
        .append(row.pathway_key),
        source_build_key=row.target_key.prepend("PHAROS:"),
        target_build_key=row.pathway_key,
        properties=ParticipatesInPathwayEdge(
            **unannotated(),
            source=row.source.default_to("unknown"),
            url=row.url,
            count=row.count,
        ),
    ),
    name="participates_in_pathway",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The protein_pathway_pair relation fulfils the PARTICIPATES IN "
                "PATHWAY use as a membership link from a kinase to a curated "
                "pathway: each row supplies one edge, keyed by target and pathway, "
                "covering every membership the slice reaches.",
                limitations=(
                    Limitation(
                        "The edge is a database's curation and does not state a "
                        "physical interaction or a direction."
                    ),
                ),
            ),
            claims=(
                Claim("One protein_pathway_pair row produces one edge."),
            ),
        ),
    ),
)
