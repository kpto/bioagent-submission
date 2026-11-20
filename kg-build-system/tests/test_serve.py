"""A default port takes the next free one; a named port is used as given."""

from __future__ import annotations

import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from kg_build_system.cli.service._private.serve import open_server


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *values: object) -> None:
        return


def _server(address: tuple[str, int]) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(address, _Handler)


def _held_port() -> tuple[socket.socket, int]:
    """Return a socket holding one port open, and that port."""
    held = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    held.bind(("127.0.0.1", 0))
    held.listen(1)
    return held, int(held.getsockname()[1])


def test_a_named_port_is_used_as_given() -> None:
    held, port = _held_port()
    held.close()
    server: ThreadingHTTPServer | None = None
    try:
        server = open_server(_server, "127.0.0.1", port, default=port + 100)
        assert server.server_port == port
    finally:
        if server is not None:
            server.server_close()


def test_a_named_busy_port_reports_the_error() -> None:
    held, port = _held_port()
    try:
        with pytest.raises(OSError):
            open_server(_server, "127.0.0.1", port, default=port + 1)
    finally:
        held.close()


def test_a_default_port_moves_to_the_next_free_one() -> None:
    held, port = _held_port()
    server: ThreadingHTTPServer | None = None
    try:
        if port > 65530:
            pytest.skip("the held port is too close to the ceiling")
        server = open_server(_server, "127.0.0.1", None, default=port, attempts=5)
        assert server.server_port > port
    finally:
        if server is not None:
            server.server_close()
        held.close()
