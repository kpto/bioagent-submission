"""The annotation fields every node and edge carries before projection.

Pruning states a decision on a record rather than removing it: the annotated
graph is the primary artifact, and the shipped graph is its projection. These
fields are part of the graph schema, so a reader of the declaration knows what a
verdict means and where it lives; the annotator steps fill them and the
projection removes them.

The fields are parallel arrays: index ``i`` of ``annotation_rule``,
``annotation_confidence`` and ``annotation_reason`` describes the same mark. A
record with no mark has three empty arrays and the verdict ``keep``.
"""

from __future__ import annotations

from typing import Any

from kg_build_system import (
    FLOAT,
    STR,
    AbstractEdge,
    AbstractNode,
    Array,
    Claim,
    EdgeOptions,
    Meaning,
    NodeOptions,
    PropertySlot,
    Purpose,
    property,
)
from kg_build_system.distribution.languages.expressions.service.public import (
    value_expression,
)
from kg_build_system.kernel.model.public.types import ArrayType

_VERDICT = Meaning(
    claims=(
        Claim(
            "keep means no annotator rule selected the record; prune means at "
            "least one did."
        ),
        Claim("Absent on the base record, which no annotator has seen yet."),
        Claim(
            "The field is present on graph.annotated.jsonl; graph.jsonl is the "
            "projection of the keep records and carries no annotation field."
        ),
        Claim("The field states this project's decision, not a fact of the release."),
    ),
)
_RULE = Meaning(
    claims=(
        Claim("The name of each annotator module that selected the record."),
        Claim(
            "Index i corresponds to the same mark in annotation_confidence and "
            "annotation_reason."
        ),
        Claim("An empty array means no rule selected the record."),
        Claim(
            "The module, not the record, states the rule's predicate and its "
            "boundary."
        ),
    ),
)
_CONFIDENCE = Meaning(
    claims=(
        Claim("The confidence the annotator module assigns to its own decision."),
        Claim(
            "The value is a rule-specific weight, not a probability that the edge "
            "is false."
        ),
        Claim("Index i corresponds to the same mark in annotation_rule."),
    ),
)
_REASON = Meaning(
    claims=(
        Claim("The one-sentence reason the annotator module states."),
        Claim("The reason names the evidence that triggered the rule, when it has one."),
        Claim("Index i corresponds to the same mark in annotation_rule."),
    ),
)


class AnnotatedNode(AbstractNode):
    """The annotation fields of every node, declared once as a category."""

    options = NodeOptions(
        name="annotated_record_node",
        meaning=Meaning(
            purpose=Purpose(
                "Carry the annotation fields every node shares, so a pruning "
                "decision is declared on the node rather than added as an "
                "undeclared column."
            ),
            claims=(
                Claim("The category produces no record of its own."),
                Claim("Every concrete node inherits its four annotation fields."),
            ),
        ),
    )

    verdict: PropertySlot[str | None] = property(meaning=_VERDICT)
    annotation_rule: PropertySlot[Array[str] | None] = property(meaning=_RULE)
    annotation_confidence: PropertySlot[Array[float] | None] = property(meaning=_CONFIDENCE)
    annotation_reason: PropertySlot[Array[str] | None] = property(meaning=_REASON)


class AnnotatedEdge(AbstractEdge[AnnotatedNode, AnnotatedNode]):
    """The annotation fields of every edge, declared once as a category."""

    options = EdgeOptions(
        name="annotated_record_edge",
        meaning=Meaning(
            purpose=Purpose(
                "Carry the annotation fields every edge shares, so a pruning "
                "decision is declared on the edge rather than added as an "
                "undeclared column."
            ),
            claims=(
                Claim("The category produces no record of its own."),
                Claim("Every concrete edge inherits its four annotation fields."),
            ),
        ),
    )

    verdict: PropertySlot[str | None] = property(meaning=_VERDICT)
    annotation_rule: PropertySlot[Array[str] | None] = property(meaning=_RULE)
    annotation_confidence: PropertySlot[Array[float] | None] = property(meaning=_CONFIDENCE)
    annotation_reason: PropertySlot[Array[str] | None] = property(meaning=_REASON)


_ARRAY_STR = ArrayType(STR)
_ARRAY_FLOAT = ArrayType(FLOAT)


def unannotated() -> dict[str, Any]:
    """The annotation fields of a record no annotator has judged yet.

    A binding seeds every record with these values, so the annotation is part of
    the graph from its first record rather than a column added later. Bind it as
    ``properties=SomeNode(**unannotated(), ...)``.
    """
    return {
        "verdict": value_expression("keep"),
        "annotation_rule": value_expression([], logical_type=_ARRAY_STR),
        "annotation_confidence": value_expression([], logical_type=_ARRAY_FLOAT),
        "annotation_reason": value_expression([], logical_type=_ARRAY_STR),
    }


__all__ = ["AnnotatedEdge", "AnnotatedNode", "unannotated"]
