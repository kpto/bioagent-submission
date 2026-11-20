"""The Pharos declarations compile and the graph builds end to end."""

from __future__ import annotations

import json

from kg_build_system import compile, create_blueprint

from tests.support import run_pharos
from pharos_kg.manifest import blueprint as blueprint_declaration
from pharos_kg.manifest import workflow as workflow_declaration


def create_project_blueprint():
    """Build the blueprint the manifest declares; the CLI does this by default."""
    return create_blueprint(
        namespace_path=blueprint_declaration.namespace_path,
        bindings=blueprint_declaration.bindings,
        languages=blueprint_declaration.languages,
    )


def compile_project():
    """Compile the workflow the manifest declares."""
    return compile(
        blueprint=create_project_blueprint(),
        planners=workflow_declaration.planners,
        toolchain=workflow_declaration.toolchain,
    )


def test_the_project_compiles() -> None:
    blueprint = create_project_blueprint()
    assert {
        node.name for node in blueprint.graph.nodes
        if not getattr(node, "abstract", False)
    } == {
        "anatomical_entity",
        "biological_process",
        "disease",
        "gene",
        "ligand",
        "pathway",
        "hpo_term",
        "phenotype",
        "protein",
    }
    assert compile_project() is not None


def test_the_pharos_graph_builds(tmp_path) -> None:
    report = run_pharos(tmp_path)

    assert report.succeeded
    records = [
        json.loads(line)
        for line in (tmp_path / "graph.jsonl").read_text().splitlines()
        if line.strip()
    ]
    nodes = [row for row in records if row["kind"] == "node"]
    edges = [row for row in records if row["kind"] == "edge"]
    assert {row["type"] for row in nodes} == {
        "anatomical_entity",
        "biological_process",
        "disease",
        "gene",
        "ligand",
        "pathway",
        "hpo_term",
        "phenotype",
        "protein",
    }
    assert {row["type"] for row in edges} == {
        "associated_with",
        "binds",
        "expressed_in",
        "disease_has_phenotype",
        "has_hpo_phenotype",
        "has_phenotype",
        "interacts_with",
        "participates_in",
        "participates_in_pathway",
        "process_subclass_of",
        "subclass_of",
        "translates_to",
    }
    assert nodes and edges
    # The build writes canonical order, so two builds of one revision share
    # bytes.
    keys = [
        (str(row.get("kind") or ""), str(row.get("type") or ""), str(row.get("build_key") or ""))
        for row in records
    ]
    assert keys == sorted(keys)

    # Integrity of the shipped graph and the evidence sidecar.
    node_keys = {row["build_key"] for row in nodes}
    edge_keys = {row["build_key"] for row in edges}
    assert len(node_keys) == len(nodes)
    assert len(edge_keys) == len(edges)
    assert not (node_keys & edge_keys)
    dangling = [
        row for row in edges
        if row["source_build_key"] not in node_keys
        or row["target_build_key"] not in node_keys
    ]
    assert dangling == []

    evidence = [
        json.loads(line)
        for line in (tmp_path / "evidence.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert {row["build_key"] for row in evidence} == node_keys | edge_keys
    assert all(row["source"]["tables"] for row in evidence)
    manifest = json.loads((tmp_path / "evidence_manifest.json").read_text())
    assert manifest["missing"] == 0
