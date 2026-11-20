"""The Pharos project's blueprint and workflow composition."""

from dataclasses import replace
from pathlib import Path

from kg_build_system import (
    DEFAULT_TOOLCHAIN,
    Blueprint,
    Workflow,
    default_toolchain,
)
from kg_build_system.distribution import (
    DeduplicationPlanner,
    MetaGraphPlanner,
)
from kg_build_system.distribution.modules.duckdb import (
    DuckDbInstructionEmitter,
    DuckDbSqlEmitter,
)

from pharos_kg.asset.pharos_source import ARCHIVE_BYTES, ARCHIVE_SHA256
from pharos_kg.asset.release import HPO_RELEASE, OPENTARGETS_RELEASE
from pharos_kg.modules.design_guard import (
    DesignGuardPlanner,
    RecordGuardExecutor,
    RecordGuardPlanner,
)
from pharos_kg.modules.annotate import AnnotateExecutor, AnnotatePlanner
from pharos_kg.modules.dump_source import (
    DumpSourceConfiguration,
    DumpSourceExecutor,
    DumpSourcePlanner,
)
from pharos_kg.modules.evidence import EvidenceExecutor, EvidencePlanner
from pharos_kg.modules.output import (
    GraphOutputConfiguration,
    GraphOutputExecutor,
    GraphOutputPlanner,
)
from pharos_kg.modules.project import ProjectExecutor, ProjectPlanner
from pharos_kg.modules.publish import PublishExecutor, PublishPlanner
from pharos_kg.modules.remote_source import (
    RemoteSourceConfiguration,
    RemoteSourceExecutor,
    RemoteSourcePlanner,
)
from pharos_kg.modules.verify import ReconcileExecutor, ReconcilePlanner
from pharos_kg.modules.row_operations import PharosRowOperations

ROOT = Path(__file__).parent

blueprint = Blueprint(namespace_path=ROOT)

engine = DuckDbSqlEmitter(
    instruction_emitter=(
        DuckDbInstructionEmitter().with_row_sources(PharosRowOperations())
    ),
)

base_toolchain = default_toolchain(
    engine=engine,
    planners=(
        DesignGuardPlanner(),
        DumpSourcePlanner(DumpSourceConfiguration(ARCHIVE_SHA256, ARCHIVE_BYTES)),
        RemoteSourcePlanner(RemoteSourceConfiguration("hpo", HPO_RELEASE)),
        RemoteSourcePlanner(
            RemoteSourceConfiguration("opentargets2609", OPENTARGETS_RELEASE)
        ),
        DeduplicationPlanner(),
        RecordGuardPlanner(),
        PublishPlanner(),
        AnnotatePlanner(),
        GraphOutputPlanner(GraphOutputConfiguration(
            "graph.annotated.jsonl",
            component="write_annotated_graph",
            name="annotated",
            annotations=True,
        )),
        ProjectPlanner(),
        GraphOutputPlanner(GraphOutputConfiguration(
            "graph.jsonl",
            component="write_facts_graph",
            name="facts",
            annotations=False,
        )),
        EvidencePlanner(),
        ReconcilePlanner(),
        MetaGraphPlanner(),
    ),
    executors=(
        *DEFAULT_TOOLCHAIN.executors,
        DumpSourceExecutor(),
        RemoteSourceExecutor(),
        RecordGuardExecutor(),
        PublishExecutor(),
        AnnotateExecutor(),
        GraphOutputExecutor(),
        ProjectExecutor(),
        EvidenceExecutor(),
        ReconcileExecutor(),
    ),
)

# WORKAROUND for a framework design flaw.
#
# default_toolchain decides whether to inject its generic DuckDbSourcePlanner
# by testing component_id == "duckdb". That conflates the component label with
# the composition decision: a project that wants its own source component must
# either impersonate "duckdb" (hiding the module in the plan) or remove the
# generic planner after composition. We do the latter, so the plan names
# remote_source and still has exactly one source planner per table.
#
# Replace this block with an explicit source-planner argument, e.g.
# default_toolchain(..., source_planner=False), when the framework exposes one;
# the filter and its knowledge of "duckdb" then disappear.
_remote = tuple(
    planner for planner in base_toolchain.planners
    if isinstance(planner, RemoteSourcePlanner)
)
_others = tuple(
    planner for planner in base_toolchain.planners
    if not isinstance(planner, RemoteSourcePlanner)
    and planner.component_id != "duckdb"
)
toolchain = replace(base_toolchain, planners=(*_remote, *_others))

workflow = Workflow(
    blueprint=blueprint,
    toolchain=toolchain,
    output_directory=ROOT.parent / "build",
)
