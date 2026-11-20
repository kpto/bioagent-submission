"""Bind the ligands relation to the ligand record."""

from kg_build_system import (
    BindingOptions,
    Claim,
    Limitation,
    Meaning,
    NodeValues,
    Purpose,
    node_binding,
)

from pharos_kg.graph.annotated import unannotated
from pharos_kg.graph.ligand.node import LigandNode
from pharos_kg.relation.derived.ligand_label.relation import LigandLabel


ligand_binding = node_binding(
    target=LigandNode,
    rows=LigandLabel.row_source(),
    bind=lambda row: NodeValues(
        build_key=row.ligand_key,
        properties=LigandNode(
            **unannotated(),
            ligand_key=row.ligand_key,
            identifier=row.ligand_key,
            name=row.name.default_to(row.ligand_key),
            target_count=row.target_count,
            isdrug=row.isdrug,
            smiles=row.smiles,
            chembl_id=row.chembl_id,
        ),
    ),
    name="ligand",
    options=BindingOptions(
        meaning=Meaning(
            purpose=Purpose(
                "The ligand_label relation fulfils the LIGAND use as one chemical record "
                "per Pharos ligand identity: each row supplies one node, keyed by "
                "the ligand key, covering every ligand the extract names.",
                limitations=(
                    Limitation(
                        "A ligand that has no kinase activity in this extract is "
                        "absent."
                    ),
                ),
            ),
            claims=(
                Claim("One ligands row produces one ligand node."),
            ),
        ),
    ),
)
