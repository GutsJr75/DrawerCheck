"""Verify calculations, full demo results, saved policies, and atomic replacement."""

import sqlite3
from contextlib import closing
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from drawercheck import db, errors
from drawercheck.config import Config
from drawercheck.importer import import_directory
from drawercheck.models import Shift
from drawercheck.money import MAX_CENTS
from drawercheck.reconcile import (
    calculate_shift,
    calculate_shifts,
    counted_cash,
    expected_cash,
    expected_deposit,
    explain_shift,
    reconcile,
)


def _saved(path: Path) -> tuple:
    with closing(db.connect(path)) as con:
        flags = db.load_flags(con, "0001-01-01", "9999-12-31")
        dates = tuple(
            tuple(row)
            for row in con.execute(
                "SELECT * FROM reconciled_dates ORDER BY business_date"
            )
        )
    return flags, dates


def test_worked_example(worked_shift: Shift) -> None:
    """The brief's expected, counted, variance, and deposit amounts all agree."""
    result = calculate_shift(worked_shift, Config())
    assert result.expected_cents == 51875
    assert result.counted_cents == 49875
    assert result.variance_cents == -2000
    assert result.status == "short"
    assert expected_deposit((result,), Config(), ("R1",)) == 119875
    assert [flag.rule_code for flag in result.flags] == [
        "R01_VARIANCE",
        "R02_SINGLE_DENOMINATION",
    ]


@pytest.mark.parametrize(
    ("field", "delta", "expected_delta"),
    [
        ("cash_sales_cents", 123, 123),
        ("paid_ins_cents", 123, 123),
        ("cash_refunds_cents", 123, -123),
        ("paid_outs_cents", 123, -123),
        ("card_sales_cents", 123, 0),
    ],
)
def test_cash_movements(
    worked_shift: Shift, field: str, delta: int, expected_delta: int
) -> None:
    """Each POS input affects cash in the correct direction, with cards excluded."""
    pos = replace(worked_shift.pos, **{field: getattr(worked_shift.pos, field) + delta})
    assert expected_cash(replace(worked_shift, pos=pos)) == 51875 + expected_delta


@pytest.mark.parametrize(
    ("changes", "expected", "counted", "status"),
    [
        ({"counts": ()}, 51875, None, "incomplete"),
        ({"pos": None}, None, 49875, "incomplete"),
        ({"counts": ((100, 0),)}, 51875, 0, "short"),
        ({"closed_at": None}, None, None, "open"),
        ({"counts": ((1, 51800),)}, 51875, 51800, "balanced"),
        ({"counts": ((1, 51976),)}, 51875, 51976, "over"),
    ],
)
def test_unknown_zero_open_and_tolerance(
    worked_shift: Shift,
    changes: dict,
    expected: int | None,
    counted: int | None,
    status: str,
) -> None:
    """Unknown, counted zero, and a small signed difference stay distinguishable."""
    result = calculate_shift(replace(worked_shift, **changes), Config())
    assert (result.expected_cents, result.counted_cents, result.status) == (
        expected,
        counted,
        status,
    )
    if status == "balanced":
        assert result.variance_cents == -75
    if status in ("incomplete", "open"):
        assert expected_deposit((result,), Config(), ("R1",)) is None


def test_aggregate_arithmetic_does_not_overflow_sqlite(worked_shift: Shift) -> None:
    """Python integers preserve sums and products beyond a single stored input's range."""
    shift = replace(
        worked_shift,
        opening_float_cents=MAX_CENTS,
        counts=((10000, MAX_CENTS),),
        safe_drops_cents=0,
    )
    assert expected_cash(shift) > MAX_CENTS
    assert counted_cash(shift) == 10000 * MAX_CENTS


@pytest.mark.parametrize(
    ("opened", "closed", "overlaps"),
    [
        ("2026-09-03T16:00:00", "2026-09-03T20:00:00", False),
        ("2026-09-03T15:59:59", "2026-09-03T20:00:00", True),
        ("2026-09-03T09:00:00", "2026-09-03T10:00:00", True),
        ("2026-09-03T09:00:00", "2026-09-03T09:00:00", False),
        ("2026-09-03T10:00:00", "2026-09-03T09:00:00", False),
        ("2026-09-03T15:00:00", None, True),
    ],
)
def test_register_intervals(
    worked_shift: Shift, opened: str, closed: str | None, overlaps: bool
) -> None:
    """Overlaps include containment and open shifts, but exclude adjacency and invalid intervals."""
    other = replace(
        worked_shift,
        id=2,
        shift_code="2026-09-03-R1-extra",
        opened_at=opened,
        closed_at=closed,
    )
    results = calculate_shifts((worked_shift, other), Config())
    assert bool(results[0].overlapping_codes) is overlaps
    assert bool(results[1].overlapping_codes) is overlaps
    if closed is not None:
        assert results[0].other_closing_codes == (other.shift_code,)
        assert any(
            flag.evidence.get("issue") == "multiple_closings"
            for flag in results[0].flags
        )
        assert expected_deposit(results, Config(), ("R1",)) is None


def test_independent_registers_and_combined_daily_deposit(worked_shift: Shift) -> None:
    """Separate registers can overlap and each retains one float in the daily total."""
    other = replace(worked_shift, id=2, register_id="R2", shift_code="2026-09-03-R2")
    results = calculate_shifts((worked_shift, other), Config())
    assert all(
        not result.overlapping_codes and not result.other_closing_codes
        for result in results
    )
    assert expected_deposit(results, Config(), ("R1", "R2")) == 239750


def test_full_demo_has_exactly_the_m3_flags(demo_database: Path) -> None:
    """S1, S2, S4, S7, and S8 match, with no premature M5 or optional flags."""
    run = reconcile(demo_database, Config())
    actual = {
        (result.shift.shift_code, flag.rule_code, flag.severity)
        for result in run.shifts
        for flag in result.flags
    }
    expected = {
        ("2026-09-03-R1", "R01_VARIANCE", "review"),
        ("2026-09-03-R1", "R02_SINGLE_DENOMINATION", "info"),
        ("2026-09-08-R2", "R01_VARIANCE", "review"),
        ("2026-09-08-R2", "R05_MISSING_VERIFIER_OR_NOTE", "review"),
        ("2026-09-12-R1", "R01_VARIANCE", "warn"),
        ("2026-09-12-R1", "R02_SINGLE_DENOMINATION", "info"),
        ("2026-09-25-R1", "R09_DATA_INTEGRITY", "review"),
        ("2026-09-27-R2", "R09_DATA_INTEGRITY", "review"),
    } | {
        (f"2026-09-{day}-R1", "R01_VARIANCE", "warn")
        for day in ("05", "09", "14", "18")
    }
    assert actual == expected
    assert sum(len(result.flags) for result in run.shifts) == 12
    assert len(run.shifts) == 60
    assert len(_saved(demo_database)[1]) == 30
    deposits = {day.business_date: day.expected_cents for day in run.deposits}
    assert deposits["2026-09-25"] is None
    assert deposits["2026-09-27"] is not None
    explanation = explain_shift(demo_database, "2026-09-03-R1")
    assert explanation.result.variance_cents == -2000
    assert explanation.deposit_contribution_cents == 119875


def test_repeated_runs_and_partial_replacement(demo_database: Path) -> None:
    """Rerunning a day does not duplicate flags or remove other completed dates."""
    first = reconcile(demo_database, Config())
    before_flags, _ = _saved(demo_database)
    assert reconcile(demo_database, Config()) == first
    assert _saved(demo_database)[0] == before_flags
    run = reconcile(demo_database, Config(), "2026-09-03", "2026-09-03")
    assert len(run.shifts) == 2
    assert _saved(demo_database)[0] == before_flags
    assert len(_saved(demo_database)[1]) == 30


@pytest.mark.parametrize(
    ("start", "end", "count"),
    [
        (None, "2026-09-03", 6),
        ("2026-09-29", None, 4),
    ],
)
def test_inclusive_ranges_and_stored_date_defaults(
    demo_database: Path, start: str | None, end: str | None, count: int
) -> None:
    """Missing endpoints use imported shift dates for inclusive selections."""
    run = reconcile(demo_database, Config(), start, end)
    assert len(run.shifts) == count
    assert run.from_date == (start or "2026-09-01")
    assert run.to_date == (end or "2026-09-30")


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("20260903", None),
        ("2026-02-30", None),
        (None, "2026-W36-4"),
        ("", None),
        ("2026-09-04", "2026-09-03"),
        ("2026-10-01", None),
        (None, "2026-08-31"),
    ],
)
def test_bad_ranges_preserve_saved_results(
    demo_database: Path, start: str | None, end: str | None
) -> None:
    """Invalid and reversed ranges cannot clear existing results."""
    reconcile(demo_database, Config())
    before = _saved(demo_database)
    with pytest.raises(errors.ReconciliationError):
        reconcile(demo_database, Config(), start, end)
    assert _saved(demo_database) == before


def test_changed_settings_clear_other_dates_and_explain_uses_snapshot(
    demo_database: Path,
) -> None:
    """A subset with new policies cannot leave earlier results using old policies."""
    reconcile(demo_database, Config())
    changed = replace(
        Config(),
        within_tolerance_cents=200,
        review_percent_of_cash_sales=Decimal("2.5"),
    )
    reconcile(demo_database, changed, "2026-09-03", "2026-09-03")
    assert len(_saved(demo_database)[1]) == 1
    assert {flag.business_date for flag in _saved(demo_database)[0]} == {"2026-09-03"}
    explanation = explain_shift(demo_database, "2026-09-03-R1")
    assert explanation.config == changed
    assert explanation.result.flags[0].evidence["review_threshold_cents"] == 2000
    with pytest.raises(
        errors.ReconciliationError, match="Run `drawercheck reconcile` first"
    ):
        explain_shift(demo_database, "2026-09-08-R2")


def test_completed_clean_day_can_be_explained(demo_database: Path) -> None:
    """A zero-flag day has a real completion marker and remains explainable."""
    reconcile(demo_database, Config(), "2026-09-01", "2026-09-01")
    explanation = explain_shift(demo_database, "2026-09-01-R1")
    assert explanation.result.flags == ()
    assert explanation.result.status == "balanced"


def test_surrounding_shift_is_checked_outside_range(demo_database: Path) -> None:
    """A prior day's open interval cannot be hidden by a filtered run."""
    with closing(db.connect(demo_database)) as con:
        with con:
            con.execute(
                "UPDATE shifts SET closed_at = ? WHERE shift_code = ?",
                ("2026-09-02T09:00:00", "2026-09-01-R1"),
            )
    run = reconcile(demo_database, Config(), "2026-09-02", "2026-09-02")
    result = next(result for result in run.shifts if result.shift.register_id == "R1")
    assert result.overlapping_codes == ("2026-09-01-R1",)
    assert any(flag.evidence.get("issue") == "overlap" for flag in result.flags)
    assert {flag.business_date for flag in _saved(demo_database)[0]} == {"2026-09-02"}


def test_saved_flags_and_markers_roll_back_on_failure(
    demo_database: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failure after replacing flags and policies restores the entire earlier run."""
    reconcile(demo_database, Config())
    before = _saved(demo_database)
    save = db.save_reconciliation

    def fail_after_save(*args: object) -> None:
        save(*args)
        raise sqlite3.IntegrityError("Demo late write failure.")

    monkeypatch.setattr(db, "save_reconciliation", fail_after_save)
    with pytest.raises(sqlite3.IntegrityError, match="Demo late write failure"):
        reconcile(demo_database, replace(Config(), within_tolerance_cents=200))
    assert _saved(demo_database) == before


@pytest.mark.parametrize("fail", [False, True])
def test_reconciliation_closes_connections(
    demo_database: Path, monkeypatch: pytest.MonkeyPatch, fail: bool
) -> None:
    """Success and failure both close the owned database connection."""
    connections = []
    connect = db.connect

    def track(path: str | Path) -> sqlite3.Connection:
        connection = connect(path)
        connections.append(connection)
        return connection

    monkeypatch.setattr(db, "connect", track)
    if fail:
        with pytest.raises(errors.ReconciliationError):
            explain_shift(demo_database, "missing-demo-shift")

        def fail_to_save(*args: object) -> None:
            raise sqlite3.OperationalError("Demo write failure.")

        monkeypatch.setattr(db, "save_reconciliation", fail_to_save)
        with pytest.raises(sqlite3.OperationalError):
            reconcile(demo_database, Config())
    else:
        reconcile(demo_database, Config())
        explain_shift(demo_database, "2026-09-03-R1")
    for connection in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("SELECT 1")


def test_m2_database_upgrades_only_on_success(
    demo_database: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The additional bookkeeping table works with the original nine-table database."""
    with closing(db.connect(demo_database)) as con:
        with con:
            con.execute("DROP TABLE reconciled_dates")
    with pytest.raises(
        errors.ReconciliationError, match="Run `drawercheck reconcile` first"
    ):
        explain_shift(demo_database, "2026-09-03-R1")
    save = db.save_reconciliation

    def fail(*args: object) -> None:
        save(*args)
        raise sqlite3.OperationalError("Demo upgrade failure.")

    with monkeypatch.context() as patch:
        patch.setattr(db, "save_reconciliation", fail)
        with pytest.raises(sqlite3.OperationalError):
            reconcile(demo_database, Config())
    with closing(db.connect(demo_database)) as con:
        assert not con.execute(
            "SELECT 1 FROM sqlite_schema WHERE name = ?", ("reconciled_dates",)
        ).fetchone()
    reconcile(demo_database, Config())
    assert len(_saved(demo_database)[1]) == 30


def test_import_invalidation_with_real_completion_markers(
    demo_database: Path, tmp_path: Path
) -> None:
    """Skipped files preserve real results, while any new record invalidates them."""
    directory = tmp_path / "full-demo"
    reconcile(demo_database, Config())
    before = _saved(demo_database)
    import_directory(directory, demo_database)
    assert _saved(demo_database) == before
    with (directory / "cashiers.csv").open("a") as stream:
        stream.write("cashier_05,Demo Cashier 05\n")
    with pytest.raises(errors.ImportValidationError):
        import_directory(directory, demo_database)
    assert _saved(demo_database) == before
    (directory / "cashiers.csv").write_text(
        "cashier_id,display_name\ncashier_05,Demo Cashier 05\n"
    )
    import_directory(directory, demo_database)
    assert _saved(demo_database) == ((), ())


def test_missing_empty_and_unknown_data(tmp_path: Path) -> None:
    """Missing paths stay absent and empty databases or unknown shifts have clear errors."""
    path = tmp_path / "absent.db"
    with pytest.raises(errors.ReconciliationError, match="not found"):
        reconcile(path, Config())
    assert not path.exists()
    with pytest.raises(errors.ReconciliationError, match="not found"):
        explain_shift(path, "fake-shift")
    assert not path.exists()
    db.initialize(path)
    with pytest.raises(errors.ReconciliationError, match="No shifts found"):
        reconcile(path, Config())
    with pytest.raises(errors.ReconciliationError, match="Unknown shift code"):
        explain_shift(path, "fake-shift")
