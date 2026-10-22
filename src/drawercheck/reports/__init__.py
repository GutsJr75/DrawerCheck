"""Read one consistent report dataset and share it across all export formats."""

import os
from collections import Counter
from contextlib import closing
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from drawercheck import db, errors
from drawercheck.config import Config, config_from_snapshot
from drawercheck.models import DailyDeposit, Flag, ShiftResult
from drawercheck.reconcile import calculate_deposits, calculate_shifts, parse_range_date

STAGE_NOTICE = "Core checks only. Repeated-shortage checks (R04) and bank-deposit matching (R08) arrive in M5."
REVIEW_NOTICE = "Flags are leads for review, not findings about a person."
VARIANCE_NOTICE = "Cashier totals include every known signed difference, including differences within tolerance. Unknown and open shifts are excluded from money totals."


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

    def shift_code(self, flag: Flag) -> str:
        """Return the real shift code or an empty cell for a date-level flag."""
        return next(
            (
                result.shift.shift_code
                for result in self.shifts
                if result.shift.id == flag.shift_id
            ),
            "",
        )


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
            if not shifts:
                raise errors.ReconciliationError(errors.NO_SHIFTS)
            start = start or min(shift.business_date for shift in shifts)
            end = end or max(shift.business_date for shift in shifts)
            selected = tuple(
                shift for shift in shifts if start <= shift.business_date <= end
            )
            if not selected:
                raise errors.ReconciliationError(errors.NO_SHIFTS_IN_RANGE)
            dates = sorted({shift.business_date for shift in selected})
            snapshots = {db.completion_snapshot(con, day) for day in dates}
            if None in snapshots:
                raise errors.ReconciliationError(errors.NOT_RECONCILED)
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
            deposits = calculate_deposits(results, config, db.load_register_ids(con))
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
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=target.parent,
            prefix=".drawercheck-",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
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
