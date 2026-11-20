"""Serve the project console and the design viewer on one origin.

The console reads the iteration ledger through three JSON endpoints:
``/console/api/relations`` (the object catalog and the event timeline derived
from the typed events), ``/console/api/revisions`` (the revision lineage and,
with ``?focus=<id>``, one revision's dependency diff) and
``/console/api/config`` (the project and its ledger). The design viewer is served at ``/`` and its snapshot at
``/snapshot``.
"""

from __future__ import annotations

import json
import socket
import sys
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from kg_build_system.iteration import (
    EvaluationCreated,
    EvaluationRun,
    Event,
    FindingCreated,
    ProposalCreated,
    RevisionCreated,
    ledger_directory,
    load_ledger,
    revision_lineage,
)

from .serve import open_server

#: The console object kind each recorded event produces.
KIND = {
    "revision.created": "revision",
    "finding.created": "finding",
    "proposal.created": "proposal",
    "evaluation.created": "evaluation_design",
    "evaluation.run": "evaluation_run",
}


def _code(by_id: dict[str, Event], event_id: str) -> str:
    target = by_id.get(event_id)
    return target.code if target is not None else event_id


def _object(event: Event, by_id: dict[str, Event]) -> dict[str, Any] | None:
    kind = KIND.get(event.event_type)
    if kind is None:
        return None
    fields: list[dict[str, str]] = []
    links: list[dict[str, str]] = []
    summary = ""
    if isinstance(event, RevisionCreated):
        description = event.description
        if isinstance(description, dict):
            summary = str(
                description.get("detail")
                or description.get("message")
                or ""
            )
        fields.append(
            {
                "label": "Proposals",
                "value": str(len(event.based_proposals)),
                "kind": "metric",
            }
        )
        links.extend(
            {"id": _code(by_id, item), "kind": "proposal", "role": "implements"}
            for item in event.based_proposals
        )
    elif isinstance(event, ProposalCreated):
        summary = str(event.rationale)
        links.append(
            {
                "id": _code(by_id, event.based_revision),
                "kind": "revision",
                "role": "based_on",
            }
        )
    elif isinstance(event, FindingCreated):
        summary = str(event.observation)
        if event.evidence:
            fields.append({"label": "Evidence", "value": str(event.evidence)})
    elif isinstance(event, EvaluationCreated):
        summary = str(event.method)
        if event.metric:
            fields.append({"label": "Metric", "value": str(event.metric)})
    elif isinstance(event, EvaluationRun):
        links.append(
            {
                "id": _code(by_id, event.evaluated_revision),
                "kind": "revision",
                "role": "measures",
            }
        )
        links.append(
            {
                "id": _code(by_id, event.evaluation),
                "kind": "evaluation_design",
                "role": "runs",
            }
        )
        result = event.result
        if isinstance(result, dict):
            design = result.get("design")
            if design:
                links.append(
                    {
                        "id": str(design),
                        "kind": "evaluation_design",
                        "role": "design",
                    }
                )
            for label, key in (
                ("Method", "method"),
                ("Design", "design"),
                ("Graph", "graph"),
            ):
                value = result.get(key)
                if value:
                    fields.append({"label": label, "value": str(value)})
            metrics = result.get("metrics")
            if isinstance(metrics, dict):
                for label, key in (
                    ("Macro AUPRC", "macro_auprc"),
                    ("Micro AUPRC", "micro_auprc"),
                ):
                    value = metrics.get(key)
                    if isinstance(value, (int, float)):
                        fields.append(
                            {"label": label, "value": f"{value:.6f}"}
                        )
            if result.get("report"):
                fields.append(
                    {"label": "Report", "value": str(result["report"])}
                )
            detail = result.get("detail")
            if detail:
                text = " ".join(str(detail).split())
                fields.append(
                    {
                        "label": "Result",
                        "value": text[:400] + ("…" if len(text) > 400 else ""),
                    }
                )
        elif result is not None:
            fields.append({"label": "Result", "value": str(result)})
    return {
        "id": event.code,
        "kind": kind,
        "title": str(event.title or event.code),
        "summary": summary[:400],
        "created": event.created_time.isoformat(),
        "fields": fields,
        "links": links,
    }


def relations_payload(root: Path) -> dict[str, Any]:
    """The console catalog and timeline for one project."""

    events = load_ledger(root)
    by_id = {event.id: event for event in events}
    objects = [
        item for event in events if (item := _object(event, by_id)) is not None
    ]
    timeline = [
        {
            "id": event.id,
            "type": event.event_type,
            "timestamp": event.created_time.isoformat(),
            "title": str(event.title or event.code),
        }
        for event in events
    ]
    return {"project": root.resolve().name, "objects": objects, "timeline": timeline}


def revision_payload(root: Path, focus: str | None = None) -> dict[str, Any]:
    """The revision lineage, or one revision's focused diff."""

    data = revision_lineage(load_ledger(root), focus=focus)
    return {"project": root.resolve().name, **data}


def config_payload(root: Path) -> dict[str, Any]:
    return {
        "project": root.resolve().name,
        "dataDir": str(ledger_directory(root.resolve())),
    }


def _assets() -> tuple[Path, Path]:
    package = files("kg_build_system")
    console = Path(str(package.joinpath("console_dist")))
    viewer = Path(str(package.joinpath("viewer_dist")))
    if (console / "index.html").exists() and (viewer / "index.html").exists():
        return console, viewer
    source = Path(__file__).resolve().parents[4] / "viewer"
    console_source = source / "console" / "out"
    viewer_source = source / "design" / "out"
    if (console_source / "index.html").exists() and (viewer_source / "index.html").exists():
        return console_source, viewer_source
    raise ValueError(
        "the console assets are not available. Build viewer/console/out and "
        "viewer/design/out with `npm run build:static --workspace console` and "
        "`--workspace design`, or install a wheel with console_dist and viewer_dist"
    )


class ConsoleServer(ThreadingHTTPServer):
    daemon_threads = True
    console_assets: Path
    viewer_assets: Path
    root: Path
    snapshot_bytes: bytes
    snapshot_type: str


class ConsoleHandler(SimpleHTTPRequestHandler):
    server: ConsoleServer

    def __init__(
        self,
        request: Any,
        client_address: Any,
        server: ConsoleServer,
    ) -> None:
        super().__init__(request, client_address, server, directory=str(server.console_assets))

    def _json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def translate_path(self, path: str) -> str:
        parsed = urlparse(path).path
        if parsed.startswith("/console/"):
            relative = parsed[len("/console/") :] or "index.html"
            base = self.server.console_assets
        else:
            relative = parsed.lstrip("/") or "index.html"
            base = self.server.viewer_assets
        candidate = (base / relative).resolve()
        root = base.resolve()
        if candidate != root and root not in candidate.parents:
            return str(root / "index.html")
        return str(candidate)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/console/api/relations", "/api/relations"}:
            self._json(relations_payload(self.server.root))
            return
        if path in {"/console/api/revisions", "/api/revisions"}:
            query = parse_qs(urlparse(self.path).query)
            focus = (query.get("focus") or [None])[0]
            self._json(revision_payload(self.server.root, focus))
            return
        if path in {"/console/api/config", "/api/config"}:
            self._json(config_payload(self.server.root))
            return
        if path == "/console/api/revision-view":
            self._json({"error": "the iteration ledger keeps no captured views"}, 404)
            return
        if path in {"/snapshot", "/api/snapshot"}:
            self.send_response(200)
            self.send_header("Content-Type", self.server.snapshot_type)
            self.send_header("Content-Length", str(len(self.server.snapshot_bytes)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(self.server.snapshot_bytes)
            return
        super().do_GET()

    def log_message(self, format: str, *args: Any) -> None:
        return


def _snapshot(root: Path, selected: Path | None = None) -> tuple[bytes, str]:
    """The project's snapshot, resolved under its root rather than the process CWD."""
    from .view import SNAPSHOT_CANDIDATES
    from .view import _snapshot as read_snapshot

    path = selected
    if path is None:
        path = next(
            (root / candidate for candidate in SNAPSHOT_CANDIDATES if (root / candidate).is_file()),
            None,
        )
    if path is None:
        return b'{"format":"kg-viewer-snapshot","version":1}', "application/json"
    try:
        return read_snapshot(path, None)
    except ValueError:
        return b'{"format":"kg-viewer-snapshot","version":1}', "application/json"


def _network_address() -> str | None:
    """An address a reader on the same network can use, when one exists."""
    try:
        addresses = socket.gethostbyname_ex(socket.gethostname())[2]
    except OSError:
        addresses = []
    for address in addresses:
        if not address.startswith(("127.", "169.254.")):
            return address
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            # A UDP connect sends nothing; it only selects the outbound interface.
            probe.connect(("8.8.8.8", 80))
            address = probe.getsockname()[0]
    except OSError:
        return None
    return None if address.startswith("127.") else address


def _urls(host: str, port: int, path: str) -> tuple[str, str | None]:
    """The local address, and the network address when bound to every interface."""
    if host in {"0.0.0.0", "::", "[::]"}:
        local = f"http://127.0.0.1:{port}{path}"
        address = _network_address()
        return local, f"http://{address}:{port}{path}" if address else None
    display = f"[{host}]" if ":" in host and not host.startswith("[") else host
    return f"http://{display}:{port}{path}", None


def run_console(arguments: Any) -> int:
    root = Path(arguments.project)
    try:
        console_assets, viewer_assets = _assets()
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    snapshot, snapshot_type = _snapshot(root, arguments.snapshot)
    try:
        server = open_server(
            lambda address: ConsoleServer(address, ConsoleHandler),
            arguments.host,
            arguments.port,
            default=8000,
        )
    except OSError as error:
        target = 8000 if arguments.port is None else arguments.port
        print(f"error: cannot bind {arguments.host}:{target}: {error}", file=sys.stderr)
        print("pick another port with --port", file=sys.stderr)
        return 1
    server.console_assets = console_assets
    server.viewer_assets = viewer_assets
    server.root = root
    server.snapshot_bytes = snapshot
    server.snapshot_type = snapshot_type
    url, network = _urls(arguments.host, server.server_port, "/console/")
    viewer, viewer_network = _urls(arguments.host, server.server_port, "/")
    print(f"Console: {url}", flush=True)
    print(f"Design viewer: {viewer}", flush=True)
    if network:
        print(
            f"On the network: {network} (console), {viewer_network} (viewer)",
            flush=True,
        )
    print("Press Ctrl+C to stop.", flush=True)
    if not arguments.no_open:
        webbrowser.open(url)
        if getattr(arguments, "also_viewer", False):
            webbrowser.open(viewer)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


__all__ = [
    "ConsoleHandler",
    "ConsoleServer",
    "config_payload",
    "relations_payload",
    "revision_payload",
    "run_console",
]
