"""Frontend monitors that observe pipeline events.

A monitor is a listener. It does not own execution, resources or scheduling;
``resolve_monitor`` turns the public ``monitor`` argument into a listener or
``None``. ``rich`` is optional and imported only when a console monitor writes.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from typing import TYPE_CHECKING, Literal, Protocol, overload

from kg_build_system.kernel import (
    PipelineEvent,
    PipelineFinished,
    PipelineHalted,
    PipelineStarted,
    StepFinished,
    StepId,
    StepLogged,
    StepOutcome,
    StepStarted,
    StepStatus,
)

if TYPE_CHECKING:
    from rich.console import Console, Group, RenderableType
    from rich.live import Live
    from rich.progress import BarColumn, Progress, TaskID
    from rich.text import Text


class Monitor(Protocol):
    """A frontend listener that presents one pipeline run.

    A monitor may be passed directly as a listener because it is callable, and
    the event bus also recognises an object exposing ``on_event``.

    Example:
    ```python
    from kg_build_system.frontend import NullMonitor

    monitor: Monitor = NullMonitor()
    ```
    """

    def on_event(self, event: PipelineEvent) -> None:
        """Handle one pipeline event.

        Example:
            ```python
            monitor.on_event(StepStarted(StepId("core", "source")))
            ```
        """
        ...

    def __call__(self, event: PipelineEvent) -> None:
        """Handle one event when the monitor is subscribed as a callable.

        Example:
            ```python
            monitor(StepStarted(StepId("core", "source")))
            ```
        """
        ...


class NullMonitor:
    """A monitor that presents nothing."""

    def on_event(self, event: PipelineEvent) -> None:
        """Ignore one pipeline event.

        Example:
            ```python
            NullMonitor().on_event(event)
            ```
        """
        pass

    def __call__(self, event: PipelineEvent) -> None:
        """Ignore one pipeline event.

        Example:
            ```python
            NullMonitor()(event)
            ```
        """
        self.on_event(event)


class ConsoleMonitor:
    """A simple text monitor for interactive builds.

    Messages are printed to a ``rich`` console when available; otherwise they
    are printed with the built-in ``print``. ``rich`` is imported lazily so the
    kernel and non-interactive runs do not load it.

    Example:
    ```python
    from kg_build_system.frontend import ConsoleMonitor

    monitor = ConsoleMonitor()
    ```
    """

    def __init__(self, console: Console | None = None) -> None:
        self._console = console

    def _write(self, text: str) -> None:
        console = self._console
        if console is None:
            try:
                from rich.console import Console
            except ImportError:
                print(text)
                return
            console = Console()
            self._console = console
        console.print(text)

    def on_event(self, event: PipelineEvent) -> None:
        """Render one pipeline event as one text line.

        Example:
            ```python
            ConsoleMonitor().on_event(StepStarted(StepId("core", "source")))
            ```
        """
        if isinstance(event, PipelineStarted):
            self._write(
                f"Pipeline started: {len(event.plan.steps)} step(s)",
            )
        elif isinstance(event, StepStarted):
            self._write(f"▶ {event.step_id} {event.detail}".rstrip())
        elif isinstance(event, StepLogged):
            self._write(
                f"[{event.step_id}] {event.level.upper()} {event.message}",
            )
        elif isinstance(event, StepFinished):
            self._write(
                f"■ {event.outcome.step_id} {event.detail}".rstrip(),
            )
        elif isinstance(event, PipelineFinished):
            self._write(
                "Pipeline finished: "
                f"{len(event.report.published_artifacts)} artifact(s)",
            )
        elif isinstance(event, PipelineHalted):
            self._write(f"Pipeline halted: {event.error}")

    def __call__(self, event: PipelineEvent) -> None:
        """Handle one event when the monitor is subscribed as a callable.

        Example:
            ```python
            ConsoleMonitor()(StepStarted(StepId("core", "source")))
            ```
        """
        self.on_event(event)


@overload
def resolve_monitor(value: Literal[True]) -> ConsoleMonitor: ...


@overload
def resolve_monitor(value: Literal[False] | None) -> None: ...


@overload
def resolve_monitor[T: Monitor](value: T) -> T: ...


@overload
def resolve_monitor(value: bool) -> Monitor | None: ...


def resolve_monitor(value: Monitor | bool | None) -> Monitor | None:
    """Turn the public monitor argument into a listener or ``None``.

    ``False`` and ``None`` select no listener; ``True`` selects a
    ``ConsoleMonitor``; a monitor is returned unchanged.

    Example:
    ```python
    from kg_build_system.frontend import resolve_monitor

    assert resolve_monitor(False) is None
    assert isinstance(resolve_monitor(True), ConsoleMonitor)
    ```
    """
    if value is True:
        return ConsoleMonitor()
    if value is False or value is None:
        return None
    return value


@dataclass
class _StepDisplay:
    """The display state of one step in the live monitor."""

    component: str
    state: str = "pending"
    detail: str = "Waiting"


_STATUS_ICON = {
    StepStatus.SUCCEEDED: ("✓", "green"),
    StepStatus.WARNING: ("!", "yellow"),
    StepStatus.FAILED: ("✗", "red"),
    StepStatus.SKIPPED: ("−", "dim"),
}


class RichMonitor:
    """A live terminal display of one pipeline run.

    Three panels: overall progress, the steps nearest the cursor and the latest
    log lines. The monitor writes to ``stderr`` by default so a JSON report on
    ``stdout`` stays machine-readable. ``rich`` is imported when the run
    starts, so an embedded pipeline that presents nothing does not load it.

    Example:
    ```python
    from rich.console import Console

    from kg_build_system.frontend import RichMonitor

    monitor = RichMonitor(console=Console(stderr=True))
    ```
    """

    def __init__(
        self,
        *,
        console: Console | None = None,
        step_lines: int = 8,
        log_lines: int = 8,
        refresh_per_second: float = 10,
    ) -> None:
        if step_lines < 2:
            raise ValueError("step_lines must be at least two")
        if log_lines < 1:
            raise ValueError("log_lines must be at least one")
        self._console = console
        self._step_lines = step_lines
        self._log_lines = log_lines
        self._refresh_per_second = refresh_per_second
        self._logs: deque[Text] = deque(maxlen=log_lines)
        self._steps: dict[StepId, _StepDisplay] = {}
        self._order: tuple[StepId, ...] = ()
        self._finished: list[StepId] = []
        self._completed = 0
        self._status = "Running"
        self._status_style = "bold green"
        self._progress: Progress | None = None
        self._task: TaskID | None = None
        self._bar: BarColumn | None = None
        self._live: Live | None = None
        self._lock = RLock()

    def on_event(self, event: PipelineEvent) -> None:
        """Render one pipeline event.

        Example:
            ```python
            monitor.on_event(StepStarted(StepId("core", "source")))
            ```
        """
        with self._lock:
            if isinstance(event, PipelineStarted):
                self._start(event)
            elif isinstance(event, StepStarted):
                self._step_started(event.step_id, event.detail)
            elif isinstance(event, StepLogged):
                self._log(event.level, event.message, event.step_id)
            elif isinstance(event, StepFinished):
                self._step_finished(event.outcome, event.detail)
            elif isinstance(event, PipelineFinished):
                self._finished_pipeline(event)
            elif isinstance(event, PipelineHalted):
                self._halted(event)

    def __call__(self, event: PipelineEvent) -> None:
        """Handle one event when the monitor is subscribed as a callable."""
        self.on_event(event)

    def stop(self) -> None:
        """Stop the live display without waiting for a terminal event."""
        with self._lock:
            self._stop()

    def _start(self, event: PipelineStarted) -> None:
        from rich.console import Console
        from rich.live import Live
        from rich.progress import BarColumn, Progress, TaskProgressColumn

        console = self._console
        if console is None:
            console = Console(stderr=True)
            self._console = console
        self._order = tuple(step.id for step in event.plan.steps)
        self._steps = {
            step_id: _StepDisplay(step_id.component)
            for step_id in self._order
        }
        self._finished = []
        self._completed = 0
        self._logs.clear()
        self._bar = BarColumn(
            bar_width=None,
            style="green dim",
            complete_style="green",
            finished_style="green",
            pulse_style="green",
        )
        self._progress = Progress(
            self._bar,
            TaskProgressColumn(),
            console=console,
            expand=True,
        )
        self._task = self._progress.add_task(
            "workflow", total=len(self._order), completed=0,
        )
        self._live = Live(
            self._render(),
            console=console,
            refresh_per_second=self._refresh_per_second,
            transient=False,
        )
        self._live.start(refresh=True)

    def _step_started(self, step_id: StepId, detail: str) -> None:
        display = self._steps.get(step_id)
        if display is None:
            return
        display.state = "processing"
        display.detail = detail
        self._refresh()

    def _step_finished(self, outcome: StepOutcome, detail: str) -> None:
        display = self._steps.get(outcome.step_id)
        if display is None:
            return
        display.state = outcome.status.value
        display.detail = detail
        self._finished.append(outcome.step_id)
        self._completed += 1
        if self._progress is not None and self._task is not None:
            self._progress.update(self._task, completed=self._completed)
        if outcome.status is StepStatus.FAILED:
            self._set_status("Continuing with errors", "yellow")
        self._refresh()

    def _finished_pipeline(self, event: PipelineFinished) -> None:
        if event.report.unresolved_failures:
            self._set_status("Halted", "red")
        elif event.report.recovered_failures:
            self._set_status("Completed with errors", "yellow")
        else:
            self._set_status("Succeeded", "green")
        self._refresh()
        self._stop()

    def _halted(self, event: PipelineHalted) -> None:
        self._set_status("Halted", "red")
        self._log("error", str(event.error))
        self._refresh()
        self._stop()

    def _log(
        self, level: str, message: str, step_id: StepId | None = None,
    ) -> None:
        from rich.text import Text

        timestamp = datetime.now().astimezone().strftime("%H:%M:%S")
        name = level.upper()
        style = {
            "DEBUG": "dim",
            "INFO": "cyan",
            "WARNING": "yellow",
            "ERROR": "red",
        }.get(name, "white")
        line = Text()
        line.append(timestamp, style="dim")
        line.append(f" {name:<7}", style=style)
        if step_id is not None:
            line.append(f" {step_id.name}", style="bold")
        line.append(f" {message}")
        self._logs.append(line)
        self._refresh()

    def _render_steps(self) -> RenderableType:
        from rich.console import Group
        from rich.spinner import Spinner
        from rich.text import Text

        processing = [
            step_id for step_id in self._order
            if self._steps[step_id].state == "processing"
        ]
        finished = list(reversed(self._finished))
        settled = set(processing) | set(self._finished)
        rest = [
            step_id for step_id in self._order if step_id not in settled
        ]
        ordered = (*processing, *finished, *rest)
        visible = (
            self._step_lines - 1
            if len(ordered) > self._step_lines
            else self._step_lines
        )
        overflow = max(0, len(ordered) - visible)
        lines: list[RenderableType] = []
        for step_id in ordered[:visible]:
            display = self._steps[step_id]
            label = Text()
            label.append(step_id.name, style="bold")
            label.append(f" [{display.component}]", style="dim")
            label.append(f" — {display.detail}")
            if display.state == "processing":
                lines.append(Spinner("dots", text=label, style="cyan"))
            elif display.state == "pending":
                lines.append(Text.assemble(("○ ", "dim"), label))
            else:
                icon, style = _STATUS_ICON[StepStatus(display.state)]
                lines.append(Text.assemble((f"{icon} ", style), label))
        if overflow:
            lines.append(
                Text(f"… {overflow} more step(s)", style="dim italic"),
            )
        return Group(*lines) if lines else Text("No workflow steps", style="dim")

    def _render_logs(self) -> RenderableType:
        from rich.console import Group
        from rich.text import Text

        if not self._logs:
            return Text("Waiting for step messages…", style="dim")
        return Group(*self._logs)

    def _render(self) -> RenderableType:
        from rich.console import Group
        from rich.panel import Panel
        from rich.text import Text

        progress: RenderableType = (
            self._progress
            if self._progress is not None
            else Text("Preparing workflow", style="dim")
        )
        status = Text(
            f"{self._status} {self._completed}/{len(self._order)} steps",
            style=self._status_style,
        )
        return Group(
            Panel(
                Group(status, progress),
                title="Workflow",
                border_style="blue",
            ),
            Panel(
                self._render_steps(),
                title="Steps",
                border_style="cyan",
                height=self._step_lines + 2,
            ),
            Panel(self._render_logs(), title="Logs", border_style="dim"),
        )

    def _refresh(self) -> None:
        if self._live is not None:
            self._live.update(self._render(), refresh=True)

    def _set_status(self, status: str, color: str) -> None:
        self._status = status
        self._status_style = f"bold {color}"
        if self._bar is not None:
            self._bar.style = f"{color} dim"
            self._bar.complete_style = color
            self._bar.finished_style = color
            self._bar.pulse_style = color

    def _stop(self) -> None:
        live, self._live = self._live, None
        if live is not None:
            live.stop()


__all__ = ["ConsoleMonitor", "Monitor", "NullMonitor", "RichMonitor", "resolve_monitor"]
