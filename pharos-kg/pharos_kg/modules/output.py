"""Write graph records to a JSON Lines file, with or without the annotations.

One step per configured output. It reads the graph-record artifacts it declares,
stamps each record with its kind and component the way the framework's file
target does, and writes one JSON Lines file. The configuration decides one
thing: whether the declared annotation fields are written. The annotated view
keeps them; the shipped graph omits them, so a reader of ``graph.jsonl`` sees
facts and no editorial field.

This module exists because the shipped graph and the annotated graph are two
presentations of one schema. The projection keeps the schema intact so every
downstream consumer can read it; the file target that publishes the facts is the
place that leaves the annotation out.
"""

from __future__ import annotations

import datetime
import json
import uuid
from dataclasses import dataclass
from typing import Any

from kg_build_system.distribution.model.public.artifacts import (
    graph_record_artifact,
)
from kg_build_system.distribution.modules.runtime import (
    OutputStorage,
    instruction_payload,
    skipped,
    succeeded,
)
from kg_build_system.distribution.service.internal.execution import (
    artifact_of,
    input_values,
    output_path,
    query,
    reference,
)
from kg_build_system.distribution.service.internal.relations import RelationService
from kg_build_system.kernel import (
    ArtifactPattern,
    ArtifactType,
    DisruptedExecutionContext,
    ExecutionContext,
    Input,
    Instruction,
    InstructionKind,
    Key,
    Publication,
    Step,
)

from pharos_kg.modules.rules import ANNOTATION_COLUMNS

OUTPUT = InstructionKind("graph_output", "pharos")
RECORDS_INPUT = "records"


@dataclass(frozen=True, slots=True)
class GraphOutputConfiguration:
    """One JSON Lines output: where it goes and whether it carries annotations."""

    relative_path: str
    component: str
    name: str
    annotations: bool


def _record_order(contribution: Any) -> tuple[str, str]:
    """The canonical order of one component's records in the file.

    Sort by kind, then component, then ``build_key`` within each component, so
    two runs of one revision write the same bytes whatever order the engine
    happened to aggregate in. The order is stated here, in the step that
    writes the file, rather than repaired afterwards.
    """
    artifact = artifact_of(contribution)
    if artifact is None:
        return ("", "")
    identity = graph_record_artifact(artifact.type)
    if identity is None:
        return ("", "")
    return (identity.kind, identity.component)


def _canonical(value: Any) -> Any:
    """The canonical form of one property value as it reaches the file."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time, uuid.UUID)):
        return str(value)
    if isinstance(value, dict):
        return {key: _canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    raise TypeError(
        f"graph property of type {type(value).__qualname__} has no canonical"
        " form in the file target"
    )


class GraphOutputPlanner:
    """Plan the one deferred step that writes one configured output."""

    version = "1"
    runtime_fields: tuple[Any, ...] = ()

    def __init__(self, configuration: GraphOutputConfiguration) -> None:
        self.configuration = configuration
        self.component_id = configuration.component

    def plan(self, model: Any, context: Any) -> tuple[Step, ...]:
        del model, context
        return (
            Step(
                component=self.component_id,
                name=f"write.{self.configuration.name}",
                inputs=(
                    Input(
                        ArtifactPattern.of("core", "graph", "**"),
                        None,
                        RECORDS_INPUT,
                    ),
                ),
                outputs=(
                    Publication(
                        ArtifactType.of(self.component_id, "write_result"),
                        Key(("result",)),
                    ),
                ),
                instruction=Instruction(OUTPUT, {
                    "relative_path": self.configuration.relative_path,
                    "annotations": self.configuration.annotations,
                }),
                assembly_preference="deferred",
            ),
        )


class GraphOutputExecutor:
    """Write every graph-record relation the step receives, in one pass."""

    kinds: tuple[InstructionKind, ...] = (OUTPUT,)
    resources = (RelationService, OutputStorage)

    def execute(
        self,
        context: ExecutionContext | DisruptedExecutionContext,
        instruction: Instruction,
    ) -> Any:
        if isinstance(context, DisruptedExecutionContext):
            return skipped(context)
        payload = instruction_payload(instruction)
        relative_path = payload.get("relative_path")
        if not isinstance(relative_path, str):
            raise RuntimeError("graph output requires a relative path")
        annotations = bool(payload.get("annotations", True))
        resources = context.resources
        path = output_path(resources, relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        omitted = () if annotations else ANNOTATION_COLUMNS
        node_count = 0
        edge_count = 0
        ordered = sorted(
            input_values(context, RECORDS_INPUT), key=_record_order,
        )
        with path.open("w", encoding="utf-8") as stream:
            for contribution in ordered:
                artifact = artifact_of(contribution)
                if artifact is None:
                    continue
                identity = graph_record_artifact(artifact.type)
                if identity is None:
                    continue
                kind, component = identity.kind, identity.component
                relation = reference(resources, artifact.value)
                result = query(
                    resources, f"SELECT * FROM {relation} ORDER BY build_key",
                )
                columns = tuple(column[0] for column in result.description)
                while batch := result.fetchmany(1_000):
                    for row in batch:
                        record = dict(zip(columns, row, strict=True))
                        for name in omitted:
                            record.pop(name, None)
                        record.update(
                            build_key=str(_canonical(record["build_key"])),
                            type=component,
                            kind=kind,
                        )
                        if kind == "node":
                            node_count += 1
                        else:
                            edge_count += 1
                        stream.write(
                            json.dumps(
                                record, sort_keys=True, default=_canonical,
                            ) + "\n",
                        )
        return succeeded(context, {
            "nodes": node_count,
            "edges": edge_count,
            "location": str(path),
        })


__all__ = [
    "GraphOutputConfiguration",
    "GraphOutputExecutor",
    "GraphOutputPlanner",
    "OUTPUT",
]
