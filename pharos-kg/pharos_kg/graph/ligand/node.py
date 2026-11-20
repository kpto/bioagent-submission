"""A chemical ligand measured against a kinase."""

from kg_build_system import (
    Claim,
    Limitation,
    Meaning,
    Node,
    NodeLabel,
    NodeOptions,
    PropertySlot,
    Purpose,
    property,
)

from pharos_kg.graph.annotated import AnnotatedNode
from pharos_kg.graph.annotations import BiolinkClass, KeyPrefix, OntologyTerm


class LigandNode(AnnotatedNode, Node):

    options = NodeOptions(
        name="ligand",
        annotations=(
            BiolinkClass("biolink:ChemicalEntity"),
            OntologyTerm("CHEBI:23888"),
            KeyPrefix(('PHAROS:',)),
            NodeLabel("Ligand"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the chemical entity for measured binding activity against a "
                "kinase.",
                limitations=(
                    Limitation(
                        "The extract does not model salts, formulations or metabolites."
                    ),
                    Limitation("A ligand may bind many targets; one edge is one pair."),
                ),
            ),
            claims=(
                Claim("A ligand is identified by its Pharos ligand identifier."),
                Claim(
                    "The isdrug flag is a classification, not a regulatory approval."
                ),
            ),
        ),
    )

    ligand_key: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The stable ligand identity, PHAROS:<ligand identifier>."),
                Claim("Use for graph identity."),
            ),
        ),
    )
    identifier: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The Pharos ligand identifier."),
                Claim("Use for cross-reference."),
            ),
        ),
    )
    target_count: PropertySlot[int] = property(
        meaning=Meaning(
            claims=(
                Claim("The number of kinases the release measures this ligand against."),
                Claim(
                    "Use to read how much target evidence the compound carries in "
                    "this extract."
                ),
                Claim(
                    "A count of measured kinases in the extract, not the compound's "
                    "full target profile."
                ),
            ),
        ),
    )
    name: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The ligand name reported by Pharos."),
                Claim("Use for display and search."),
            ),
        ),
    )
    isdrug: PropertySlot[bool | None] = property(
        meaning=Meaning(
            claims=(
                Claim("Whether Pharos classifies the ligand as a drug."),
                Claim("Use to stratify chemical entities."),
                Claim(
                    "The flag is not an approval, a formulation or a clinical "
                    "recommendation."
                ),
            ),
        ),
    )
    smiles: PropertySlot[str | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The canonical SMILES when the release provides one."),
                Claim("Use for chemistry, not identity."),
            ),
        ),
    )
    chembl_id: PropertySlot[str | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The ChEMBL identifier when the release provides one."),
                Claim("Use for cross-reference."),
            ),
        ),
    )
