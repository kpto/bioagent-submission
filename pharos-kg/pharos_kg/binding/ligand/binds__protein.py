"""Bind the ligand_activity relation to the binds edge."""

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
from pharos_kg.graph.ligand.binds__protein import BindsEdge
from pharos_kg.relation.derived.ligand_target_pair.relation import (
    LigandTargetPair,
)


binds_binding = edge_binding(
    target=BindsEdge,
    rows=LigandTargetPair.row_source(),
    bind=lambda row: EdgeValues(
        build_key=row.ligand_key
        .append("::BINDS::")
        .append(row.target_key.prepend("PHAROS:")),
        source_build_key=row.ligand_key,
        target_build_key=row.target_key.prepend("PHAROS:"),
        properties=BindsEdge(
            **unannotated(),
            mean_p_activity=row.mean_p_activity,
            std=row.std,
            count=row.count,
            target_count=row.target_count,
            pmids=row.pmids,
            references=row.references,
            min_p_activity=row.min_p_activity,
            max_p_activity=row.max_p_activity,
        ),
    ),
    name="binds",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The ligand_target_pair relation fulfils the BINDS use as the measured "
                "link from a ligand to a kinase: each row supplies one edge, keyed "
                "by the ligand and target ids, covering every measured pair.",
                limitations=(
                    Limitation(
                        "Activity is binding evidence, not efficacy or safety."
                    ),
                ),
            ),
            claims=(
                Claim("One ligand_activity row produces one binds edge."),
            ),
        ),
    ),
)
