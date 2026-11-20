"""A kinase protein identified by UniProt."""

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


class ProteinNode(AnnotatedNode, Node):

    options = NodeOptions(
        name="protein",
        annotations=(
            BiolinkClass("biolink:Protein"),
            OntologyTerm("PR:000000001"),
            KeyPrefix(('PHAROS:',)),
            NodeLabel("Protein"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the protein for ligand binding, interactions and disease "
                "associations.",
                limitations=(
                    Limitation(
                        "Isoforms and modified forms are not separate nodes."
                    ),
                    Limitation(
                        "A missing association is not evidence that the protein is "
                        "unrelated to the disease."
                    ),
                ),
            ),
            claims=(
                Claim("A protein is identified by its UniProt accession."),
                Claim(
                    "The TDL is the Pharos development level, not a measure of "
                    "evidence quality."
                ),
            ),
        ),
    )

    target_key: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The stable target identity, PHAROS:<UniProt accession>."),
                Claim("Use for graph identity."),
            ),
        ),
    )
    symbol: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The preferred gene symbol for the protein."),
                Claim("Use for display and search."),
            ),
        ),
    )
    uniprot: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The UniProt accession."),
                Claim("Use for cross-reference."),
            ),
        ),
    )
    name: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The protein name reported by Pharos."),
                Claim("Use for display."),
            ),
        ),
    )
    description: PropertySlot[str | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The release's protein description."),
                Claim("Use as context, never as evidence for an edge."),
                Claim("The description may be absent."),
            ),
        ),
    )
    tdl: PropertySlot[str] = property(
        meaning=Meaning(
            purpose=Purpose(
                "Stratify a kinase by its Pharos Target Development Level.",
                limitations=(
                    Limitation(
                        "The level is a release classification, not a probability or "
                        "a measure of evidence quality."
                    ),
                    Limitation(
                        "The level changes between releases and is not comparable "
                        "across releases."
                    ),
                ),
            ),
            claims=(
                Claim(
                    "The Pharos Target Development Level: Tclin, Tchem, Tbio or "
                    "Tdark."
                ),
                Claim("Use to stratify targets, not to infer causality."),
                Claim("TDL changes between releases and is not a probability."),
            ),
        ),
    )
    family: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The IDG protein family."),
                Claim("Use to scope the kinase slice."),
            ),
        ),
    )
    novelty: PropertySlot[float | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The release's novelty score."),
                Claim("Use as a release-specific ranking feature."),
                Claim("The score is not comparable across releases."),
            ),
        ),
    )
