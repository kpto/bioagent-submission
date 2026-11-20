"""Package the static viewer surfaces into the wheel.

The design viewer and the console are frontend deliverables.
Their static exports are committed under ``viewer/design/out`` and
``viewer/console/out``; a wheel packages both by default and needs no Node. Rebuilding the exports is opt-in because it requires npm and a compile.

Environment:
    KBS_BUILD_VIEWER=1         rebuild ``viewer/design/out`` before packaging
    KBS_BUILD_CONSOLE=1        rebuild ``viewer/console/out`` before packaging
    KBS_SKIP_VIEWER_BUILD=1    force the existing ``viewer/design/out``
    KBS_SKIP_CONSOLE_BUILD=1   force the existing ``viewer/console/out``
    KBS_SKIP_VIEWER_INSTALL=1  reuse existing ``viewer/node_modules``
    KBS_NPM=/path/to/npm       alternate npm executable
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class ViewerBuildHook(BuildHookInterface):
    PLUGIN_NAME = "viewer"

    def initialize(self, version: str, build_data: dict[str, object]) -> None:
        # Editable installs read the source frontends; only a wheel carries the
        # compiled static exports.
        if version == "editable" or self.target_name != "wheel":
            return

        root = Path(self.root)
        workspace = root / "viewer"
        design = workspace / "design"
        console = workspace / "console"
        design_out = design / "out"
        console_out = console / "out"

        build_viewer = (
            os.environ.get("KBS_BUILD_VIEWER") == "1"
            and os.environ.get("KBS_SKIP_VIEWER_BUILD") != "1"
        )
        build_console = (
            os.environ.get("KBS_BUILD_CONSOLE") == "1"
            and os.environ.get("KBS_SKIP_CONSOLE_BUILD") != "1"
        )
        if build_viewer or build_console:
            for required in (workspace, design, console):
                if not (required / "package.json").exists():
                    raise RuntimeError(
                        f"{required.relative_to(root)}/package.json is missing"
                    )
            npm = os.environ.get("KBS_NPM") or shutil.which("npm")
            if not npm:
                raise RuntimeError(
                    "npm is required to rebuild the bundled frontends; install Node "
                    "or set KBS_NPM, or omit KBS_BUILD_VIEWER/KBS_BUILD_CONSOLE "
                    "to package the committed exports"
                )
            if os.environ.get("KBS_SKIP_VIEWER_INSTALL") != "1":
                subprocess.run([npm, "ci"], cwd=workspace, check=True)
            environment = {
                **os.environ,
                "NEXT_TELEMETRY_DISABLED": "1",
                "CI": "1",
            }
            if build_viewer:
                if design_out.exists():
                    shutil.rmtree(design_out)
                subprocess.run(
                    [npm, "run", "build:static", "--workspace", "design"],
                    cwd=workspace,
                    check=True,
                    env=environment,
                )
            if build_console:
                if console_out.exists():
                    shutil.rmtree(console_out)
                subprocess.run(
                    [npm, "run", "build:static", "--workspace", "console"],
                    cwd=workspace,
                    check=True,
                    env=environment,
                )
        for name, out in (("design viewer", design_out), ("console", console_out)):
            if not (out / "index.html").exists():
                raise RuntimeError(
                    f"{name} export is missing at {out}; run its static build or set "
                    "KBS_BUILD_VIEWER=1/KBS_BUILD_CONSOLE=1"
                )

        self._temp = tempfile.TemporaryDirectory(prefix="kbs-frontends-")
        temporary = Path(self._temp.name)
        for name, out in (("viewer_dist", design_out), ("console_dist", console_out)):
            target = temporary / name
            # Project snapshots are served by the Python servers; demo data is
            # not part of the package.
            shutil.copytree(out, target, ignore=shutil.ignore_patterns("data"))
            build_data["force_include"][str(target)] = f"kg_build_system/{name}"

    def finalize(
        self,
        version: str,
        build_data: dict[str, object],
        artifact_path: str,
    ) -> None:
        temp = getattr(self, "_temp", None)
        if temp is not None:
            temp.cleanup()
            self._temp = None
