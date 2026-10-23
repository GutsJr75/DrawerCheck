"""Read one consistent report dataset and share it across all export formats."""

import os
import stat
from collections import Counter
from contextlib import closing
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from functools import cached_property
from pathlib import Path
from secrets import token_hex

from drawercheck import db, errors
from drawercheck.config import Config, config_from_snapshot
from drawercheck.models import DailyDeposit, Flag, ShiftResult
from drawercheck.money import format_cents
from drawercheck.reconcile import (
    calculate_deposits,
    calculate_shifts,
    imported_dates,
    parse_range_date,
)

STAGE_NOTICE = "Includes repeated-shortage checks (R04) and simplified bank-deposit matching (R08). Matching reserves all exact matches first, then reviews remaining entries in date order. It does not combine deposits and uses calendar-day windows. Expected deposits are calculated amounts; review bank flags for exceptions. Dates with zero shifts are bank-entry dates, not inferred business days."
REVIEW_NOTICE = "Flags are leads for review, not findings about a person."
VARIANCE_NOTICE = "Cashier totals include every known signed difference, including differences within tolerance. Unknown and open shifts are excluded from money totals."


def format_amount(value: int | None) -> str:
    """Label unavailable cash explicitly and delegate currency formatting to money.py."""
    return "unknown" if value is None else format_cents(value)


@dataclass(frozen=True)
class DailySummary:
    """Status counts and review counts for one completed business date."""

    business_date: str
    shifts: int
    balanced: int
    over: int
    short: int
    incomplete: int
    open: int
    info: int
    warn: int
    review: int
    expected_deposit_cents: int | None

    @property
    def expected_deposit_text(self) -> str:
        """Distinguish a bank-only date from a closing day with incomplete cash records."""
        if self.shifts == 0:
            return "Not calculated (no shifts)"
        return format_amount(self.expected_deposit_cents)


@dataclass(frozen=True)
class CashierSummary:
    """Exact known over/short amounts alongside counts of missing closing results."""

    cashier_id: str
    display_name: str
    shifts: int
    known: int
    incomplete: int
    open: int
    over_cents: int
    short_cents: int
    net_cents: int


@dataclass(frozen=True)
class ReportData:
    """A read-only export snapshot built from completed dates and their saved policy."""

    from_date: str
    to_date: str
    generated_at: str
    config: Config
    shifts: tuple[ShiftResult, ...]
    flags: tuple[Flag, ...]
    days: tuple[DailySummary, ...]
    cashiers: tuple[CashierSummary, ...]

    @cached_property
    def _shift_codes(self) -> dict[int, str]:
        return {result.shift.id: result.shift.shift_code for result in self.shifts}

    def shift_code(self, flag: Flag) -> str:
        """Return the real shift code or an empty cell for a date-level flag."""
        return "" if flag.shift_id is None else self._shift_codes.get(flag.shift_id, "")


def _daily_summaries(
    results: tuple[ShiftResult, ...],
    deposits: tuple[DailyDeposit, ...],
    flags: tuple[Flag, ...],
) -> tuple[DailySummary, ...]:
    summaries = []
    for day in deposits:
        shifts = tuple(
            result
            for result in results
            if result.shift.business_date == day.business_date
        )
        statuses = Counter(result.status for result in shifts)
        severities = Counter(
            flag.severity for flag in flags if flag.business_date == day.business_date
        )
        summaries.append(
            DailySummary(
                day.business_date,
                len(shifts),
                statuses["balanced"],
                statuses["over"],
                statuses["short"],
                statuses["incomplete"],
                statuses["open"],
                severities["info"],
                severities["warn"],
                severities["review"],
                day.expected_cents,
            )
        )
    return tuple(summaries)


def _cashier_summaries(
    results: tuple[ShiftResult, ...], names: dict[str, str]
) -> tuple[CashierSummary, ...]:
    summaries = []
    for cashier_id in sorted({result.shift.cashier_id for result in results}):
        shifts = tuple(
            result for result in results if result.shift.cashier_id == cashier_id
        )
        known = tuple(
            result.variance_cents
            for result in shifts
            if result.variance_cents is not None
        )
        summaries.append(
            CashierSummary(
                cashier_id,
                names[cashier_id],
                len(shifts),
                len(known),
                sum(result.status == "incomplete" for result in shifts),
                sum(result.status == "open" for result in shifts),
                sum(value for value in known if value > 0),
                -sum(value for value in known if value < 0),
                sum(known),
            )
        )
    return tuple(summaries)


def load_report(
    database_path: str | Path,
    from_date: str | None = None,
    to_date: str | None = None,
    *,
    date: str | None = None,
    generated_at: datetime | None = None,
) -> ReportData:
    """Read completed dates without reconciling, changing flags, or loading today's config."""
    if date is not None and (from_date is not None or to_date is not None):
        raise errors.UsageError(errors.REPORT_DATE_CONFLICT)
    start = parse_range_date(
        date if date is not None else from_date,
        "--date" if date is not None else "--from",
    )
    end = parse_range_date(
        date if date is not None else to_date, "--date" if date is not None else "--to"
    )
    if start is not None and end is not None and start > end:
        raise errors.ReconciliationError(errors.REVERSED_RANGE)
    if not Path(database_path).exists():
        raise errors.ReconciliationError(
            errors.DATABASE_NOT_FOUND.format(path=database_path)
        )
    with closing(db.connect(database_path)) as con:
        with con:
            db.require_import_schema(con)
            shifts = db.load_shifts(con)
            bank_entries = db.load_bank_deposits(con)
            if not shifts and not bank_entries:
                raise errors.ReconciliationError(errors.NO_SHIFTS)
            all_dates = imported_dates(shifts, bank_entries)
            start = start or all_dates[0]
            end = end or all_dates[-1]
            selected = tuple(
                shift for shift in shifts if start <= shift.business_date <= end
            )
            dates = tuple(day for day in all_dates if start <= day <= end)
            if not dates:
                raise errors.ReconciliationError(errors.NO_SHIFTS_IN_RANGE)
            snapshots = set()
            for day in dates:
                snapshot = db.completion_snapshot(con, day)
                if snapshot is None:
                    raise errors.ReconciliationError(
                        errors.REPORT_NOT_RECONCILED.format(date=day)
                    )
                snapshots.add(snapshot)
            if len(snapshots) != 1:
                raise errors.ReconciliationError(errors.REPORT_MIXED_POLICIES)
            config = config_from_snapshot(snapshots.pop())
            flags = db.load_flags(con, start, end)
            selected_ids = {shift.id for shift in selected}
            results = tuple(
                replace(
                    result,
                    flags=tuple(
                        flag for flag in flags if flag.shift_id == result.shift.id
                    ),
                )
                for result in calculate_shifts(shifts, config)
                if result.shift.id in selected_ids
            )
            deposits = calculate_deposits(
                results,
                config,
                db.load_register_ids(con),
                tuple(
                    entry
                    for entry in bank_entries
                    if start <= entry.deposit_date <= end
                ),
            )
            names = db.load_cashier_names(con)
    timestamp = generated_at if generated_at is not None else datetime.now(UTC)
    return ReportData(
        start,
        end,
        timestamp.isoformat(timespec="seconds"),
        config,
        results,
        flags,
        _daily_summaries(results, deposits, flags),
        _cashier_summaries(results, names),
    )


def write_report(path: str | Path, content: str, database_path: str | Path) -> None:
    """Atomically write UTF-8 output while protecting the database and cleaning partial files."""
    target, database = Path(path), Path(database_path)
    protected = {
        str(database.resolve()) + suffix for suffix in ("", "-journal", "-wal", "-shm")
    }
    if str(target.resolve()) in protected or (
        target.exists() and database.exists() and target.samefile(database)
    ):
        raise errors.UsageError(errors.REPORT_DATABASE_OUTPUT)
    temporary = None
    try:
        existing_mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else None
        candidate = target.parent / f".drawercheck-{token_hex(16)}.tmp"
        # Exclusive creation prevents replacing another file; the OS applies umask.
        descriptor = os.open(
            candidate,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600 if existing_mode is not None else 0o666,
        )
        temporary = candidate
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
        if existing_mode is not None:
            temporary.chmod(existing_mode)
        os.replace(temporary, target)
    except OSError as error:
        raise errors.DrawerCheckError(
            errors.REPORT_OUTPUT_ERROR.format(
                path=target, detail=error.strerror or str(error)
            )
        ) from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
