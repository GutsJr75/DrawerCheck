"""Check the implemented commands and their plain-English failures."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from drawercheck import db, errors
from drawercheck.cli import main
from drawercheck.csv_contract import CSV_HEADERS


@pytest.mark.parametrize("argv", [["--help"], []])
def test_help_returns_success(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """Help is available directly through main() without terminating the test."""
    assert main(argv) == 0
    output = capsys.readouterr()
    assert "usage: drawercheck" in output.out
    assert "Demo Store #001" in output.out
    assert "init-db" in output.out
    assert "demo-data" in output.out
    assert "import" in output.out
    assert output.err == ""


def test_unknown_argument_returns_one(capsys: pytest.CaptureFixture[str]) -> None:
    """Invalid arguments use the shared error, stderr, and exit code 1."""
    assert main(["--unknown"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err.strip() == errors.INVALID_ARGUMENTS.format(
        detail="unrecognized arguments: --unknown"
    )
    assert "Traceback" not in output.err


@pytest.mark.parametrize(
    "command", ["init-db", "demo-data", "import", "reconcile", "explain"]
)
def test_command_help(command: str, capsys: pytest.CaptureFixture[str]) -> None:
    """Each implemented subcommand offers help without running the command."""
    assert main([command, "--help"]) == 0
    assert f"usage: drawercheck {command}" in capsys.readouterr().out


def test_init_db_creates_tables_at_the_requested_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The init command creates a usable database and reports its path."""
    path = tmp_path / "demo.db"
    assert main(["init-db", "--db", str(path)]) == 0
    assert errors.DATABASE_INITIALIZED.format(path=path) in capsys.readouterr().out
    with closing(db.connect(path)) as con:
        tables = con.execute(
            "SELECT name FROM sqlite_schema WHERE type = 'table'"
        ).fetchall()
        assert len(tables) == 10


def test_default_database_path_is_local(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Commands use drawercheck.db in the current working directory by default."""
    monkeypatch.chdir(tmp_path)
    assert main(["init-db"]) == 0
    assert (tmp_path / "drawercheck.db").exists()


def test_non_sqlite_file_is_explained_without_overwriting(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A mistaken database path reports the real failure without a traceback."""
    path = tmp_path / "demo.db"
    content = "Demo text file, not a SQLite database."
    path.write_text(content)
    assert main(["init-db", "--db", str(path)]) == 1
    output = capsys.readouterr()
    assert "Cannot use the database" in output.err
    assert "not a database" in output.err
    assert "Traceback" not in output.err
    assert path.read_text() == content


def test_demo_and_repeated_import_commands(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The implemented workflow generates data, imports it, then reports skips."""
    directory, path = tmp_path / "inputs", tmp_path / "demo.db"
    assert (
        main(["demo-data", "--out", str(directory), "--days", "3", "--seed", "42"]) == 0
    )
    assert "Demo Store #001" in capsys.readouterr().out
    arguments = ["import", "--dir", str(directory), "--db", str(path)]
    assert main(arguments) == 0
    assert "shifts.csv: imported 6 rows." in capsys.readouterr().out
    assert main(arguments) == 0
    assert capsys.readouterr().out.count("already imported; skipped.") == 7


def test_header_only_import_is_reported(
    csv_directory: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Zero-row imports say zero rows instead of implying a missing file."""
    for name, headers in CSV_HEADERS.items():
        (csv_directory / name).write_text(",".join(headers) + "\n")
    assert (
        main(["import", "--dir", str(csv_directory), "--db", str(tmp_path / "demo.db")])
        == 0
    )
    assert capsys.readouterr().out.count("imported 0 rows.") == 7


def test_import_failure_reports_location_without_success_messages(
    csv_directory: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A failed transaction prints only its file/line/column error."""
    (csv_directory / "bank_deposits.csv").write_text(
        "deposit_date,amount,reference\n2026-09-01,1.234,DEMO-INVALID\n"
    )
    assert (
        main(["import", "--dir", str(csv_directory), "--db", str(tmp_path / "demo.db")])
        == 1
    )
    output = capsys.readouterr()
    assert output.out == ""
    assert "bank_deposits.csv: line 2, column amount:" in output.err
    assert "exactly two decimal places" in output.err
    assert "Traceback" not in output.err


def test_missing_import_file_is_explained(
    csv_directory: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing file gives its path and a short error instead of a traceback."""
    (csv_directory / "cashiers.csv").unlink()
    assert (
        main(["import", "--dir", str(csv_directory), "--db", str(tmp_path / "demo.db")])
        == 1
    )
    output = capsys.readouterr()
    assert "Cannot access" in output.err
    assert "cashiers.csv" in output.err
    assert "Traceback" not in output.err


def test_unwritable_demo_destination_is_explained(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A regular file cannot act as a destination folder, on any platform."""
    path = tmp_path / "not-a-directory"
    path.write_text("Demo placeholder.")
    assert main(["demo-data", "--out", str(path)]) == 1
    output = capsys.readouterr()
    assert "Cannot access" in output.err
    assert str(path) in output.err
    assert "Traceback" not in output.err


@pytest.mark.parametrize(
    "arguments",
    [["import"], ["demo-data", "--days", "no"], ["demo-data", "--days", "0"]],
)
def test_bad_arguments_return_one(
    arguments: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing arguments and invalid values use the project's error exit code."""
    assert main(arguments) == 1
    output = capsys.readouterr()
    assert output.err
    assert "Traceback" not in output.err


def test_old_sqlite_is_explained_at_command_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An unsupported SQLite installation is rejected before opening a database."""
    path = tmp_path / "demo.db"
    monkeypatch.setattr(sqlite3, "sqlite_version_info", (3, 36, 0))
    assert main(["init-db", "--db", str(path)]) == 1
    assert capsys.readouterr().err.strip() == errors.SQLITE_TOO_OLD.format(
        version="3.36.0"
    )
    assert not path.exists()


@pytest.mark.parametrize(
    ("detail", "expected"),
    [
        ("database is locked", errors.DATABASE_LOCKED),
        ("attempt to write a readonly database", errors.DATABASE_READ_ONLY),
        (
            "unable to open database file",
            errors.DATABASE_ERROR.format(detail="unable to open database file"),
        ),
    ],
)
def test_sqlite_operational_failures_are_translated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    detail: str,
    expected: str,
) -> None:
    """Platform-dependent SQLite failures produce stable documented messages."""

    def fail(path: str | Path) -> None:
        raise sqlite3.OperationalError(detail)

    monkeypatch.setattr(db, "initialize", fail)
    assert main(["init-db", "--db", str(tmp_path / "demo.db")]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err.strip() == expected
    assert "Traceback" not in output.err


def test_reconcile_and_explain_workflow(
    demo_database: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The installed command interface explains S1 with its full math and saved flags."""
    assert main(["reconcile", "--db", str(demo_database)]) == 0
    assert (
        "Reconciled 60 shifts from 2026-09-01 to 2026-09-30; saved 12 review flags."
        in capsys.readouterr().out
    )
    assert main(["explain", "2026-09-03-R1", "--db", str(demo_database)]) == 0
    output = capsys.readouterr()
    for expected in (
        "DEMO DATA ONLY",
        "Opening float: $200.00",
        "Cash sales: $1,250.75",
        "Cash refunds: $12.00",
        "Paid-outs: $20.00",
        "Safe drops: $900.00",
        "Expected drawer: $518.75",
        "Counted drawer: $498.75",
        "Variance = counted - expected: -$20.00",
        "Shift deposit contribution: $1,198.75",
        "R01_VARIANCE",
        "R02_SINGLE_DENOMINATION",
    ):
        assert expected in output.out
    assert "R05_MISSING_VERIFIER_OR_NOTE" not in output.out
    assert output.err == ""


def test_missing_config_notice_and_saved_policy(
    demo_database: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Defaults are announced once, and explain ignores subsequent config-file changes."""
    path = tmp_path / "policy.toml"
    assert main(["reconcile", "--db", str(demo_database), "--config", str(path)]) == 0
    assert capsys.readouterr().out.count("using built-in example defaults") == 1
    path.write_text("This is no longer valid TOML.")
    assert main(["explain", "2026-09-03-R1", "--db", str(demo_database)]) == 0
    output = capsys.readouterr()
    assert "Review threshold: $12.50" in output.out
    assert "not found" not in output.out


@pytest.mark.parametrize(
    ("shift_code", "text"),
    [
        ("2026-09-01-R1", "No review flags for this shift."),
        ("2026-09-25-R1", "Counted drawer: unknown"),
        ("2026-09-27-R2", "Closing time is not after opening time"),
    ],
)
def test_clean_and_incomplete_explanations(
    demo_database: Path, capsys: pytest.CaptureFixture[str], shift_code: str, text: str
) -> None:
    """Clean, missing-count, and invalid-time shifts all have readable explanations."""
    assert main(["reconcile", "--db", str(demo_database)]) == 0
    capsys.readouterr()
    assert main(["explain", shift_code, "--db", str(demo_database)]) == 0
    assert text in capsys.readouterr().out


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        (["explain", "unknown-demo-shift"], "Unknown shift code"),
        (["explain", "2026-09-03-R1"], errors.NOT_RECONCILED),
        (["reconcile", "--from", "2026-02-30"], "Invalid --from date"),
        (
            ["reconcile", "--from", "2026-09-04", "--to", "2026-09-03"],
            errors.REVERSED_RANGE,
        ),
    ],
)
def test_m3_cli_errors(
    demo_database: Path,
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
    expected: str,
) -> None:
    """Expected M3 failures use exit 1 and short central errors without tracebacks."""
    assert main([*arguments, "--db", str(demo_database)]) == 1
    output = capsys.readouterr()
    assert expected in output.err
    assert "Traceback" not in output.err


def test_invalid_existing_config_fails_without_saving(
    demo_database: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A bad config does not silently use defaults or save any results."""
    path = tmp_path / "invalid.toml"
    path.write_text("[tolerance]\nwarn_cents = true\n")
    assert main(["reconcile", "--db", str(demo_database), "--config", str(path)]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "nonnegative whole number" in output.err
    with closing(db.connect(demo_database)) as con:
        assert con.execute("SELECT COUNT(*) FROM reconciled_dates").fetchone()[0] == 0


def test_reconcile_and_explain_use_local_default_paths(
    demo_database: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both new commands work with the documented local database and missing config."""
    path = tmp_path / "drawercheck.db"
    demo_database.rename(path)
    monkeypatch.chdir(tmp_path)
    assert main(["reconcile"]) == 0
    assert main(["explain", "2026-09-03-R1"]) == 0
