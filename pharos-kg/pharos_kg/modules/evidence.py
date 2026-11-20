"""Publish the occurrence-level evidence sidecar beside the facts graph.

The graph records carry identity and declared properties. The sidecar carries,
for every shipped record, the asset tables the binding read and the record's own
locating values, so a reader can reach the source rows through the declared
relation instead of trusting the graph's summary.

The step reads the same projected records the facts output writes. That keeps
one declaration of identity: the key the graph asserts is the key the sidecar
points at, and no join is written twice. The table names come from the asset
declarations and the relation closure of each binding, not from a hand-kept map
of record types.

The sidecar is a publication of the workflow, so ``kbs run`` writes it and the
plan shows it. Its purpose is one reader doing provenance work; it is not a
second graph and it adds no fact the source did not state.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, cast

from kg_build_system.distribution.languages.binding.model.internal import (
    EdgeBindingDTO,
)
from kg_build_system.distribution.languages.data.service.internal import (
    plan_expressions,
    plan_inputs,
    plan_scan_sources,
)
from kg_build_system.distribution.languages.expressions.model.internal import (
    FieldReferenceDTO,
    LookupExpressionDTO,
)
from kg_build_system.distribution.languages.expressions.service.internal import (
    walk_expression_dto,
)
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
from kg_build_system.distribution.service.public import asset_tables
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

COMPONENT = "evidence"
SIDECAR = InstructionKind("evidence_sidecar", "pharos")
RECORDS_INPUT = "records"
RELATIVE_PATH = "evidence.jsonl"
MANIFEST_PATH = "evidence_manifest.json"
EVIDENCE_LIMIT = 20

# Properties that locate the source rows or state what the source reported.
ROW_FIELDS = frozenset({
    "assigners",
    "count",
    "evidence",
    "evidence_class",
    "evidence_types",
    "family",
    "level",
    "max_conf",
    "max_p_activity",
    "max_score",
    "mean_p_activity",
    "min_p_activity",
    "min_p_value",
    "p_int",
    "p_ni",
    "pmids",
    "procedures",
    "references",
    "score",
    "sources",
    "symbol",
    "tdl",
})

EVIDENCE_FIELDS = (
    "evidence",
    "sources",
    "assigners",
    "procedures",
    "evidence_types",
)


def _expression_relations(expressions: Iterable[Any]) -> set[str]:
    """Every relation an expression tree reads."""
    found: set[str] = set()
    for expression in expressions:
        if expression is None:
            continue
        for node in walk_expression_dto(expression):
            if isinstance(node, FieldReferenceDTO):
                found.add(node.field.relation)
            elif isinstance(node, LookupExpressionDTO):
                found.add(node.relation.name)
    return found


def _plan_relations(plan: Any) -> set[str]:
    """Every relation a row plan reads, including its inputs."""
    if plan is None:
        return set()
    found = set(plan_scan_sources(plan))
    found.update(_expression_relations(plan_expressions(plan)))
    for child in plan_inputs(plan):
        found.update(_plan_relations(child))
    return found


def _binding_relations(binding: Any) -> set[str]:
    """Every relation one binding reads through its identity and its rows."""
    expressions: list[Any] = [binding.identity]
    if isinstance(binding, EdgeBindingDTO):
        expressions.extend((binding.source_identity, binding.target_identity))
    expressions.extend(expression for _, expression in binding.properties)
    found = _expression_relations(expressions)
    if binding.rows is not None:
        found.update(_plan_relations(binding.rows))
    return found


def _source_closure(blueprint: Any) -> Any:
    """Resolve a relation name to the source relations it is read from."""
    sources = {relation.name for relation in blueprint.data.source_relations}
    derived = {
        relation.name: relation for relation in blueprint.data.derived_relations
    }
    resolved: dict[str, set[str]] = {}

    def resolve(name: str) -> set[str]:
        if name in sources:
            return {name}
        if name in resolved:
            return resolved[name]
        relation = derived.get(name)
        if relation is None:
            return set()
        found = _expression_relations(
            column.expression for column in relation.columns
        )
        found.update(_plan_relations(relation.row_source))
        closure: set[str] = set()
        for child in found:
            if child != name:
                closure.update(resolve(child))
        resolved[name] = closure
        return closure

    return resolve


def _relation_sources(blueprint: Any) -> dict[str, dict[str, str]]:
    """The declared file and table behind each asset-backed relation."""
    root = Path(__file__).resolve().parents[2]

    def relative(value: str) -> str:
        path = Path(value)
        try:
            return str(path.relative_to(root))
        except ValueError:
            return str(path)

    found: dict[str, dict[str, str]] = {}
    for table in asset_tables(blueprint):
        layout = table.asset.layout
        if layout is None:
            continue
        member = dict(layout.members).get(table.relation_name)
        if not member:
            continue
        if (layout.format or layout.kind) == "mysqldump":
            cache = dict(layout.properties).get("cache")
            if not cache:
                continue
            found[table.relation_name] = {
                "file": relative(f"{cache}/{member}.parquet"),
                "table": member,
            }
        else:
            found[table.relation_name] = {
                "file": relative(f"{layout.locator}/{member}"),
                "table": Path(member).stem,
            }
    return found


def _archive_location(blueprint: Any) -> str:
    """The declared archive, as a project-relative path."""
    root = Path(__file__).resolve().parents[2]
    for table in asset_tables(blueprint):
        layout = table.asset.layout
        if layout is None or (layout.format or layout.kind) != "mysqldump":
            continue
        archive = layout.locator
        if not archive:
            return ""
        try:
            return str(Path(archive).relative_to(root))
        except ValueError:
            return str(archive)
    return ""


def _binding_sources(blueprint: Any) -> dict[str, dict[str, Any]]:
    """Plan-time map: record type name to its binding and declared sources."""
    resolve = _source_closure(blueprint)
    sources = _relation_sources(blueprint)
    found: dict[str, dict[str, Any]] = {}
    for index, binding in enumerate(blueprint.bindings):
        name = str(binding.name)
        if not name:
            continue
        kind = "node" if not isinstance(binding, EdgeBindingDTO) else "edge"
        relations: set[str] = set()
        for relation in _binding_relations(binding):
            relations.update(resolve(relation))
        selected = [
            sources[relation] for relation in sorted(relations)
            if relation in sources
        ]
        found[name] = {
            "kind": kind,
            "index": index,
            "sources": selected,
        }
    return found


class EvidencePlanner:
    """Plan the one deferred step that publishes the evidence sidecar."""

    component_id = COMPONENT
    version = "1"
    runtime_fields: tuple[Any, ...] = ()

    def plan(self, model: Any, context: Any) -> tuple[Step, ...]:
        del context
        return (
            Step(
                component=self.component_id,
                name="sidecar",
                inputs=(
                    Input(
                        ArtifactPattern.of("core", "graph", "**"),
                        None,
                        RECORDS_INPUT,
                    ),
                ),
                outputs=(
                    Publication(
                        ArtifactType.of(self.component_id, "sidecar"),
                        Key(("evidence",)),
                    ),
                ),
                instruction=Instruction(SIDECAR, cast(Any, {
                    "relative_path": RELATIVE_PATH,
                    "manifest_path": MANIFEST_PATH,
                    "limit": EVIDENCE_LIMIT,
                    "archive": _archive_location(model),
                    "bindings": _binding_sources(model),
                })),
                assembly_preference="deferred",
            ),
        )


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _row(record: Mapping[str, Any], limit: int) -> dict[str, Any]:
    """The record's own locating and evidence values, capped for size."""
    row: dict[str, Any] = {}
    for name, value in record.items():
        if name not in ROW_FIELDS:
            continue
        if isinstance(value, (list, tuple)):
            row[name] = list(value)[:limit]
        else:
            row[name] = value
    if record.get("kind") == "edge":
        row["source_build_key"] = record.get("source_build_key")
        row["target_build_key"] = record.get("target_build_key")
    return row


def _evidence(record: Mapping[str, Any], limit: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for name in EVIDENCE_FIELDS:
        for value in _as_list(record.get(name))[:limit]:
            if value is None or value == "":
                continue
            items.append({"field": name, "value": value})
            if len(items) >= limit:
                return items
    return items


def _entry(
    record: Mapping[str, Any],
    binding: Mapping[str, Any],
    *,
    archive: str,
    limit: int,
) -> dict[str, Any]:
    sources = list(binding.get("sources") or ())
    evidence = _evidence(record, limit)
    count = record.get("count")
    total = int(count) if isinstance(count, (int, float)) else len(evidence)
    files = sorted({str(source["file"]) for source in sources})
    tables = sorted({str(source["table"]) for source in sources})
    return {
        "build_key": record.get("build_key"),
        "kind": record.get("kind"),
        "type": record.get("type"),
        "binding": f"binding:{binding.get('kind')}:{binding.get('index')}",
        "source": {
            "files": files or ([archive] if archive else []),
            "tables": tables,
            "row": _row(record, limit),
        },
        "sources": sources,
        "evidence": evidence,
        "evidence_total": total,
    }


class EvidenceExecutor:
    """Read the projected records and publish the sidecar and its manifest."""

    kinds: tuple[InstructionKind, ...] = (SIDECAR,)
    resources = (RelationService, OutputStorage)

    def execute(
        self,
        context: ExecutionContext | DisruptedExecutionContext,
        instruction: Instruction,
    ) -> Any:
        if isinstance(context, DisruptedExecutionContext):
            return skipped(context)
        payload = instruction_payload(instruction)
        relative_path = str(payload["relative_path"])
        manifest_path = str(payload["manifest_path"])
        declared_limit = payload.get("limit")
        limit = (
            int(declared_limit)
            if isinstance(declared_limit, int)
            else EVIDENCE_LIMIT
        )
        archive = str(payload.get("archive") or "")
        declared_bindings = payload.get("bindings")
        bindings: dict[str, Any] = {}
        if isinstance(declared_bindings, Mapping):
            bindings = {
                str(name): value for name, value in declared_bindings.items()
            }
        resources = context.resources
        path = output_path(resources, relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        written: list[dict[str, Any]] = []
        missing: list[str] = []
        for contribution in input_values(context, RECORDS_INPUT):
            artifact = artifact_of(contribution)
            if artifact is None:
                continue
            identity = graph_record_artifact(artifact.type)
            if identity is None:
                continue
            kind, component = identity.kind, identity.component
            binding = bindings.get(
                component, {"kind": kind, "index": -1, "sources": []}
            )
            relation = reference(resources, artifact.value)
            result = query(resources, f"SELECT * FROM {relation}")
            columns = tuple(column[0] for column in result.description)
            while batch := result.fetchmany(1_000):
                for values in batch:
                    record = dict(zip(columns, values, strict=True))
                    record.update(
                        build_key=str(record["build_key"]),
                        type=component,
                        kind=kind,
                    )
                    entry = _entry(
                        record,
                        binding,
                        archive=archive,
                        limit=limit,
                    )
                    if not entry["source"]["tables"]:
                        missing.append(str(record.get("type")))
                    written.append(entry)

        written.sort(key=lambda item: str(item["build_key"]))
        with path.open("w", encoding="utf-8") as handle:
            for entry in written:
                handle.write(
                    json.dumps(entry, sort_keys=True, default=str) + "\n",
                )

        counts = Counter(str(entry["type"]) for entry in written)
        manifest = {
            "source": "the projected facts records",
            "output": relative_path,
            "entries": len(written),
            "missing": len(missing),
            "missing_types": sorted(set(missing)),
            "by_type": dict(sorted(counts.items())),
            "limit": limit,
        }
        manifest_target = output_path(resources, manifest_path)
        manifest_target.write_text(
            json.dumps(manifest, indent=1, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return succeeded(context, manifest)


__all__ = [
    "COMPONENT",
    "EVIDENCE_LIMIT",
    "EvidenceExecutor",
    "EvidencePlanner",
    "SIDECAR",
]
