"""The project's relation operations: declared shape, grain and emitted SQL.

These run without data. They pin the contract between the operation's declared
output shape and the relation that publishes it, and they require the emitted
SQL to group - so a relation can neither drift from its operation nor silently
become a row-wise projection.
"""

from __future__ import annotations

from typing import Any

from kg_build_system.distribution.languages.data.service._private.shapes import (
    shape_fields,
)
from tests.support import create_pharos_blueprint

from pharos_kg.modules.row_operations import (
    LABEL_ROWS,
    PAIR_ROWS,
    PharosRowOperations,
)


class _Plan:
    def __init__(self, operation: str) -> None:
        self.operation = operation
        self.input = object()


class _Context:
    def relation_for(self, plan: Any) -> str:
        return "kg_rowsource_1"


def test_every_operation_emits_one_grouped_select() -> None:
    emitter = PharosRowOperations()
    for spec in (PAIR_ROWS, LABEL_ROWS):
        sql = emitter.emit(_Plan(spec.name), _Context())
        upper = sql.upper()
        assert "GROUP BY" in upper
        assert "SELECT" in upper
        assert "kg_rowsource_1" in sql
        for field in shape_fields(spec.output):
            assert f"AS {field.name}" in sql.replace("\n", " "), field.name


def test_an_unknown_operation_is_refused() -> None:
    emitter = PharosRowOperations()
    try:
        emitter.emit(_Plan("not_declared"), _Context())
    except ValueError as error:
        assert "not_declared" in str(error)
    else:  # pragma: no cover - the refusal is the contract
        raise AssertionError("an undeclared operation must be refused")


def test_published_relations_match_the_operation_output() -> None:
    blueprint = create_pharos_blueprint()
    declared = {
        relation.name: tuple(column.name for column in relation.columns)
        for relation in blueprint.data.derived_relations
    }
    for spec in (PAIR_ROWS, LABEL_ROWS):
        expected = tuple(field.name for field in shape_fields(spec.output))
        assert declared[spec.name] == expected, spec.name
