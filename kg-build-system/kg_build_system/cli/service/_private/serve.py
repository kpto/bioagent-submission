"""Bind a local server, taking the next free port when none is named."""

from __future__ import annotations

import errno
from http.server import ThreadingHTTPServer
from typing import Callable, TypeVar

_ADDRESS_IN_USE = frozenset({errno.EADDRINUSE, 10048})
_ATTEMPTS = 11

Server = TypeVar("Server", bound=ThreadingHTTPServer)


def open_server(
    factory: Callable[[tuple[str, int]], Server],
    host: str,
    port: int | None,
    *,
    default: int,
    attempts: int = _ATTEMPTS,
) -> Server:
    """Return a server bound to a port.

    A named ``port`` is never moved: when it is taken the bind error propagates,
    so a caller that asked for one port learns it is unavailable. With no port
    named, the first free port from ``default`` is taken.
    """
    if port is not None:
        return factory((host, port))
    last: OSError | None = None
    for candidate in range(default, min(default + attempts, 65536)):
        try:
            return factory((host, candidate))
        except OSError as error:
            if error.errno not in _ADDRESS_IN_USE:
                raise
            last = error
    if last is None:
        raise OSError(f"no free port in {default}..{default + attempts - 1}")
    raise last
