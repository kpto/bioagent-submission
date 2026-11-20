"""The project's composition: its blueprint and workflow.

The values are declarations. `kbs blueprint`, `kbs workflow` and `kbs run` read
them and perform the requested step; importing this module builds nothing.

The empty manifest composes the default languages and the graph workflow, and it
declares no output target. A target is a consumer, not a stage: add one only
when the graph's purpose names who consumes the graph. The framework has no
canonical pipeline shape; a plan copied from an example is not a design.
"""

from pathlib import Path

from kg_build_system import (
    Blueprint,
    Workflow,
    default_languages,
    default_toolchain,
)

ROOT = Path(__file__).parent

languages = default_languages()

blueprint = Blueprint(namespace_path=ROOT, languages=languages)

toolchain = default_toolchain(
    languages=languages,
    planners=(
        # A guard, not a stage: keep it when two rows can produce one build_key.
        # Leave it out when the identity is unique by construction.
        #
        #   from kg_build_system.distribution import DeduplicationPlanner
        #   DeduplicationPlanner(),
        #
        # Targets are consumers, not stages. Name who consumes this graph, then
        # add only the target that consumer needs:
        #
        #   from kg_build_system.distribution import (
        #       FileConfiguration, FilePlanner, MetaGraphPlanner, Neo4jPlanner,
        #   )
        #
        #   FilePlanner(FileConfiguration("graph.jsonl"))  # readers, git, diffs
        #   Neo4jPlanner()                                 # a graph database
        #   MetaGraphPlanner()                             # notebook data document
    ),
)

workflow = Workflow(
    blueprint=blueprint,
    toolchain=toolchain,
    output_directory=ROOT.parent / "build",
)
