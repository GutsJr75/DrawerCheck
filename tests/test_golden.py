"""Compare the complete fake-month result with independent documented expectations."""

import csv
import re
from contextlib import closing
from io import StringIO
from pathlib import Path

from drawercheck import db
from drawercheck.cli import main
from drawercheck.config import Config
from drawercheck.importer import import_directory
from drawercheck.reconcile import reconcile
from drawercheck.reports import csv_out, html, load_report, text

_EXPECTED = {
    ("2026-09-03", "2026-09-03-R1", "R01_VARIANCE", "review"),
    ("2026-09-03", "2026-09-03-R1", "R02_SINGLE_DENOMINATION", "info"),
    ("2026-09-08", "2026-09-08-R2", "R01_VARIANCE", "review"),
    ("2026-09-08", "2026-09-08-R2", "R05_MISSING_VERIFIER_OR_NOTE", "review"),
    ("2026-09-05", "2026-09-05-R1", "R01_VARIANCE", "warn"),
    ("2026-09-09", "2026-09-09-R1", "R01_VARIANCE", "warn"),
    ("2026-09-14", "2026-09-14-R1", "R01_VARIANCE", "warn"),
    ("2026-09-14", "2026-09-14-R1", "R04_REPEAT_SHORT", "warn"),
    ("2026-09-18", "2026-09-18-R1", "R01_VARIANCE", "warn"),
    ("2026-09-18", "2026-09-18-R1", "R04_REPEAT_SHORT", "warn"),
    ("2026-09-12", "2026-09-12-R1", "R01_VARIANCE", "warn"),
    ("2026-09-12", "2026-09-12-R1", "R02_SINGLE_DENOMINATION", "info"),
    ("2026-09-16", "", "R08_DEPOSIT", "review"),
    ("2026-09-21", "", "R08_DEPOSIT", "review"),
    ("2026-09-25", "2026-09-25-R1", "R09_DATA_INTEGRITY", "review"),
    ("2026-09-27", "2026-09-27-R2", "R09_DATA_INTEGRITY", "review"),
}


def test_full_demo_pipeline_exact_flags_and_documented_scenarios(
    tmp_path: Path,
) -> None:
    """S1 through S8 match exactly with no optional or extra rules in any export."""
    inputs, database = tmp_path / "demo", tmp_path / "demo.db"
    assert main(["demo-data", "--out", str(inputs)]) == 0
    assert main(["import", "--dir", str(inputs), "--db", str(database)]) == 0
    assert main(["reconcile", "--db", str(database)]) == 0
    report = load_report(database)
    actual = [
        (flag.business_date, report.shift_code(flag), flag.rule_code, flag.severity)
        for flag in report.flags
    ]
    assert len(actual) == len(_EXPECTED) == 16
    assert set(actual) == _EXPECTED
    documentation = Path(__file__).resolve().parents[1] / "docs/DEMO_SCENARIOS.md"
    rows = [
        line.split("|")[1:-1]
        for line in documentation.read_text().splitlines()
        if line.startswith(tuple(f"| S{number} |" for number in range(1, 9)))
    ]
    documented = {
        (
            day.strip(),
            "" if code.strip() == "none" else code.strip(),
            rule.strip(),
            severity.strip(),
        )
        for _, day, code, rule, severity, _ in rows
    }
    assert documented == _EXPECTED
    csv_rows = list(csv.DictReader(StringIO(csv_out.render(report))))
    assert {
        (row["date"], row["shift_code"], row["rule_code"], row["severity"])
        for row in csv_rows
    } == _EXPECTED
    for render in (text.render, html.render):
        output = render(report)
        assert "R04_REPEAT_SHORT" in output and "R08_DEPOSIT" in output
        assert "Missing deposit" in output and "-$100.00" in output
        assert "arrive in M5" not in output
    assert (
        next(
            flag for flag in report.flags if flag.business_date == "2026-09-16"
        ).evidence["issue"]
        == "missing"
    )
    mismatch = next(flag for flag in report.flags if flag.business_date == "2026-09-21")
    assert (
        mismatch.evidence["issue"] == "mismatch"
        and mismatch.evidence["difference_cents"] == -10000
    )
    assert not any(
        flag.rule_code == "R05_MISSING_VERIFIER_OR_NOTE"
        and report.shift_code(flag) == "2026-09-03-R1"
        for flag in report.flags
    )


def test_s9_repeated_import_preserves_all_counts_and_saved_results(
    demo_database: Path, tmp_path: Path
) -> None:
    """Skipped files preserve every table, saved evidence, settings, and completion time."""
    original = reconcile(demo_database, Config())
    tables = (
        "cashiers",
        "registers",
        "shifts",
        "pos_totals",
        "safe_drops",
        "cash_counts",
        "bank_deposits",
        "flags",
        "import_log",
        "reconciled_dates",
    )
    with closing(db.connect(demo_database)) as con:
        before = {
            table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in tables
        }
        markers = [
            tuple(row)
            for row in con.execute(
                "SELECT * FROM reconciled_dates ORDER BY business_date"
            )
        ]
        flags = db.load_flags(con, "0001-01-01", "9999-12-31")
    assert all(
        result.skipped
        for result in import_directory(tmp_path / "full-demo", demo_database)
    )
    with closing(db.connect(demo_database)) as con:
        assert before == {
            table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in tables
        }
        assert markers == [
            tuple(row)
            for row in con.execute(
                "SELECT * FROM reconciled_dates ORDER BY business_date"
            )
        ]
        assert flags == db.load_flags(con, "0001-01-01", "9999-12-31")
        assert con.execute("PRAGMA foreign_key_check").fetchall() == []
    assert reconcile(demo_database, Config()) == original


def test_committed_sample_matches_full_demo_except_timestamp(
    demo_database: Path,
) -> None:
    """The downloadable sample remains a real full-month report with every required rule."""
    reconcile(demo_database, Config())
    expected = html.render(load_report(demo_database))
    sample = (
        Path(__file__).resolve().parents[1] / "examples/sample_report.html"
    ).read_text()

    def without_timestamp(value: str) -> str:
        return re.sub(r"Generated on: [^<]+", "Generated on: TIMESTAMP", value)

    assert without_timestamp(sample) == without_timestamp(expected)
