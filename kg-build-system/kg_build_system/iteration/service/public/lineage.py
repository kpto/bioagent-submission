"""Read the ledger as the revision lineage a surface draws.

Example:
    ```python
    from kg_build_system.iteration import load_ledger, revision_lineage

    events = load_ledger(root)
    graph = revision_lineage(events)
    diff = revision_lineage(events, focus=graph["nodes"][-1]["id"])["focus"]
    ```
"""

from __future__ import annotations

from collections.abc import Sequence

from kg_build_system.kernel import JsonValue

from ...model.public.events import Event
from .._private.lineage import lineage


def revision_lineage(
    events: Sequence[Event], *, focus: str | None = None
) -> dict[str, JsonValue]:
    """The spine of builds, its collapsed counts and one focused diff.

    The result carries ``nodes``, ``edges``, ``details`` and ``summary``. With
    ``focus`` naming a revision id it also carries ``focus``: the graph of
    everything that revision depends on, with every path stopping at a revision
    (inclusive), the runs that measured it, and its external references.
    """

    return lineage(list(events), focus=focus)


__all__ = ["revision_lineage"]
