"""Reproduce the reviewed M3 failures through imports, commands, and saved results."""

import csv
import json
from contextlib import closing
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from drawercheck import db, errors
from drawercheck.cli import main
from drawercheck.config import Config, config_from_snapshot, load_config
from drawercheck.importer import import_directory
from drawercheck.reconcile import explain_shift, reconcile


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _write(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


@pytest.mark.parametrize(
    "percentage", ["1e999999", "1e-999999", "100.000001", "0.0000001", "1.23456789"]
)
def test_percentage_limits_apply_before_expansion(percentage: str) -> None:
    """Extreme or over-precise policies are rejected without constructing huge fractions."""
    with pytest.raises(errors.ConfigError):
        replace(Config(), review_percent_of_cash_sales=Decimal(percentage))


@pytest.mark.parametrize(
    "percentage", ["0.000001", "1.234567", "100", "100.0000000", "1.0000000"]
)
def test_valid_percentage_boundaries_remain_exact(percentage: str) -> None:
    """Redundant trailing zeros do not count as extra decimal places."""
    settings = replace(Config(), review_percent_of_cash_sales=Decimal(percentage))
    assert config_from_snapshot(settings.snapshot()) == settings
    assert len(settings.snapshot()) < 600


@pytest.mark.parametrize("lag", [32, 2**63 - 1])
def test_deposit_lag_has_a_practical_cap(lag: int) -> None:
    """Unusable calendar-day windows are rejected before M5 consumes them."""
    with pytest.raises(errors.ConfigError):
        replace(Config(), max_lag_days=lag)


@pytest.mark.parametrize("lag", [0, 31])
def test_deposit_lag_boundaries(lag: int) -> None:
    """Same-day matching and the maximum supported lag are valid policies."""
    assert replace(Config(), max_lag_days=lag).max_lag_days == lag


@pytest.mark.parametrize(
    "value",
    ["9" * 5000, "1e9999999999999999999", "1e999999", "1e-999999"],
    ids=["huge-integer", "unrepresentable-exponent", "huge-percent", "tiny-percent"],
)
def test_numeric_config_failures_are_clean_cli_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], value: str
) -> None:
    """Numeric parsing and range failures are translated before any database work."""
    policy = tmp_path / "policy.toml"
    policy.write_text("[tolerance]\nreview_percent_of_cash_sales = " + value + "\n")
    with pytest.raises(errors.ConfigError):
        load_config(policy)
    database = tmp_path / "absent.db"
    assert main(["reconcile", "--config", str(policy), "--db", str(database)]) == 1
    output = capsys.readouterr()
    assert "Config" in output.err or "config" in output.err
    if len(value) == 5000 or value == "1e9999999999999999999":
        assert "number" in output.err and "range" in output.err
        assert "UTF-8" not in output.err
    assert "Traceback" not in output.err
    assert not database.exists()


def test_missing_register_creates_daily_flag_and_unknown_deposit(
    csv_directory: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing R2 shift cannot make R1's share look like the whole day's deposit."""
    missing = "2026-09-02-R2"
    for name in ("shifts.csv", "pos_totals.csv", "safe_drops.csv", "cash_counts.csv"):
        path = csv_directory / name
        _write(path, [row for row in _read(path) if row["shift_code"] != missing])
    database = tmp_path / "demo.db"
    import_directory(csv_directory, database)
    for _ in range(2):
        run = reconcile(database, Config(), "2026-09-02", "2026-09-02")
        assert run.deposits[0].expected_cents is None
        with closing(db.connect(database)) as con:
            flags = db.load_flags(con, "2026-09-02", "2026-09-02")
        daily_flags = [
            flag
            for flag in flags
            if flag.shift_id is None and flag.rule_code == "R09_DATA_INTEGRITY"
        ]
        assert any(flag.evidence.get("issue") == "unexpected" for flag in flags)
        assert len(daily_flags) == 1
        flag = daily_flags[0]
        assert (flag.rule_code, flag.severity) == ("R09_DATA_INTEGRITY", "review")
        assert flag.evidence == {"issue": "missing_register_shift", "register_id": "R2"}
    assert explain_shift(database, "2026-09-02-R1").daily_deposit_cents is None
    assert (
        main(
            [
                "reconcile",
                "--from",
                "2026-09-02",
                "--to",
                "2026-09-02",
                "--db",
                str(database),
            ]
        )
        == 0
    )
    assert "saved 2 review flags." in capsys.readouterr().out
    assert main(["explain", "2026-09-02-R1", "--db", str(database)]) == 0
    output = capsys.readouterr().out
    assert "Expected daily deposit (all registers): unknown" in output
    assert "R09_DATA_INTEGRITY" in output and "R2" in output


@pytest.mark.parametrize(
    ("name", "column"),
    [
        ("cashiers.csv", "display_name"),
        ("registers.csv", "label"),
        ("shifts.csv", "variance_note"),
        ("safe_drops.csv", "bag_number"),
        ("bank_deposits.csv", "reference"),
    ],
)
@pytest.mark.parametrize(
    "control", ["\x1b[8m", "\x00", "\x7f", "\x9b", "\u202e", "\u2028"]
)
def test_unsafe_text_rejected_with_source_location(
    csv_directory: Path, tmp_path: Path, name: str, column: str, control: str
) -> None:
    """Unsafe terminal and invisible formatting characters cannot enter any free-text column."""
    path = csv_directory / name
    rows = _read(path)
    rows[0][column] = "Demo " + control + " value"
    _write(path, rows)
    database = tmp_path / "demo.db"
    with pytest.raises(errors.ImportValidationError) as caught:
        import_directory(csv_directory, database)
    assert (caught.value.file_name, caught.value.line_number, caught.value.column) == (
        name,
        2,
        column,
    )
    assert "control" in str(caught.value)
    if database.exists():
        with closing(db.connect(database)) as con:
            assert not con.execute(
                "SELECT name FROM sqlite_schema WHERE type = 'table'"
            ).fetchall()


@pytest.mark.parametrize(
    ("name", "column"),
    [
        ("cashiers.csv", "cashier_id"),
        ("registers.csv", "register_id"),
        ("shifts.csv", "shift_code"),
        ("shifts.csv", "cashier_id"),
        ("shifts.csv", "register_id"),
        ("shifts.csv", "verifier_id"),
        ("pos_totals.csv", "shift_code"),
        ("safe_drops.csv", "shift_code"),
        ("cash_counts.csv", "shift_code"),
    ],
)
@pytest.mark.parametrize(
    "padding", ["leading", "trailing", "unicode", "tab", "newline"]
)
def test_identifiers_are_rejected_instead_of_silently_trimmed(
    csv_directory: Path, tmp_path: Path, name: str, column: str, padding: str
) -> None:
    """IDs and references share the same unambiguous spelling requirements."""
    path = csv_directory / name
    rows = _read(path)
    value = rows[0][column]
    rows[0][column] = {
        "leading": " " + value,
        "trailing": value + " ",
        "unicode": "\u00a0" + value,
        "tab": value + "\tX",
        "newline": value + "\nX",
    }[padding]
    _write(path, rows)
    with pytest.raises(errors.ImportValidationError) as caught:
        import_directory(csv_directory, tmp_path / "demo.db")
    assert caught.value.column == column
    assert "IDs and shift codes" in str(caught.value)


def test_multiline_notes_stay_in_database_but_cannot_fake_output(
    csv_directory: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ordinary CSV multiline text is preserved and rendered as one terminal field."""
    path = csv_directory / "shifts.csv"
    rows = _read(path)
    note = "Demo recount.\r\n  No review flags for this shift.\tDemo"
    next(row for row in rows if row["shift_code"] == "2026-09-03-R1")[
        "variance_note"
    ] = note
    _write(path, rows)
    database = tmp_path / "demo.db"
    import_directory(csv_directory, database)
    reconcile(database, Config())
    assert explain_shift(database, "2026-09-03-R1").result.shift.variance_note == note
    assert main(["explain", "2026-09-03-R1", "--db", str(database)]) == 0
    output = capsys.readouterr().out
    assert "\r" not in output and "\t" not in output
    assert "\\r\\n  No review flags for this shift.\\tDemo" in output
    assert "  No review flags for this shift." not in output.splitlines()
    assert "[review] R01_VARIANCE" in output


def test_legacy_database_and_error_output_cannot_control_terminal(
    demo_database: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Output protection also covers old records and command-line error values."""
    with closing(db.connect(demo_database)) as con:
        with con:
            con.execute(
                "UPDATE shifts SET variance_note = ? WHERE shift_code = ?",
                ("Demo\x1b[8m\nFake line", "2026-09-03-R1"),
            )
    reconcile(demo_database, Config())
    assert main(["explain", "2026-09-03-R1", "--db", str(demo_database)]) == 0
    output = capsys.readouterr().out
    assert "\x1b" not in output
    assert "\\x1b[8m\\nFake line" in output
    assert main(["explain", "Unknown\x1b[8m\nFake", "--db", str(demo_database)]) == 1
    assert "\x1b" not in capsys.readouterr().err


@pytest.mark.parametrize(
    "options",
    [
        ["--from", "2026-10-15"],
        ["--to", "2026-08-15"],
        ["--from", "2026-10-15", "--to", "2026-10-16"],
    ],
)
def test_empty_ranges_report_no_matching_shifts_and_preserve_results(
    demo_database: Path, capsys: pytest.CaptureFixture[str], options: list[str]
) -> None:
    """An inferred endpoint cannot turn an empty selection into a misleading reversed-range error."""
    reconcile(demo_database, Config())
    with closing(db.connect(demo_database)) as con:
        before = db.load_flags(con, "2026-09-01", "2026-09-30")
    assert main(["reconcile", *options, "--db", str(demo_database)]) == 1
    output = capsys.readouterr()
    assert "No shifts match the requested date range." in output.err
    assert "on or before" not in output.err
    with closing(db.connect(demo_database)) as con:
        assert db.load_flags(con, "2026-09-01", "2026-09-30") == before
        assert con.execute("SELECT COUNT(*) FROM reconciled_dates").fetchone()[0] == 30


@pytest.mark.parametrize("arguments", [["reconcile"], ["explain", "2026-09-03-R1"]])
def test_tableless_database_suggests_import(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], arguments: list[str]
) -> None:
    """An existing empty database gets setup guidance rather than a permissions diagnosis."""
    database = tmp_path / "empty.db"
    database.touch()
    assert main([*arguments, "--db", str(database)]) == 1
    output = capsys.readouterr()
    assert "not initialized" in output.err
    assert "drawercheck import" in output.err
    assert "permissions" not in output.err


def test_old_m3_results_require_refresh_and_cannot_mix_policies(
    demo_database: Path,
) -> None:
    """The new register policy invalidates prior snapshots even when numeric settings match."""
    reconcile(demo_database, Config())
    snapshot = json.loads(Config().snapshot())
    snapshot.pop("policy_version")
    with closing(db.connect(demo_database)) as con:
        with con:
            con.execute(
                "UPDATE reconciled_dates SET config_json = ?",
                (json.dumps(snapshot, sort_keys=True),),
            )
    with pytest.raises(errors.ReconciliationError, match="earlier review policy"):
        explain_shift(demo_database, "2026-09-03-R1")
    reconcile(demo_database, Config(), "2026-09-03", "2026-09-03")
    with closing(db.connect(demo_database)) as con:
        dates = [
            row["business_date"]
            for row in con.execute("SELECT business_date FROM reconciled_dates")
        ]
        assert dates == ["2026-09-03"]
        assert {
            flag.business_date
            for flag in db.load_flags(con, "2026-09-01", "2026-09-30")
        } == {"2026-09-03"}
    assert explain_shift(demo_database, "2026-09-03-R1").result.variance_cents == -2000


def test_long_redundant_percentage_does_not_bloat_snapshot() -> None:
    """Allowed trailing zeros are removed before fixed decimal formatting."""
    percentage = Decimal("1." + "0" * 5000)
    settings = replace(Config(), review_percent_of_cash_sales=percentage)
    assert settings.snapshot() == Config().snapshot()


def test_empty_selection_with_new_policy_cannot_clear_completed_results(
    demo_database: Path,
) -> None:
    """A failed empty selection is not treated as a successful policy change."""
    reconcile(demo_database, Config())
    with closing(db.connect(demo_database)) as con:
        before = db.load_flags(con, "2026-09-01", "2026-09-30")
        snapshot = db.completion_snapshot(con, "2026-09-03")
    with pytest.raises(errors.ReconciliationError, match="No shifts match"):
        reconcile(
            demo_database,
            replace(Config(), max_lag_days=31),
            "2026-10-15",
            "2026-10-16",
        )
    with closing(db.connect(demo_database)) as con:
        assert db.load_flags(con, "2026-09-01", "2026-09-30") == before
        assert db.completion_snapshot(con, "2026-09-03") == snapshot
