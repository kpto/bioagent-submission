"""The ``kbs`` command-line interface."""
from __future__ import annotations

import argparse
import asyncio
import inspect
import logging
import sys
from collections.abc import Coroutine
from pathlib import Path
from typing import Any, Sequence, cast

from kg_build_system.generation.code_generation.service.internal import (
    add_generate_command,
)
from .init import add_init_command
from .iteration import add_iteration_commands
from .manifest_command import add_manifest_commands
from .view import add_view_command


def _configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    ))
    logger = logging.getLogger("kg_build_system")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def _add_console_arguments(parser: argparse.ArgumentParser) -> None:
    """The flags shared by ``console`` and the ``up`` shortcut."""
    parser.add_argument(
        "--project", dest="project", metavar="PROJECT", default=".",
        help="project directory",
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind address")
    parser.add_argument(
        "--port", type=int, default=None,
        help="console port; defaults to the first free port from 8000",
    )
    parser.add_argument(
        "--snapshot", type=Path, default=None,
        help="workflow plan, blueprint or viewer snapshot; defaults to the "
        "project's build/workflow_plan.json",
    )
    parser.add_argument(
        "--no-open", action="store_true", help="do not open a browser",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="run the source dev servers for the console and viewer behind kbs",
    )


def _run_console(arguments: argparse.Namespace) -> int:
    if getattr(arguments, "dev", False):
        from .console import _snapshot as read_snapshot
        from .dev.service import serve_console_dev

        root = Path(arguments.project)
        snapshot, snapshot_type = read_snapshot(root, arguments.snapshot)
        return serve_console_dev(
            root,
            snapshot,
            snapshot_type,
            host=arguments.host,
            port=arguments.port,
            no_open=arguments.no_open,
            open_viewer=getattr(arguments, "also_viewer", False),
        )
    from .console import run_console

    return run_console(arguments)


def _run_guide(arguments: argparse.Namespace) -> int:
    from importlib.resources import files

    text = files("kg_build_system").joinpath("PHILOSOPHY.md").read_text(
        encoding="utf-8"
    )
    print(text, end="")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kbs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "command groups:\n"
            "  model      init, generate, blueprint, workflow, check, run\n"
            "  iteration  finding, proposal, revision, evaluation\n"
            "  read       view, console, up, guide\n"
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True)
    add_generate_command(commands)
    add_init_command(commands)
    add_manifest_commands(commands)
    add_view_command(commands)
    add_iteration_commands(commands)

    console = commands.add_parser(
        "console",
        help="serve the project console and the design viewer",
    )
    _add_console_arguments(console)
    console.set_defaults(command_handler=_run_console)

    up = commands.add_parser(
        "up",
        help="serve both surfaces and open the console and design viewer",
    )
    _add_console_arguments(up)
    up.set_defaults(command_handler=_run_console, also_viewer=True)

    guide = commands.add_parser(
        "guide",
        help="print the framework philosophy",
        description=(
            "Print the framework's philosophy: the principles it enforces and "
            "the practices each one rules out."
        ),
    )
    guide.set_defaults(command_handler=_run_guide)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    _configure_logging()
    parser = _parser()
    arguments = parser.parse_args(argv)
    try:
        result = arguments.command_handler(arguments)
        if inspect.isawaitable(result):
            return asyncio.run(cast(Coroutine[Any, Any, int], result))
        return result
    except KeyboardInterrupt:
        logging.getLogger("kg_build_system").info("Stopped.")
        return 0
    except ValueError as error:
        parser.error(str(error))


__all__ = ["main"]
