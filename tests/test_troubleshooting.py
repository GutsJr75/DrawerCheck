"""Keep each troubleshooting symptom tied to a real CLI failure and central message."""

import errno
import re
import sqlite3
from pathlib import Path

import pytest

from drawercheck import db, errors
from drawercheck.cli import main
from drawercheck.config import Config
from drawercheck.importer import import_directory
from drawercheck.reconcile import reconcile


@pytest.mark.parametrize("case", range(1, 11), ids=lambda case: f"T{case:02d}")
def test_documented_symptom_is_emitted_by_cli(
    case: int,
    csv_directory: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Trigger each documented error and compare its full text with errors.py and the guide."""
    monkeypatch.chdir(tmp_path)
    database = Path("demo.db")
    import_directory(csv_directory, database)
    if case == 1:
        (csv_directory / "bank_deposits.csv").write_text(
            "deposit_date,amount,reference\n2026-09-01,1.234,DEMO-INVALID\n"
        )
        arguments = ["import", "--dir", str(csv_directory)]
        expected = errors.IMPORT_VALIDATION.format(
            file_name="bank_deposits.csv",
            line_number=2,
            column="amount",
            detail=errors.INVALID_MONEY.format(value="1.234"),
        )
    elif case == 2:
        (csv_directory / "cash_counts.csv").write_text(
            "shift_code,denomination,quantity\n2026-09-01-R1,3.00,1\n"
        )
        arguments = ["import", "--dir", str(csv_directory)]
        expected = errors.IMPORT_VALIDATION.format(
            file_name="cash_counts.csv",
            line_number=2,
            column="denomination",
            detail=errors.UNKNOWN_DENOMINATION.format(value="3.00"),
        )
    elif case == 3:
        arguments = ["explain", "DEMO-NO-SHIFT"]
        expected = errors.UNKNOWN_SHIFT.format(shift_code="DEMO-NO-SHIFT")
    elif case == 4:
        monkeypatch.setattr(sqlite3, "sqlite_version_info", (3, 36, 0))
        arguments = ["init-db"]
        expected = errors.SQLITE_TOO_OLD.format(version="3.36.0")
    elif case in (5, 6):

        def fail(path: str | Path) -> None:
            raise sqlite3.OperationalError(
                "database is locked"
                if case == 5
                else "attempt to write a readonly database"
            )

        monkeypatch.setattr(db, "initialize", fail)
        arguments = ["init-db"]
        expected = errors.DATABASE_LOCKED if case == 5 else errors.DATABASE_READ_ONLY
    elif case == 7:
        reconcile(database, Config())

        def deny(source: object, destination: object) -> None:
            raise PermissionError(errno.EACCES, "Permission denied", str(destination))

        monkeypatch.setattr("drawercheck.reports.os.replace", deny)
        arguments = [
            "report",
            "--date",
            "2026-09-01",
            "--format",
            "html",
            "--out",
            "blocked.html",
        ]
        expected = errors.REPORT_OUTPUT_ERROR.format(
            path="blocked.html", detail="Permission denied"
        )
    elif case == 8:
        arguments = ["report", "--date", "2026-09-01"]
        expected = errors.REPORT_NOT_RECONCILED.format(date="2026-09-01")
    elif case == 9:
        (csv_directory / "cashiers.csv").write_text("cashier_id\n")
        arguments = ["import", "--dir", str(csv_directory)]
        expected = errors.IMPORT_VALIDATION.format(
            file_name="cashiers.csv",
            line_number=1,
            column="<header>",
            detail=errors.MISSING_COLUMNS.format(columns="display_name"),
        )
    else:
        Path("bad.toml").write_text("[tolerance\n")
        arguments = ["reconcile", "--config", "bad.toml"]
        expected = errors.CONFIG_INVALID.format(path="bad.toml")
    assert main([*arguments, "--db", str(database)]) == 1
    output = capsys.readouterr()
    assert output.out == "" and output.err.strip() == expected
    assert "Traceback" not in output.err
    guide = Path(__file__).resolve().parents[1] / "docs/TROUBLESHOOTING.md"
    section = guide.read_text().split(f"## T{case:02d}:", 1)[1].split("\n## ", 1)[0]
    symptom = re.search(r"```text\n(.*?)\n```", section, re.DOTALL)
    assert symptom is not None and symptom.group(1) == expected
