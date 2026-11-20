"""Add one rule's mark to the records of the components it governs.

One step per (rule, component). A step reads the component's current annotated
records, appends this rule's mark where its predicate holds, and sets the
verdict to prune for those rows. It never removes a record and never reads
another rule's output, so the steps are monotone and order-independent; the
chain of steps is the annotated graph.

The annotation fields are declared on every node and edge; this step fills them.
The decision itself lives in the rule module: ``NAME``, ``APPLIES_TO``,
``PREDICATE``, ``CONFIDENCE`` and ``REASON`` are read, not reimplemented.
"""

from __future__ import annotations

from typing import Any, Literal

from kg_build_system.distribution.model.public.artifacts import CoreArtifactTypes
from kg_build_system.distribution.modules.duckdb import DuckDbService
from kg_build_system.distribution.modules.runtime import (
    instruction_payload,
    skipped,
    succeeded,
)
from kg_build_system.kernel import (
    ArtifactPattern,
    DisruptedExecutionContext,
    ExecutionContext,
    Input,
    Instruction,
    InstructionKind,
    Key,
    Output,
    Step,
)

from pharos_kg.modules.rules import (
    ANNOTATION_COLUMNS,
    CONFIDENCE_COLUMN,
    PRUNE,
    REASON_COLUMN,
    RULE_COLUMN,
    RULES,
    VERDICT_COLUMN,
)

COMPONENT = "annotate_rule_matches"
ANNOTATE = InstructionKind("annotate_rule", "duckdb")


def _components(model: Any) -> list[tuple[Literal["node", "edge"], Any]]:
    found: list[tuple[Literal["node", "edge"], Any]] = []
    for component in model.graph.nodes:
        if not component.abstract:
            found.append(("node", component))
    for component in model.graph.edges:
        if not component.abstract:
            found.append(("edge", component))
    return found


def _quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


class AnnotatePlanner:
    """Plan one annotator step per rule and component it applies to."""

    component_id = COMPONENT
    version = "1"
    runtime_fields: tuple[Any, ...] = ()

    def plan(self, model: Any, context: Any) -> tuple[Step, ...]:
        del context
        steps = []
        for rule in RULES:
            for kind, component in _components(model):
                if component.name not in rule.APPLIES_TO:
                    continue
                records = CoreArtifactTypes.graph_records(kind, component.name)
                steps.append(Step(
                    component=self.component_id,
                    name=f"{component.name}.{rule.NAME}",
                    inputs=(Input(ArtifactPattern(records.key), None, "records"),),
                    outputs=(Output(
                        records,
                        opening_name=Key((f"annotated.{rule.NAME}",)),
                    ),),
                    instruction=Instruction(ANNOTATE, {
                        "relation": f"annotate_{component.name}_{rule.NAME}",
                        "rule": rule.NAME,
                        "predicate": rule.PREDICATE,
                        "confidence": rule.CONFIDENCE,
                        "reason": rule.REASON,
                    }),
                ))
        return tuple(steps)


class AnnotateExecutor:
    """Append this rule's mark to every record its predicate selects."""

    kinds: tuple[InstructionKind, ...] = (ANNOTATE,)
    resources = (DuckDbService,)

    def execute(
        self,
        context: ExecutionContext | DisruptedExecutionContext,
        instruction: Instruction,
    ) -> Any:
        if isinstance(context, DisruptedExecutionContext):
            return skipped(context)
        service = context.resources.get(DuckDbService)
        payload = instruction_payload(instruction)
        relation = None
        for contributions in context.inputs.values():
            for item in contributions:
                if item.artifact is not None:
                    relation = item.artifact.value
        source = service.relations.reference(relation)
        confidence = payload.get("confidence")
        if not isinstance(confidence, (int, float)):
            raise TypeError("an annotator rule states a numeric confidence")
        predicate = str(payload["predicate"])
        excluded = ", ".join(ANNOTATION_COLUMNS)
        view = service.relations.materialize(
            str(payload["relation"]),
            f"SELECT * EXCLUDE ({excluded}),"
            f" CASE WHEN ({predicate}) THEN '{PRUNE}'"
            f" ELSE {VERDICT_COLUMN} END AS {VERDICT_COLUMN},"
            f" CASE WHEN ({predicate})"
            f" THEN list_append({RULE_COLUMN}, {_quote(str(payload['rule']))})"
            f" ELSE {RULE_COLUMN} END AS {RULE_COLUMN},"
            f" CASE WHEN ({predicate})"
            f" THEN list_append({CONFIDENCE_COLUMN}, {float(confidence)})"
            f" ELSE {CONFIDENCE_COLUMN} END AS {CONFIDENCE_COLUMN},"
            f" CASE WHEN ({predicate})"
            f" THEN list_append({REASON_COLUMN}, {_quote(str(payload['reason']))})"
            f" ELSE {REASON_COLUMN} END AS {REASON_COLUMN}"
            f" FROM {source}",
        )
        return succeeded(context, view)


__all__ = ["ANNOTATE", "AnnotateExecutor", "AnnotatePlanner", "COMPONENT"]
