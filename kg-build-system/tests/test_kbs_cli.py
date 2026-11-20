from __future__ import annotations

import json
from pathlib import Path

import pytest

from kg_build_system.cli import main as kbs_main


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    return root


def test_top_level_help_names_the_groups(capsys) -> None:
    with pytest.raises(SystemExit) as stopped:
        kbs_main(["--help"])
    assert stopped.value.code == 0
    out = " ".join(capsys.readouterr().out.split())
    assert "iteration finding, proposal, revision, evaluation" in out


def test_each_noun_lists_its_verbs(capsys) -> None:
    expected = {
        "finding": {"add", "list", "withdraw"},
        "proposal": {"create", "list", "withdraw"},
        "revision": {"record", "list", "compare"},
        "evaluation": {"run", "list"},
    }
    for noun, verbs in expected.items():
        with pytest.raises(SystemExit) as stopped:
            kbs_main([noun, "--help"])
        assert stopped.value.code == 0
        out = capsys.readouterr().out
        assert f"usage: kbs {noun}" in out
        for verb in verbs:
            assert verb in out


def test_the_old_notebook_surface_is_gone(capsys) -> None:
    with pytest.raises(SystemExit) as stopped:
        kbs_main(["notebook", "--help"])
    assert stopped.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_a_finding_is_added_listed_and_withdrawn(tmp_path: Path, capsys) -> None:
    root = _project(tmp_path)
    assert (
        kbs_main(
            [
                "finding", "add",
                "--project", str(root),
                "--observation", "One site is hot.",
                "--evidence", "row 42",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert kbs_main(["finding", "list", "--project", str(root), "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)["rows"]
    assert rows[0]["observation"] == "One site is hot."
    assert rows[0]["withdrawn"] is False
    assert (
        kbs_main(
            [
                "finding", "withdraw",
                "--project", str(root),
                "--id", rows[0]["code"],
                "--reason", "superseded",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert kbs_main(["finding", "list", "--project", str(root), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["rows"][0]["withdrawn"] is True


def test_a_proposal_is_created_listed_and_withdrawn(tmp_path: Path, capsys) -> None:
    root = _project(tmp_path)
    assert (
        kbs_main(
            [
                "proposal", "create",
                "--project", str(root),
                "--subject", "edge:associated_with",
                "--rationale", "Add a semantics frame.",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert kbs_main(["proposal", "list", "--project", str(root), "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)["rows"]
    assert rows and rows[0]["code"].startswith("P")
    assert rows[0]["based_revision"] == "BEGIN-1"
    assert (
        kbs_main(
            [
                "proposal", "withdraw",
                "--project", str(root),
                "--id", rows[0]["code"],
                "--reason", "not now",
            ]
        )
        == 0
    )


def test_a_revision_records_the_proposals_it_implements(
    tmp_path: Path, capsys
) -> None:
    root = _project(tmp_path)
    assert (
        kbs_main(
            [
                "proposal", "create",
                "--project", str(root),
                "--subject", "edge:associated_with",
                "--rationale", "Add a semantics frame.",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert (
        kbs_main(
            [
                "revision", "record",
                "--project", str(root),
                "--based-proposal", "P-1",
                "--message", "First revision",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert kbs_main(["revision", "list", "--project", str(root), "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)["rows"]
    assert rows[0]["code"] == "B-1"
    assert rows[0]["based_on"] == "P-1"


def test_an_evaluation_run_names_the_revision_it_measured(
    tmp_path: Path, capsys
) -> None:
    root = _project(tmp_path)
    assert (
        kbs_main(
            [
                "proposal", "create",
                "--project", str(root),
                "--subject", "edge:associated_with",
                "--rationale", "Add a semantics frame.",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert (
        kbs_main(
            [
                "revision", "record",
                "--project", str(root),
                "--based-proposal", "P-1",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert (
        kbs_main(
            [
                "evaluation", "run",
                "--project", str(root),
                "--revision", "B-1",
                "--result", '{"status": "passed"}',
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert kbs_main(["evaluation", "list", "--project", str(root), "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)["rows"]
    assert rows[0]["revision"] == "B-1"
    assert rows[0]["protocol"] == "E-1"


def test_a_missing_proposal_reports_an_error(tmp_path: Path, capsys) -> None:
    root = _project(tmp_path)
    assert (
        kbs_main(
            ["proposal", "withdraw", "--project", str(root), "--id", "P-9",
             "--reason", "none"]
        )
        == 1
    )
    streams = capsys.readouterr()
    assert streams.out == ""
    assert "proposal P-9 not found" in streams.err


def test_up_is_the_shortcut_for_both_surfaces(capsys) -> None:
    with pytest.raises(SystemExit) as stopped:
        kbs_main(["up", "--help"])
    assert stopped.value.code == 0
    out = capsys.readouterr().out
    assert "usage: kbs up" in out
    assert "--snapshot" in out
    assert "--no-open" in out
