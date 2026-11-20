"""Guard the graph at plan time and at the record boundary.

Two contributions, both before publication:

``DesignGuardPlanner`` reads the declarations and refuses to plan a blueprint in
which a record kind declares no identity namespace, an edge names an undeclared
endpoint kind, or a record has no binding. Nothing executes.

``RecordGuardPlanner`` follows the deduplication pattern: one post-processing
step per bound component. The step checks that component's records against the
design before the file target can consume them. A component whose keys fall
outside its declared namespaces, whose identity is null, or whose keys collide
fails the step, so the file write is disrupted and the graph is never published.
"""

from __future__ import annotations

from typing import Any, cast

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
    Failure,
    Input,
    Instruction,
    InstructionKind,
    Key,
    Output,
    Step,
    StepOutcome,
    StepStatus,
)

RECORD_GUARD = InstructionKind("post_process", "record_guard")


class DesignViolation(ValueError):
    """A blueprint or a record that contradicts the design contract."""


def _annotation(declaration: Any, namespace: str, identifier: str) -> Any | None:
    for annotation in declaration.annotations:
        if annotation.namespace == namespace and annotation.id == identifier:
            return annotation
    return None


def _node_name(reference: Any) -> str:
    segments = getattr(getattr(reference, "key", None), "segments", ())
    if not segments:
        raise DesignViolation(f"edge endpoint {reference!r} names no node")
    return str(segments[-1])


def _prefixes(declaration: Any) -> tuple[str, ...]:
    annotation = _annotation(declaration, "pharos", "key_prefix")
    return () if annotation is None else tuple(annotation.arguments.get("values") or ())


def is_edge(component: Any) -> bool:
    return hasattr(component, "source") and hasattr(component, "target")


def design_problems(blueprint: Any) -> list[str]:
    """Every declaration-level reason the blueprint cannot be built."""
    problems: list[str] = []
    # An abstract category carries shared properties and may be an endpoint; it
    # produces no record, so it needs no identity prefix, Biolink annotation or
    # binding of its own.
    declared_nodes = {node.name: node for node in blueprint.graph.nodes}
    nodes = {
        name: node for name, node in declared_nodes.items()
        if not getattr(node, "abstract", False)
    }
    edges = {
        edge.name: edge for edge in blueprint.graph.edges
        if not getattr(edge, "abstract", False)
    }

    for name, node in nodes.items():
        if not _prefixes(node):
            problems.append(f"node {name!r} declares no identity prefix")
        if _annotation(node, "biolink", "class") is None:
            problems.append(f"node {name!r} declares no Biolink class")

    for name, edge in edges.items():
        if _annotation(edge, "biolink", "predicate") is None:
            problems.append(f"edge {name!r} declares no Biolink predicate")
        for side in ("source", "target"):
            endpoint = _node_name(getattr(edge, side))
            if endpoint not in declared_nodes:
                problems.append(
                    f"edge {name!r} {side} names undeclared node {endpoint!r}"
                )

    bound = [str(binding.name) for binding in blueprint.bindings]
    duplicates = sorted({name for name in bound if bound.count(name) > 1})
    if duplicates:
        problems.append(f"duplicate binding names: {', '.join(duplicates)}")
    declared = set(nodes) | set(edges)
    for name in sorted(declared):
        if name not in bound:
            problems.append(f"{name!r} has no binding")
    for name in sorted(set(bound) - declared):
        problems.append(f"binding {name!r} targets no declared record")

    return problems


def identity_predicate(kind: str, prefixes: tuple[str, ...]) -> str:
    """The SQL predicate a component's records must not satisfy."""
    if kind == "node":
        allowed = " OR ".join(
            f"build_key LIKE '{prefix.replace(chr(39), chr(39) * 2)}%'"
            for prefix in prefixes
        )
        return f"build_key IS NULL OR NOT ({allowed})"
    return (
        "build_key IS NULL OR source_build_key IS NULL OR "
        "target_build_key IS NULL"
    )


class DesignGuardPlanner:
    """Fail planning when the declarations contradict the design contract."""

    component_id = "pharos_design"
    version = "1"
    runtime_fields: tuple[Any, ...] = ()

    def plan(self, blueprint: Any, context: Any) -> tuple[Step, ...]:
        del context
        problems = design_problems(blueprint)
        if problems:
            raise DesignViolation(
                "the blueprint contradicts its design: " + "; ".join(problems)
            )
        return ()


class RecordGuardPlanner:
    """Plan one post-processing guard step per bound graph-record component."""

    component_id = "pharos_records"
    version = "1"
    runtime_fields: tuple[Any, ...] = ()

    def plan(self, blueprint: Any, context: Any) -> tuple[Step, ...]:
        del context
        bound = {binding.component for binding in blueprint.bindings}
        steps: list[Step] = []
        for component in (*blueprint.graph.nodes, *blueprint.graph.edges):
            if component.name not in bound:
                continue
            kind = "edge" if is_edge(component) else "node"
            records_type = CoreArtifactTypes.graph_records(kind, component.name)
            steps.append(
                Step(
                    component=self.component_id,
                    name=component.name,
                    inputs=(
                        Input(
                            type=ArtifactPattern(records_type.key),
                            opening_name=None,
                            declared_name="records",
                        ),
                    ),
                    outputs=(
                        Output(records_type, opening_name=Key(("validated",))),
                    ),
                    instruction=Instruction(
                        RECORD_GUARD,
                        {
                            "name": component.name,
                            "kind": kind,
                            "prefixes": list(_prefixes(component)),
                        },
                    ),
                )
            )
        return tuple(steps)


def _first_relation(context: ExecutionContext) -> Any | None:
    for contributions in context.inputs.values():
        for item in contributions:
            if item.artifact is not None:
                return item.artifact.value
    return None


class RecordGuardExecutor:
    """Check one component's records against the design before they are written."""

    kinds: tuple[InstructionKind, ...] = (RECORD_GUARD,)
    resources = (DuckDbService,)

    def execute(
        self,
        context: ExecutionContext | DisruptedExecutionContext,
        instruction: Instruction,
    ) -> Any:
        if isinstance(context, DisruptedExecutionContext):
            return skipped(context)
        payload = instruction_payload(instruction)
        name = str(payload.get("name") or "")
        kind = str(payload.get("kind") or "")
        raw_prefixes = payload.get("prefixes")
        prefixes = (
            tuple(str(value) for value in raw_prefixes)
            if isinstance(raw_prefixes, list)
            else ()
        )
        relation = _first_relation(context)
        if relation is None:
            return succeeded(context, None)

        relations = context.resources.get(DuckDbService).relations
        source = relations.reference(relation)
        predicate = identity_predicate(kind, prefixes)
        invalid_row = relations.query(
            f"SELECT count(*) FROM {source} WHERE {predicate}"
        ).fetchone()
        duplicate_row = relations.query(
            f"SELECT count(*) FROM (SELECT build_key FROM {source} "
            "GROUP BY 1 HAVING count(*) > 1)"
        ).fetchone()
        invalid = int(cast(int, invalid_row[0])) if invalid_row else 0
        duplicates = (
            int(cast(int, duplicate_row[0])) if duplicate_row else 0
        )
        if invalid or duplicates:
            return StepOutcome(
                step_id=context.step_id,
                status=StepStatus.FAILED,
                failure=Failure(
                    message=(
                        f"{name}: {int(invalid)} record(s) outside the declared "
                        f"design and {int(duplicates)} duplicate key group(s)"
                    ),
                    step_id=context.step_id,
                ),
            )
        return succeeded(context, relation)


__all__ = [
    "DesignGuardPlanner",
    "DesignViolation",
    "RECORD_GUARD",
    "RecordGuardExecutor",
    "RecordGuardPlanner",
    "design_problems",
    "identity_predicate",
    "is_edge",
]
