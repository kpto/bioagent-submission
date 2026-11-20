from __future__ import annotations

import io
import unittest
from pathlib import Path

from rich.console import Console

from kg_build_system.frontend import RichMonitor
from kg_build_system.kernel import (
    ArtifactType,
    Component,
    Instruction,
    InstructionKind,
    Key,
    PipelineFinished,
    PipelineHalted,
    PipelineStarted,
    Publication,
    ResourceRegistry,
    RuntimeConfiguration,
    Step,
    StepFinished,
    StepId,
    StepLogged,
    StepOutcome,
    StepStarted,
    StepStatus,
    WorkflowPlan,
    WorkflowReport,
)

VALUE = ArtifactType.of("demo", "value")
STEP = StepId("demo", "make")


def _plan() -> WorkflowPlan:
    return WorkflowPlan(
        components=(Component("demo", "1"),),
        steps=(
            Step(
                "demo",
                "make",
                (),
                (Publication(VALUE, Key(("value",))),),
                Instruction(InstructionKind("test", "default"), None),
            ),
        ),
    )


def _started(plan: WorkflowPlan) -> PipelineStarted:
    configuration = RuntimeConfiguration(
        output_directory=Path("build"),
        working_directory=Path("build") / "_workdir",
    )
    return PipelineStarted(plan, configuration, ResourceRegistry())


class RichMonitorTests(unittest.TestCase):
    def test_a_run_renders_progress_steps_and_logs(self) -> None:
        stream = io.StringIO()
        monitor = RichMonitor(
            console=Console(file=stream, width=100, force_terminal=False),
            refresh_per_second=1000,
        )

        monitor.on_event(_started(_plan()))
        monitor.on_event(StepStarted(STEP, "reading 0 input(s)"))
        monitor.on_event(StepLogged(STEP, "info", "rows 3"))
        monitor.on_event(
            StepFinished(
                StepOutcome(STEP, StepStatus.SUCCEEDED),
                "succeeded; 1 artifact(s)",
            ),
        )
        monitor.on_event(PipelineFinished(WorkflowReport((), (), (), {})))

        text = stream.getvalue()
        self.assertIn("Succeeded 1/1 steps", text)
        self.assertIn("make", text)
        self.assertIn("rows 3", text)

    def test_a_halted_run_names_the_error(self) -> None:
        stream = io.StringIO()
        monitor = RichMonitor(
            console=Console(file=stream, width=100, force_terminal=False),
            refresh_per_second=1000,
        )

        monitor.on_event(_started(_plan()))
        monitor.on_event(PipelineHalted(RuntimeError("missing resource")))

        text = stream.getvalue()
        self.assertIn("Halted", text)
        self.assertIn("missing resource", text)

    def test_stop_is_idempotent(self) -> None:
        monitor = RichMonitor(
            console=Console(file=io.StringIO(), force_terminal=False),
        )
        monitor.on_event(_started(_plan()))
        monitor.stop()
        monitor.stop()


if __name__ == "__main__":
    unittest.main()
