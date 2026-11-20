"""Compose the dev commands and one reverse proxy for the console and viewer."""

from __future__ import annotations

import json
import signal
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from ..console import _urls, config_payload, relations_payload, revision_payload
from .env import load_dev_config
from .proxy import LocalData, Route, make_proxy_server
from .session import DevSession

DEFAULT_PORT = 8000
PORT_ATTEMPTS = 11


def _display_host(host: str) -> str:
    return "127.0.0.1" if host in {"0.0.0.0", "::", "[::]"} else host


def _bind(host: str, port: int | None, local: LocalData, routes: list[Route]):
    candidates = [port] if port is not None else list(
        range(DEFAULT_PORT, DEFAULT_PORT + PORT_ATTEMPTS)
    )
    last: OSError | None = None
    for candidate in candidates:
        try:
            return make_proxy_server(host, int(candidate), local, routes)
        except OSError as error:
            last = error
            if port is not None:
                raise OSError(
                    f"cannot bind dev proxy to {host}:{port}: {error}"
                ) from error
    raise OSError(
        f"cannot bind dev proxy in {DEFAULT_PORT}-"
        f"{DEFAULT_PORT + PORT_ATTEMPTS - 1}: {last}"
    )


def _run(server, session: DevSession) -> int:
    previous = None
    try:
        import signal as _signal

        def stop(signum: int, frame: object) -> None:
            raise KeyboardInterrupt

        previous = _signal.getsignal(_signal.SIGTERM)
        _signal.signal(_signal.SIGTERM, stop)
    except (ImportError, OSError, ValueError):
        previous = None
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        session.stop()
        if previous is not None:
            try:
                signal.signal(signal.SIGTERM, previous)
            except (OSError, ValueError):
                pass
    return 0


def _json(payload: object, status: int = 200) -> tuple[int, str, bytes]:
    return status, "application/json", json.dumps(payload, default=str).encode()


def _local_data(
    root: Path, snapshot: bytes, snapshot_type: str
) -> LocalData:
    """The kbs-owned paths: snapshot and ledger API, never the dev servers."""

    def local(path: str) -> tuple[int, str, bytes] | None:
        parsed = urlsplit(path)
        if parsed.path in {"/snapshot", "/api/snapshot"}:
            return 200, snapshot_type, snapshot
        if parsed.path in {"/console/api/relations", "/api/relations"}:
            return _json(relations_payload(root))
        if parsed.path in {"/console/api/config", "/api/config"}:
            return _json(config_payload(root))
        if parsed.path in {"/console/api/revisions", "/api/revisions"}:
            focus = (parse_qs(parsed.query).get("focus") or [None])[0]
            return _json(revision_payload(root, focus))
        return None

    return local


def serve_view_dev(
    snapshot: bytes,
    snapshot_type: str,
    *,
    host: str = "127.0.0.1",
    port: int | None = None,
    no_open: bool = False,
) -> int:
    """Start the viewer dev command and proxy it beside the kbs snapshot."""

    config = load_dev_config()
    session = DevSession()
    try:
        viewer = session.start(
            "viewer", config.command("viewer"), config.cwd, health_path="/"
        )

        def local(path: str) -> tuple[int, str, bytes] | None:
            if urlsplit(path).path in {"/snapshot", "/api/snapshot"}:
                return 200, snapshot_type, snapshot
            return None

        routes = [
            Route("/", "127.0.0.1", viewer.port, f"http://127.0.0.1:{viewer.port}")
        ]
        server = _bind(host, port, local, routes)
        url, network = _urls(host, server.server_port, "/")
        print(f"kbs dev viewer: {url}", flush=True)
        if network:
            print(f"On the network: {network}", flush=True)
        print(f"viewer -> 127.0.0.1:{viewer.port}", flush=True)
        if not no_open:
            webbrowser.open(url)
        return _run(server, session)
    except Exception:
        session.stop()
        raise


def serve_console_dev(
    root: Path,
    snapshot: bytes,
    snapshot_type: str,
    *,
    host: str = "127.0.0.1",
    port: int | None = None,
    no_open: bool = False,
    open_viewer: bool = False,
) -> int:
    """Start both dev commands and proxy them beside the kbs-owned API."""

    config = load_dev_config()
    session = DevSession()
    try:
        viewer = session.start(
            "viewer", config.command("viewer"), config.cwd, health_path="/"
        )
        console = session.start(
            "console",
            config.command("console"),
            config.cwd,
            health_path="/console/",
        )
        routes = [
            Route(
                "/console",
                "127.0.0.1",
                console.port,
                f"http://127.0.0.1:{console.port}",
            ),
            Route(
                "/",
                "127.0.0.1",
                viewer.port,
                f"http://127.0.0.1:{viewer.port}",
            ),
        ]
        server = _bind(host, port, _local_data(root, snapshot, snapshot_type), routes)
        console_url, network = _urls(host, server.server_port, "/console/")
        viewer_url, viewer_network = _urls(host, server.server_port, "/")
        print(f"kbs dev console: {console_url}", flush=True)
        print(f"kbs dev viewer: {viewer_url}", flush=True)
        if network:
            print(
                f"On the network: {network} (console), {viewer_network} (viewer)",
                flush=True,
            )
        print(f"viewer -> 127.0.0.1:{viewer.port}", flush=True)
        print(f"console -> 127.0.0.1:{console.port}", flush=True)
        if not no_open:
            webbrowser.open(console_url)
            if open_viewer:
                webbrowser.open(viewer_url)
        return _run(server, session)
    except Exception:
        session.stop()
        raise
