"""Test support: compile and execute the manifest without a project surface.

The project is a declaration package. These helpers are the same two framework
calls every build makes, so a test asserts the declaration, not a wrapper.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from kg_build_system import (
    GraphBlueprint,
    WorkflowPlan,
    WorkflowReport,
    compile,
    create_blueprint,
    execute,
)
from kg_build_system.distribution.interpreter.service.internal.codec import (
    blueprint_to_document,
)

from pharos_kg.manifest import blueprint as blueprint_declaration
from pharos_kg.manifest import workflow as workflow_declaration


def create_pharos_blueprint() -> GraphBlueprint:
    """Build the semantic model from the project's declarations."""
    return create_blueprint(
        namespace_path=blueprint_declaration.namespace_path,
        bindings=blueprint_declaration.bindings,
        languages=blueprint_declaration.languages,
    )


def compile_pharos(blueprint: GraphBlueprint | None = None) -> WorkflowPlan:
    """Compile the blueprint into the workflow the manifest declares."""
    return compile(
        blueprint=blueprint or create_pharos_blueprint(),
        planners=workflow_declaration.planners,
        toolchain=workflow_declaration.toolchain,
    )


def blueprint_revision(blueprint: GraphBlueprint) -> str:
    """A stable short fingerprint of the semantic model."""
    payload = json.dumps(
        blueprint_to_document(blueprint),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def run_pharos(output_directory: str | Path) -> WorkflowReport:
    """Execute the declared workflow into one directory."""
    return execute(
        compile_pharos(),
        output_directory=Path(output_directory),
        toolchain=workflow_declaration.toolchain,
    )


__all__ = [
    "blueprint_revision",
    "compile_pharos",
    "create_pharos_blueprint",
    "run_pharos",
]
