"""Check efficient lookups and optional limits on expanded reconciliation details."""

import csv
from contextlib import closing
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import pytest

from drawercheck import db, errors
from drawercheck.config import Config
from drawercheck.importer import import_directory
from drawercheck.models import Shift
from drawercheck.reconcile import calculate_shifts, reconcile


@pytest.mark.parametrize("upgrade", [False, True])
@pytest.mark.parametrize("table", ["bank_deposits", "safe_drops"])
def test_duplicate_lookup_has_bounded_database_work(
    demo_database: Path, table: str, upgrade: bool
) -> None:
    """A missing duplicate key must not scan thousands of similar existing rows."""
    with closing(db.connect(demo_database)) as con:
        if upgrade:
            with con:
                con.execute("DROP INDEX IF EXISTS bank_deposits_record")
                con.execute("DROP INDEX IF EXISTS safe_drops_record")
    if upgrade:
        db.initialize(demo_database)
        db.initialize(demo_database)
    with closing(db.connect(demo_database)) as con:
        with con:
            if table == "bank_deposits":
                con.executemany(
                    "INSERT INTO bank_deposits (deposit_date, amount_cents, reference) VALUES (?, ?, ?)",
                    [("2026-10-01", 1, f"DEMO-{index}") for index in range(2000)],
                )
                query = "SELECT 1 FROM bank_deposits WHERE deposit_date = ? AND amount_cents = ? AND reference IS ?"
                values = ("2026-10-01", 1, "DEMO-MISSING")
            else:
                shift_id = con.execute(
                    "SELECT id FROM shifts ORDER BY id LIMIT 1"
                ).fetchone()[0]
                con.executemany(
                    "INSERT INTO safe_drops (shift_id, amount_cents, dropped_at, bag_number) VALUES (?, ?, ?, ?)",
                    [
                        (shift_id, 1, "2026-09-01T09:00:00", f"DEMO-{index}")
                        for index in range(2000)
                    ],
                )
                query = "SELECT 1 FROM safe_drops WHERE shift_id = ? AND amount_cents = ? AND dropped_at = ? AND bag_number IS ?"
                values = (shift_id, 1, "2026-09-01T09:00:00", "DEMO-MISSING")
        # Count SQLite work rather than depending on a machine's clock speed.
        con.set_progress_handler(lambda: 1, 1000)
        try:
            assert con.execute(query, values).fetchone() is None
        finally:
            con.set_progress_handler(None, 0)
        assert con.execute("SELECT COUNT(*) FROM shifts").fetchone()[0] == 60


@pytest.mark.parametrize("case", ["overlap-only", "closings-only", "both"])
@pytest.mark.parametrize("difference", [-1, 0, 1])
def test_related_shift_detail_budget_boundary(
    worked_shift: Shift, case: str, difference: int
) -> None:
    """Bound the expanded evidence while leaving default CLI calculations unchanged."""
    shifts = []
    for index in range(4):
        day = (
            date(2026, 9, 3) + timedelta(days=index if case == "overlap-only" else 0)
        ).isoformat()
        opened = (
            f"{day}T{8 + index * 2:02d}:00:00"
            if case == "closings-only"
            else f"{day}T08:00:00"
        )
        closed = (
            f"{day}T{9 + index * 2:02d}:00:00"
            if case == "closings-only"
            else "2035-01-01T16:00:00"
        )
        shifts.append(
            replace(
                worked_shift,
                id=index + 1,
                shift_code=f"DEMO-{index}",
                business_date=day,
                opened_at=opened,
                closed_at=closed,
            )
        )
    baseline = calculate_shifts(tuple(shifts), Config())
    references = sum(
        len(result.overlapping_codes) + len(result.other_closing_codes)
        for result in baseline
    )
    assert references == (24 if case == "both" else 12)
    if difference < 0:
        with pytest.raises(errors.CalculationLimitError):
            calculate_shifts(
                tuple(shifts), Config(), max_related_shift_codes=references + difference
            )
    else:
        assert (
            calculate_shifts(
                tuple(shifts), Config(), max_related_shift_codes=references + difference
            )
            == baseline
        )


def test_default_core_imports_keep_web_only_limits_optional(
    csv_directory: Path, tmp_path: Path
) -> None:
    """The CLI's shared import still accepts larger rosters and longer values."""
    for name, count in (("cashiers.csv", 101), ("registers.csv", 6)):
        source = csv_directory / name
        with source.open(newline="") as stream:
            rows = list(csv.reader(stream))
        if name == "cashiers.csv":
            rows[1][1] = "x" * 257
        rows.extend(
            [
                [f"EXTRA-{index}", f"Demo entry {index}"]
                for index in range(count - len(rows) + 1)
            ]
        )
        with source.open("w", newline="") as stream:
            csv.writer(stream, lineterminator="\n").writerows(rows)
    database = tmp_path / "uncapped.db"
    import_directory(csv_directory, database)
    assert reconcile(database, Config()).shifts
    with closing(db.connect(database)) as con:
        assert con.execute("SELECT COUNT(*) FROM cashiers").fetchone()[0] == 101
        assert con.execute("SELECT COUNT(*) FROM registers").fetchone()[0] == 6
        assert (
            con.execute("SELECT MAX(length(display_name)) FROM cashiers").fetchone()[0]
            == 257
        )


def test_default_core_allows_details_above_the_web_budget(worked_shift: Shift) -> None:
    """Ordinary core calls still return all leads without the optional web budget."""
    shifts = tuple(
        replace(worked_shift, id=index + 1, shift_code=f"DEMO-{index}")
        for index in range(23)
    )
    results = calculate_shifts(shifts, Config())
    assert (
        sum(
            len(result.overlapping_codes) + len(result.other_closing_codes)
            for result in results
        )
        == 1012
    )
    with pytest.raises(errors.CalculationLimitError):
        calculate_shifts(shifts, Config(), max_related_shift_codes=1000)
