"""A disease or phenotype term."""

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


class DiseaseNode(AnnotatedNode, Node):

    options = NodeOptions(
        name="disease",
        annotations=(
            BiolinkClass("biolink:Disease"),
            OntologyTerm("MONDO:0000001"),
            KeyPrefix(('MONDO:', 'DOID:', 'UMLS:', 'MESH:', 'OMIM:', 'MIM:', 'NAME:',)),
            NodeLabel("Disease"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read the disease when the question is about a condition rather than "
                "a target.",
                limitations=(
                    Limitation(
                        "The extract does not carry the ontology hierarchy or "
                        "synonyms."
                    ),
                    Limitation(
                        "A name-derived key is a last resort and is less stable than "
                        "a CURIE."
                    ),
                ),
            ),
            claims=(
                Claim(
                    "A disease is identified by an ontology accession, preferably "
                    "MONDO."
                ),
                Claim("The name is a label for the term, not the term's definition."),
            ),
        ),
    )

    disease_key: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim(
                    "The stable disease identity, preferably a MONDO or DOID CURIE."
                ),
                Claim("Use for graph identity."),
                Claim(
                    "A NAME: key is stable only while the release name is stable."
                ),
            ),
        ),
    )
    name: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The release's disease label."),
                Claim("Use for display and search."),
            ),
        ),
    )
    mondo_id: PropertySlot[str | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The MONDO accession when the release provides one."),
                Claim("Use for standards alignment."),
            ),
        ),
    )
    doid: PropertySlot[str | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The DOID accession when the release provides one."),
                Claim("Use for cross-reference."),
            ),
        ),
    )
