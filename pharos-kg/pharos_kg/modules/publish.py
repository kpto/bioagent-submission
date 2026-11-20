"""Publish the annotated view of every component, before any rule runs.

One step per graph component. It reads the component's records and publishes
them unchanged under the ``annotated`` opening. The annotation fields are part
of the graph schema and every binding seeds them with ``keep`` and three empty
mark arrays, so this step adds no column and decides nothing: its responsibility
is to make the pre-projection view addressable.

The annotated view is the primary artifact of pruning: the annotator steps fill
its marks, and the pruned graph is the projection of the records whose verdict
is still keep.
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

COMPONENT = "publish_annotated_records"
PUBLISH = InstructionKind("publish_view", "duckdb")
ANNOTATED = "annotated"


def _components(model: Any) -> list[tuple[Literal["node", "edge"], Any]]:
    found: list[tuple[Literal["node", "edge"], Any]] = []
    for component in model.graph.nodes:
        if not component.abstract:
            found.append(("node", component))
    for component in model.graph.edges:
        if not component.abstract:
            found.append(("edge", component))
    return found


class PublishPlanner:
    """Plan one publish step per graph component."""

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
                name=f"publish.{component.name}",
                inputs=(Input(ArtifactPattern(records.key), None, "records"),),
                outputs=(Output(records, opening_name=Key((ANNOTATED,))),),
                instruction=Instruction(
                    PUBLISH, {"relation": f"publish_{component.name}"},
                ),
            ))
        return tuple(steps)


class PublishExecutor:
    """Copy each component's records into the annotated opening."""

    kinds: tuple[InstructionKind, ...] = (PUBLISH,)
    resources = (DuckDbService,)

    def execute(
        self,
        context: ExecutionContext | DisruptedExecutionContext,
        instruction: Instruction,
    ) -> Any:
        if isinstance(context, DisruptedExecutionContext):
            return skipped(context)
        service = context.resources.get(DuckDbService)
        name = str(instruction_payload(instruction)["relation"])
        relation = None
        for contributions in context.inputs.values():
            for item in contributions:
                if item.artifact is not None:
                    relation = item.artifact.value
        source = service.relations.reference(relation)
        view = service.relations.materialize(name, f"SELECT * FROM {source}")
        return succeeded(context, view)


__all__ = ["ANNOTATED", "PUBLISH", "PublishExecutor", "PublishPlanner", "COMPONENT"]
