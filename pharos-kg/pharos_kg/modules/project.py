"""Project the keeps from the annotated graph.

One step per graph component. It reads the component's annotated records and
keeps the rows whose verdict is still ``keep``. It applies no rule and changes
no column: pruning is already decided by the marks. Which fields reach the
shipped file is the output module's decision, so the projection stays a view of
the same schema that every other consumer reads.

The step also publishes its counts, so a later step can reconcile the two
outputs instead of trusting that they agree.
"""

from __future__ import annotations

from typing import Any, Literal, cast

from kg_build_system.distribution.model.public.artifacts import CoreArtifactTypes
from kg_build_system.distribution.modules.duckdb import DuckDbService
from kg_build_system.distribution.modules.runtime import (
    instruction_payload,
    skipped,
    succeeded,
)
from kg_build_system.kernel import (
    Artifact,
    ArtifactPattern,
    ArtifactType,
    DisruptedExecutionContext,
    ExecutionContext,
    Input,
    Instruction,
    InstructionKind,
    Key,
    Output,
    Step,
    StepOutcome,
)

from pharos_kg.modules.rules import KEEP, VERDICT_COLUMN

COMPONENT = "project_kept_records"
PROJECT = InstructionKind("project_view", "duckdb")
PROJECTED = "projected"
SUMMARY = "summary"


def _components(model: Any) -> list[tuple[Literal["node", "edge"], Any]]:
    found: list[tuple[Literal["node", "edge"], Any]] = []
    for component in model.graph.nodes:
        if not component.abstract:
            found.append(("node", component))
    for component in model.graph.edges:
        if not component.abstract:
            found.append(("edge", component))
    return found


class ProjectPlanner:
    """Plan one projection step per graph component."""

    component_id = COMPONENT
    version = "1"
    runtime_fields: tuple[Any, ...] = ()

    def plan(self, model: Any, context: Any) -> tuple[Step, ...]:
        del context
        steps = []
        for kind, component in _components(model):
            records = CoreArtifactTypes.graph_records(kind, component.name)
            steps.append(Step(
                component=self.component_id,
                name=component.name,
                inputs=(Input(ArtifactPattern(records.key), None, "records"),),
                outputs=(
                    Output(records, opening_name=Key((PROJECTED,))),
                    Output(
                        ArtifactType.of(self.component_id, SUMMARY, component.name),
                        opening_name=Key((SUMMARY,)),
                    ),
                ),
                instruction=Instruction(PROJECT, {
                    "relation": f"project_{component.name}",
                    "kind": kind,
                }),
            ))
        return tuple(steps)


class ProjectExecutor:
    """Keep the records whose verdict is keep and publish the counts."""

    kinds: tuple[InstructionKind, ...] = (PROJECT,)
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
        name = str(payload["relation"])
        kind = str(payload["kind"])
        relation = None
        for contributions in context.inputs.values():
            for item in contributions:
                if item.artifact is not None:
                    relation = item.artifact.value
        source = service.relations.reference(relation)
        row = service.relations.query(
            f"SELECT count(*), count(*) FILTER (WHERE {VERDICT_COLUMN} <> '{KEEP}')"
            f" FROM {source}"
        ).fetchone()
        total = int(cast(int, row[0])) if row else 0
        pruned = int(cast(int, row[1])) if row else 0
        view = service.relations.materialize(
            name,
            f"SELECT * FROM {source} WHERE {VERDICT_COLUMN} = '{KEEP}'",
        )
        outcome = succeeded(context, view)
        summary_output = context.step.outputs[1]
        opening = summary_output.opening_name
        if opening is None:
            raise RuntimeError("projection summary output has no opening name")
        summary = Artifact(
            opening,
            summary_output.type,
            {
                "kind": kind,
                "input": total,
                "kept": total - pruned,
                "pruned": pruned,
            },
        )
        return StepOutcome(
            step_id=outcome.step_id,
            status=outcome.status,
            artifacts=(*outcome.artifacts, summary),
        )


__all__ = ["PROJECT", "PROJECTED", "ProjectExecutor", "ProjectPlanner", "SUMMARY", "COMPONENT"]
