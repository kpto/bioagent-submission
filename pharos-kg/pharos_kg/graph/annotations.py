"""Biolink and ontology annotations carried by the Pharos declarations."""

from dataclasses import dataclass

from kg_build_system import Annotation


@dataclass(frozen=True)
class BiolinkClass(Annotation):
    namespace = "biolink"
    annotation_id = "class"

    value: str


@dataclass(frozen=True)
class BiolinkPredicate(Annotation):
    namespace = "biolink"
    annotation_id = "predicate"

    value: str


@dataclass(frozen=True)
class OntologyTerm(Annotation):
    namespace = "obo"
    annotation_id = "term"

    value: str


@dataclass(frozen=True)
class KeyPrefix(Annotation):
    """The identity namespaces a record's key may use.

    A node type declares every prefix its build keys can start with. The design
    guard refuses to compile a node without one, and the binding is the only
    place that constructs a key, so a record cannot reach the graph under a
    namespace the design did not state.
    """

    namespace = "pharos"
    annotation_id = "key_prefix"

    values: tuple[str, ...]
