"""Reconcile the annotated graph, the projection and the shipped graph.

One step. It reads the counts the writers published and the counts the
projection published, and fails the build when the two outputs disagree:
the shipped graph must be exactly the annotation minus the pruned records.
It decides nothing and writes nothing; its only output is its verdict on the
pair.
"""

from __future__ import annotations

from typing import Any, cast

from kg_build_system.distribution.model.public.artifacts import CoreArtifactTypes
from kg_build_system.distribution.modules.runtime import skipped, succeeded
from kg_build_system.kernel import (
    ArtifactPattern,
    ArtifactType,
    DisruptedExecutionContext,
    ExecutionContext,
    Failure,
    Input,
    Instruction,
    InstructionKind,
    Key,
    Publication,
    Step,
    StepOutcome,
    StepStatus,
)

from pharos_kg.modules.project import COMPONENT as PROJECT_COMPONENT, SUMMARY

COMPONENT = "reconcile_outputs"
RECONCILE = InstructionKind("reconcile_outputs", "pharos")
REPORT = "reconciliation"
ANNOTATED_WRITER = "write_annotated_graph"
GRAPH_WRITER = "write_facts_graph"


def _counts(context: ExecutionContext, name: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for contributions in context.inputs.get(name, ()):
        if contributions.artifact is None:
            continue
        value = contributions.artifact.value
        if isinstance(value, dict):
            found.append(value)
    return found


class ReconcilePlanner:
    """Plan the one reconciliation step, after both writers."""

    component_id = COMPONENT
    version = "1"
    runtime_fields: tuple[Any, ...] = ()

    def plan(self, model: Any, context: Any) -> tuple[Step, ...]:
        del model, context
        return (
            Step(
                component=self.component_id,
                name="reconcile",
                inputs=(
                    Input(
                        ArtifactPattern.of(PROJECT_COMPONENT, SUMMARY, "**"),
                        None,
                        "projection",
                    ),
                    Input(
                        ArtifactPattern(
                            ArtifactType.of(ANNOTATED_WRITER, "write_result").key,
                        ),
                        None,
                        "annotated",
                    ),
                    Input(
                        ArtifactPattern(
                            ArtifactType.of(GRAPH_WRITER, "write_result").key,
                        ),
                        None,
                        "graph",
                    ),
                ),
                outputs=(
                    Publication(
                        ArtifactType.of(self.component_id, REPORT),
                        Key(("report",)),
                    ),
                ),
                instruction=Instruction(RECONCILE, {}),
            ),
        )


class ReconcileExecutor:
    """Fail the build when the shipped graph is not the projection."""

    kinds: tuple[InstructionKind, ...] = (RECONCILE,)
    resources: tuple[Any, ...] = ()

    def execute(
        self,
        context: ExecutionContext | DisruptedExecutionContext,
        instruction: Instruction,
    ) -> Any:
        del instruction
        if isinstance(context, DisruptedExecutionContext):
            return skipped(context)
        projections = _counts(cast(ExecutionContext, context), "projection")
        annotated = _counts(cast(ExecutionContext, context), "annotated")
        graph = _counts(cast(ExecutionContext, context), "graph")
        if not projections or not annotated or not graph:
            return self._fail(
                context, "reconciliation is missing a writer or a projection count",
            )
        totals: dict[str, dict[str, int]] = {}
        for item in projections:
            kind = str(item.get("kind") or "")
            bucket = totals.setdefault(
                kind, {"input": 0, "kept": 0, "pruned": 0},
            )
            for field in bucket:
                bucket[field] += int(item.get(field, 0))
        for kind, bucket in totals.items():
            if bucket["kept"] + bucket["pruned"] != bucket["input"]:
                return self._fail(
                    context,
                    f"{kind} projection accounts for "
                    f"{bucket['kept'] + bucket['pruned']} of {bucket['input']} "
                    "records",
                )
        for kind, written in (("edge", "edges"), ("node", "nodes")):
            bucket = totals.get(kind)
            if bucket is None:
                continue
            annotated_count = int(annotated[0].get(written, 0))
            graph_count = int(graph[0].get(written, 0))
            ungoverned = annotated_count - bucket["input"]
            if graph_count != bucket["kept"] + ungoverned:
                return self._fail(
                    context,
                    f"the pruned graph holds {graph_count} {written} but the "
                    f"projection kept {bucket['kept']} of {bucket['input']} "
                    f"governed {written} beside {ungoverned} no rule governs",
                )
            if annotated_count - graph_count != bucket["pruned"]:
                return self._fail(
                    context,
                    f"the annotated graph holds {annotated_count} {written} and "
                    f"the pruned graph {graph_count}, but {bucket['pruned']} were "
                    "marked",
                )
        return succeeded(context, {
            "annotated": {
                "nodes": int(annotated[0].get("nodes", 0)),
                "edges": int(annotated[0].get("edges", 0)),
            },
            "pruned": {kind: bucket["pruned"] for kind, bucket in totals.items()},
            "shipped": {
                "nodes": int(graph[0].get("nodes", 0)),
                "edges": int(graph[0].get("edges", 0)),
            },
        })

    def _fail(self, context: ExecutionContext, message: str) -> StepOutcome:
        return StepOutcome(
            step_id=context.step_id,
            status=StepStatus.FAILED,
            failure=Failure(message=message, step_id=context.step_id),
        )


__all__ = ["RECONCILE", "ReconcileExecutor", "ReconcilePlanner", "COMPONENT"]
