"""Verify shared reports, saved-policy boundaries, escaping, and safe output files."""

import csv
import json
import os
import sqlite3
import stat
import subprocess
import sys
from contextlib import closing
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from html import escape
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path

import pytest

from drawercheck import db, errors
from drawercheck.cli import main
from drawercheck.config import Config
from drawercheck.importer import import_directory
from drawercheck.reconcile import reconcile
from drawercheck.reports import (
    ReportData,
    csv_out,
    html,
    load_report,
    text,
    write_report,
)

_GENERATED_AT = datetime(2026, 10, 22, 12, 0, tzinfo=UTC)


@pytest.fixture
def report(demo_database: Path) -> ReportData:
    """Provide the complete month using a fixed generation time."""
    reconcile(demo_database, Config())
    return load_report(demo_database, generated_at=_GENERATED_AT)


@pytest.fixture
def small_database(tmp_path: Path) -> Path:
    """Provide known small amounts plus missing POS and open-shift cases."""
    path = tmp_path / "small.db"
    db.initialize(path)
    with closing(db.connect(path)) as con:
        with con:
            con.executemany(
                "INSERT INTO cashiers VALUES (?, ?)",
                [("cashier_A", "Demo A"), ("cashier_B", "Demo B")],
            )
            con.executemany(
                "INSERT INTO registers VALUES (?, ?)",
                [("R1", "Demo R1"), ("R2", "Demo R2")],
            )
            con.executemany(
                """INSERT INTO shifts (id, shift_code, business_date, register_id, cashier_id, opened_at, closed_at, opening_float_cents)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        1,
                        "2026-09-01-R1",
                        "2026-09-01",
                        "R1",
                        "cashier_A",
                        "2026-09-01T08:00:00",
                        "2026-09-01T16:00:00",
                        0,
                    ),
                    (
                        2,
                        "2026-09-01-R2",
                        "2026-09-01",
                        "R2",
                        "cashier_B",
                        "2026-09-01T08:00:00",
                        "2026-09-01T16:00:00",
                        0,
                    ),
                    (
                        3,
                        "2026-09-02-R1",
                        "2026-09-02",
                        "R1",
                        "cashier_A",
                        "2026-09-02T08:00:00",
                        "2026-09-02T16:00:00",
                        0,
                    ),
                    (
                        4,
                        "2026-09-02-R2",
                        "2026-09-02",
                        "R2",
                        "cashier_B",
                        "2026-09-02T08:00:00",
                        None,
                        0,
                    ),
                ],
            )
            con.executemany(
                "INSERT INTO pos_totals VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [(1, 10000, 900000, 0, 0, 0, 0, 0), (2, 20000, 0, 0, 0, 0, 0, 0)],
            )
            con.executemany(
                "INSERT INTO cash_counts VALUES (?, ?, ?)",
                [(1, 1, 10025), (2, 1, 19500), (3, 1, 0)],
            )
    reconcile(
        path,
        replace(
            Config(),
            review_percent_of_cash_sales=Decimal(100),
            retained_float_per_register_cents=0,
        ),
    )
    return path


def test_full_month_summary_and_saved_flags(report: ReportData) -> None:
    """Reports include all required M5 flags and retain the exact shift amounts."""
    assert (
        len(report.shifts) == 60 and len(report.flags) == 18 and len(report.days) == 30
    )
    assert sum(day.balanced for day in report.days) == 52
    assert sum(day.short for day in report.days) == 6
    assert sum(day.over for day in report.days) == 1
    assert sum(day.incomplete for day in report.days) == 1
    assert (
        sum(day.info for day in report.days),
        sum(day.warn for day in report.days),
        sum(day.review for day in report.days),
    ) == (4, 7, 7)
    assert (
        next(
            day for day in report.days if day.business_date == "2026-09-25"
        ).expected_deposit_cents
        is None
    )
    assert report.generated_at == "2026-10-22T12:00:00+00:00"
    for render in (text.render, html.render):
        output = render(report)
        assert (
            "DEMO DATA ONLY" in output and "simplified bank-deposit matching" in output
        )
        assert "arrive in M5" not in output
        assert "$518.75" in output and "$498.75" in output and "-$20.00" in output


def test_known_variances_missing_cash_and_saved_threshold(small_database: Path) -> None:
    """Small exact differences are retained in totals while unknown/open amounts stay excluded."""
    data = load_report(small_database, generated_at=_GENERATED_AT)
    day1, day2 = data.days
    assert (
        day1.balanced,
        day1.short,
        day1.warn,
        day1.info,
        day1.expected_deposit_cents,
    ) == (1, 1, 1, 1, 29525)
    assert (day2.incomplete, day2.open, day2.expected_deposit_cents) == (1, 1, None)
    first, second = data.cashiers
    assert (
        first.known,
        first.incomplete,
        first.over_cents,
        first.short_cents,
        first.net_cents,
    ) == (1, 1, 25, 0, 25)
    assert (
        second.known,
        second.open,
        second.over_cents,
        second.short_cents,
        second.net_cents,
    ) == (1, 1, 0, 500, -500)
    assert data.config.review_percent_of_cash_sales == Decimal(100)
    unknown = load_report(small_database, date="2026-09-02", generated_at=_GENERATED_AT)
    assert all(cashier.known == 0 for cashier in unknown.cashiers)
    for render in (text.render, html.render):
        assert "unknown" in render(unknown)
    assert data.shifts[0].variance_cents == 25 and data.shifts[0].status == "balanced"


def test_report_does_not_mutate_results_or_read_current_config(
    demo_database: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Export reads a consistent saved policy without touching flags or completion timestamps."""
    reconcile(demo_database, Config())
    with closing(db.connect(demo_database)) as con:
        before = (
            db.load_flags(con, "2026-09-01", "2026-09-30"),
            tuple(
                tuple(row)
                for row in con.execute(
                    "SELECT * FROM reconciled_dates ORDER BY business_date"
                )
            ),
        )
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.toml").write_text("Invalid current config.")
    load_report(demo_database, generated_at=_GENERATED_AT)
    with closing(db.connect(demo_database)) as con:
        after = (
            db.load_flags(con, "2026-09-01", "2026-09-30"),
            tuple(
                tuple(row)
                for row in con.execute(
                    "SELECT * FROM reconciled_dates ORDER BY business_date"
                )
            ),
        )
    assert after == before


def test_report_requires_every_selected_date_to_be_completed(
    demo_database: Path,
) -> None:
    """A partly reconciled range cannot make unchecked dates look clean."""
    with pytest.raises(
        errors.ReconciliationError, match="Run `drawercheck reconcile` first"
    ):
        load_report(demo_database)
    reconcile(demo_database, Config(), "2026-09-01", "2026-09-01")
    clean = load_report(demo_database, date="2026-09-01")
    assert clean.flags == ()
    assert "No review flags in this completed range." in text.render(clean)
    assert len(list(csv.reader(StringIO(csv_out.render(clean))))) == 1
    with pytest.raises(
        errors.ReconciliationError, match="Run `drawercheck reconcile` first"
    ):
        load_report(demo_database)


@pytest.mark.parametrize(
    ("completed_to", "from_date", "missing_date"),
    [
        (None, None, "2026-09-01"),
        ("2026-09-10", None, "2026-09-11"),
        ("2026-09-10", "2026-09-15", "2026-09-15"),
    ],
)
def test_unreconciled_report_names_first_missing_date(
    demo_database: Path,
    capsys: pytest.CaptureFixture[str],
    completed_to: str | None,
    from_date: str | None,
    missing_date: str,
) -> None:
    """Missing-date guidance identifies the first unchecked date in the selected range."""
    if completed_to is not None:
        reconcile(demo_database, Config(), "2026-09-01", completed_to)
    arguments = ["report", "--db", str(demo_database)]
    if from_date is not None:
        arguments.extend(["--from", from_date])
    assert main(arguments) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err.strip() == (
        errors.NOT_RECONCILED + f" First unreconciled date: {missing_date}."
    )


@pytest.mark.parametrize("old", [True, False])
def test_stale_or_mixed_snapshots_are_rejected(demo_database: Path, old: bool) -> None:
    """Reports never mix completed dates from different settings or an earlier policy."""
    reconcile(demo_database, Config())
    snapshot = json.loads(Config().snapshot())
    if old:
        snapshot.pop("policy_version")
    else:
        snapshot["warn_cents"] = 600
    with closing(db.connect(demo_database)) as con:
        with con:
            if old:
                con.execute(
                    "UPDATE reconciled_dates SET config_json = ?",
                    (json.dumps(snapshot, sort_keys=True),),
                )
            else:
                con.execute(
                    "UPDATE reconciled_dates SET config_json = ? WHERE business_date = ?",
                    (json.dumps(snapshot, sort_keys=True), "2026-09-01"),
                )
    with pytest.raises(errors.ReconciliationError):
        load_report(demo_database)


@pytest.mark.parametrize(
    "arguments",
    [
        {"date": "2026-09-01", "from_date": "2026-09-01"},
        {"date": "2026-09-01", "to_date": "2026-09-02"},
        {"from_date": "20260901"},
        {"date": "2026-02-30"},
        {"from_date": "2026-09-02", "to_date": "2026-09-01"},
        {"from_date": "2026-10-15"},
        {"to_date": "2026-08-01"},
    ],
)
def test_invalid_report_ranges(demo_database: Path, arguments: dict) -> None:
    """Reports enforce exact dates, mutually exclusive selectors, and nonempty ranges."""
    with pytest.raises(errors.DrawerCheckError):
        load_report(demo_database, **arguments)


def test_missing_database_stays_absent(tmp_path: Path) -> None:
    """A report typo must not create a new empty database."""
    path = tmp_path / "absent.db"
    with pytest.raises(errors.ReconciliationError):
        load_report(path)
    assert not path.exists()


@pytest.mark.parametrize("fail", [False, True])
def test_report_connection_is_closed(
    demo_database: Path, monkeypatch: pytest.MonkeyPatch, fail: bool
) -> None:
    """Both a completed report and an unchecked-data error release the database."""
    if not fail:
        reconcile(demo_database, Config())
    connect = db.connect
    connections = []

    def track(path: str | Path) -> sqlite3.Connection:
        con = connect(path)
        connections.append(con)
        return con

    monkeypatch.setattr(db, "connect", track)
    if fail:
        with pytest.raises(errors.ReconciliationError):
            load_report(demo_database)
    else:
        load_report(demo_database)
    for con in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            con.execute("SELECT 1")


def test_all_dynamic_html_values_are_escaped(report: ReportData) -> None:
    """Hostile-looking names, identifiers, dates, and messages remain plain text."""
    payload = '"><script>alert("demo")</script>&\''
    flag = replace(
        report.flags[0], message=payload, business_date=payload, rule_code=payload
    )
    shift = replace(
        report.shifts[0],
        shift=replace(report.shifts[0].shift, shift_code=payload, cashier_id=payload),
    )
    data = replace(
        report,
        from_date=payload,
        to_date=payload,
        generated_at=payload,
        flags=(flag,),
        shifts=(shift, *report.shifts[1:]),
        cashiers=(
            replace(report.cashiers[0], cashier_id=payload, display_name=payload),
        ),
    )
    output = html.render(data)
    assert payload not in output
    assert escape(payload, quote=True) in output
    assert "<script" not in output


class _HTMLInventory(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))


def test_html_is_offline_semantic_and_theme_aware(report: ReportData) -> None:
    """Exports have no executable/external resources and expose real table structure."""
    output = html.render(report)
    inventory = _HTMLInventory()
    inventory.feed(output)
    assert not any(
        tag in {"script", "link", "iframe", "img", "object", "embed"}
        for tag, _ in inventory.tags
    )
    assert all(
        attributes.get("href", "#").startswith("#") for _, attributes in inventory.tags
    )
    assert sum(tag == "table" for tag, _ in inventory.tags) == 4
    assert sum(tag == "caption" for tag, _ in inventory.tags) == 4
    assert all(
        attributes.get("scope") == "col"
        for tag, attributes in inventory.tags
        if tag == "th"
    )
    assert any(
        tag == "meta" and attrs.get("name") == "viewport"
        for tag, attrs in inventory.tags
    )
    assert "prefers-color-scheme:dark" in output and "@media print" in output
    assert "url(" not in output and "@import" not in output


def test_generated_stylesheet_starts_with_valid_root_rule(report: ReportData) -> None:
    """The base theme variables belong to a valid top-level root selector."""
    stylesheet = html.render(report).split("<style>", 1)[1].split("</style>", 1)[0]
    assert stylesheet.lstrip().startswith(":root {")


def test_demo_banner_has_fallback_background(report: ReportData) -> None:
    """The white demo warning retains a dark background if its variable is absent."""
    stylesheet = html.render(report).split("<style>", 1)[1].split("</style>", 1)[0]
    banner = stylesheet.split(".demo {", 1)[1].split("}", 1)[0]
    assert "color:#fff" in banner
    assert "background:var(--head, #143c4a)" in banner


def test_text_cannot_fake_lines_or_control_terminal(report: ReportData) -> None:
    """Legacy controls and multiline display names are made visible in text exports."""
    value = "Demo\x1b[8m\nFAKE RESULT\tName"
    data = replace(
        report,
        flags=(replace(report.flags[0], message=value),),
        cashiers=(replace(report.cashiers[0], display_name=value),),
    )
    output = text.render(data)
    assert "\x1b" not in output and "\t" not in output
    assert "\\x1b[8m\\nFAKE RESULT\\tName" in output
    assert "FAKE RESULT" not in output.splitlines()


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@", "\t", "\r"])
@pytest.mark.parametrize(
    "column", ["date", "shift_code", "rule_code", "severity", "message"]
)
def test_csv_protects_each_export_column(
    report: ReportData, prefix: str, column: str
) -> None:
    """No flag field can bypass the shared spreadsheet protection."""
    value = prefix + 'DEMO,"quoted"\nnext'
    flag = report.flags[0]
    shifts = report.shifts
    if column == "shift_code":
        shifts = tuple(
            replace(result, shift=replace(result.shift, shift_code=value))
            if result.shift.id == flag.shift_id
            else result
            for result in shifts
        )
    else:
        flag = replace(flag, **{"business_date" if column == "date" else column: value})
    output = csv_out.render(replace(report, flags=(flag,), shifts=shifts))
    row = next(csv.DictReader(StringIO(output, newline="")))
    assert row[column] == "'" + value


def test_csv_headers_also_use_protection(
    report: ReportData, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Headers and every data cell pass through the same safety function."""
    original = csv_out.sanitize_cell
    seen = []

    def track(value: str) -> str:
        seen.append(value)
        return original(value)

    monkeypatch.setattr(csv_out, "sanitize_cell", track)
    csv_out.render(report)
    assert seen[:5] == ["date", "shift_code", "rule_code", "severity", "message"]
    assert len(seen) == 5 * (len(report.flags) + 1)


@pytest.mark.parametrize("kind", ["text", "html", "csv"])
def test_report_cli_stdout_and_file(
    demo_database: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], kind: str
) -> None:
    """Each format works through the public command and writes complete UTF-8 output."""
    reconcile(demo_database, Config())
    arguments = [
        "report",
        "--db",
        str(demo_database),
        "--date",
        "2026-09-03",
        "--format",
        kind,
    ]
    assert main(arguments) == 0
    output = capsys.readouterr()
    assert output.err == ""
    assert "R01_VARIANCE" in output.out
    path = tmp_path / ("report." + kind)
    assert main([*arguments, "--out", str(path)]) == 0
    assert "report written:" in capsys.readouterr().out
    assert "R01_VARIANCE" in path.read_text()
    assert not list(tmp_path.glob(".drawercheck-*.tmp"))


def test_report_before_reconciliation_is_cli_error(
    demo_database: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Unchecked data never produces a false clean report."""
    assert main(["report", "--db", str(demo_database)]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err.strip() == (
        errors.NOT_RECONCILED + " First unreconciled date: 2026-09-01."
    )


@pytest.mark.parametrize(
    "selector",
    [
        ["--date", "2026-09-01", "--from", "2026-09-01"],
        ["--date", "2026-09-01", "--to", "2026-09-02"],
        ["--format", "pdf"],
    ],
)
def test_bad_report_cli_arguments(
    demo_database: Path, capsys: pytest.CaptureFixture[str], selector: list[str]
) -> None:
    """Invalid selectors and formats return a concise usage error."""
    assert main(["report", "--db", str(demo_database), *selector]) == 1
    assert "Traceback" not in capsys.readouterr().err


@pytest.mark.parametrize("suffix", ["", "-journal", "-wal", "-shm"])
def test_output_cannot_replace_database_or_sidecar(
    demo_database: Path, suffix: str
) -> None:
    """A report path cannot overwrite SQLite storage."""
    before = demo_database.read_bytes()
    with pytest.raises(errors.UsageError):
        write_report(str(demo_database) + suffix, "Demo report", demo_database)
    assert demo_database.read_bytes() == before


@pytest.mark.parametrize("alias", ["symlink", "hardlink"])
def test_database_aliases_are_also_protected(
    demo_database: Path, tmp_path: Path, alias: str
) -> None:
    """Aliases cannot bypass output-file protection."""
    path = tmp_path / "alias.txt"
    if alias == "symlink":
        path.symlink_to(demo_database)
    else:
        path.hardlink_to(demo_database)
    with pytest.raises(errors.UsageError):
        write_report(path, "Demo report", demo_database)


def test_failed_write_preserves_existing_output_and_cleans_temp(
    demo_database: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A late filesystem failure leaves the earlier report intact and removes partial output."""
    from drawercheck import reports

    path = tmp_path / "report.html"
    path.write_text("Previous demo report.")

    def fail(source: str | Path, target: str | Path) -> None:
        raise PermissionError("Demo write failure.")

    monkeypatch.setattr(reports.os, "replace", fail)
    with pytest.raises(errors.DrawerCheckError, match="Cannot write report"):
        write_report(path, "New demo report.", demo_database)
    assert path.read_text() == "Previous demo report."
    assert not list(tmp_path.glob(".drawercheck-*.tmp"))


@pytest.mark.skipif(os.name != "posix", reason="POSIX file permission semantics")
@pytest.mark.parametrize(
    ("mask", "existing_mode", "expected_mode"),
    [
        (0o022, None, 0o644),
        (0o077, None, 0o600),
        (0o002, None, 0o664),
        (0o077, 0o640, 0o640),
        (0o022, 0o600, 0o600),
    ],
)
def test_output_permissions_respect_umask_and_existing_mode(
    tmp_path: Path, mask: int, existing_mode: int | None, expected_mode: int
) -> None:
    """New exports use the caller's umask while replacements keep prior permissions."""
    path = tmp_path / "report.html"
    if existing_mode is not None:
        path.write_text("Previous report.")
        path.chmod(existing_mode)
    # Change the process-wide umask only in an isolated child process.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import os, sys; from drawercheck.reports import write_report; "
            "os.umask(int(sys.argv[1])); "
            "write_report(sys.argv[2], 'Updated report.', sys.argv[3]); "
            "assert os.umask(int(sys.argv[1])) == int(sys.argv[1])",
            str(mask),
            str(path),
            str(tmp_path / "unused.db"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert path.read_text() == "Updated report."
    assert stat.S_IMODE(path.stat().st_mode) == expected_mode
    assert not list(tmp_path.glob(".drawercheck-*.tmp"))


def test_permission_failure_preserves_existing_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failure to retain permissions must not replace an earlier complete report."""
    path = tmp_path / "report.html"
    path.write_text("Previous report.")

    def fail(*args: object, **kwargs: object) -> None:
        raise PermissionError("Demo permission failure.")

    monkeypatch.setattr(os, "chmod", fail)
    with pytest.raises(errors.DrawerCheckError, match="Cannot write report"):
        write_report(path, "Updated report.", tmp_path / "unused.db")
    assert path.read_text() == "Previous report."
    assert not list(tmp_path.glob(".drawercheck-*.tmp"))


def test_unwritable_report_path_is_a_cli_error(
    demo_database: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing output folder gives a report-specific error without a traceback."""
    reconcile(demo_database, Config())
    assert (
        main(
            [
                "report",
                "--db",
                str(demo_database),
                "--out",
                str(tmp_path / "missing" / "report.html"),
            ]
        )
        == 1
    )
    output = capsys.readouterr()
    assert "Cannot write report" in output.err and "Traceback" not in output.err


def test_missing_register_daily_flag_reaches_every_report(demo_database: Path) -> None:
    """A date-level lead survives export with no invented shift code or complete deposit."""
    with closing(db.connect(demo_database)) as con:
        with con:
            shift_id = con.execute(
                "SELECT id FROM shifts WHERE shift_code = ?", ("2026-09-02-R2",)
            ).fetchone()[0]
            con.execute("DELETE FROM pos_totals WHERE shift_id = ?", (shift_id,))
            con.execute("DELETE FROM cash_counts WHERE shift_id = ?", (shift_id,))
            con.execute("DELETE FROM safe_drops WHERE shift_id = ?", (shift_id,))
            con.execute("DELETE FROM shifts WHERE id = ?", (shift_id,))
    reconcile(demo_database, Config(), "2026-09-02", "2026-09-02")
    report = load_report(demo_database, date="2026-09-02", generated_at=_GENERATED_AT)
    assert len(report.flags) == 2 and all(
        flag.shift_id is None for flag in report.flags
    )
    assert {flag.rule_code for flag in report.flags} == {
        "R08_DEPOSIT",
        "R09_DATA_INTEGRITY",
    }
    assert report.days[0].review == 1 and report.days[0].expected_deposit_cents is None
    for render in (text.render, html.render):
        assert "R09_DATA_INTEGRITY" in render(report) and "unknown" in render(report)
    row = next(csv.DictReader(StringIO(csv_out.render(report))))
    assert row["shift_code"] == "" and row["date"] == "2026-09-02"


def test_new_import_invalidates_report_readiness(
    demo_database: Path, tmp_path: Path
) -> None:
    """New imported facts require another reconciliation before any export."""
    reconcile(demo_database, Config())
    inputs = tmp_path / "full-demo"
    (inputs / "cashiers.csv").write_text(
        "cashier_id,display_name\ncashier_extra,Demo Extra\n"
    )
    import_directory(inputs, demo_database)
    with pytest.raises(
        errors.ReconciliationError, match="Run `drawercheck reconcile` first"
    ):
        load_report(demo_database)
