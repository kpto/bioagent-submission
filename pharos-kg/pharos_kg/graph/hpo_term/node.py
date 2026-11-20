"""A phenotype term from the Human Phenotype Ontology."""

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


class HpoTermNode(AnnotatedNode, Node):

    options = NodeOptions(
        name="hpo_term",
        annotations=(
            BiolinkClass("biolink:PhenotypicFeature"),
            OntologyTerm("HP:0000118"),
            KeyPrefix(("HP:",)),
            NodeLabel("HPO term"),
        ),
        meaning=Meaning(
            purpose=Purpose(
                "Read a phenotype term when the question is what a disease looks like "
                "in a patient, including diseases no target in the graph reaches.",
                limitations=(
                    Limitation(
                        "The node carries the term and its label, not the ontology's "
                        "hierarchy or synonyms."
                    ),
                    Limitation(
                        "A phenotype is an observation recorded in a cohort; it is not "
                        "a mechanism and not a diagnosis."
                    ),
                ),
            ),
            claims=(
                Claim("A phenotype term is identified by its HPO accession."),
                Claim("The label is the ontology's term name."),
            ),
        ),
    )

    hpo_id: PropertySlot[str] = property(
        meaning=Meaning(
            claims=(
                Claim("The HPO accession, such as HP:0001250."),
                Claim("Use for graph identity."),
            ),
        ),
    )
    name: PropertySlot[str | None] = property(
        meaning=Meaning(
            claims=(
                Claim("The ontology's label for the term."),
                Claim("Use for display and search."),
            ),
        ),
    )
