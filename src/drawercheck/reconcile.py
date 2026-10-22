"""Calculate exact cash differences and atomically save neutral review leads."""

from collections import defaultdict
from contextlib import closing
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

from drawercheck import db, errors
from drawercheck.config import Config, config_from_snapshot
from drawercheck.models import (
    DailyDeposit,
    ReconciliationResult,
    Shift,
    ShiftExplanation,
    ShiftResult,
)
from drawercheck.rules import evaluate_rules


def expected_cash(shift: Shift) -> int | None:
    """Calculate closing cash from the float and cash movements, excluding cards."""
    if shift.closed_at is None or shift.pos is None:
        return None
    pos = shift.pos
    return (
        shift.opening_float_cents
        + pos.cash_sales_cents
        + pos.paid_ins_cents
        - pos.cash_refunds_cents
        - pos.paid_outs_cents
        - shift.safe_drops_cents
    )


def counted_cash(shift: Shift) -> int | None:
    """Sum denomination quantities, preserving missing counts as unknown."""
    if shift.closed_at is None or not shift.counts:
        return None
    return sum(denomination * quantity for denomination, quantity in shift.counts)


def calculate_shift(
    shift: Shift,
    config: Config,
    overlapping_codes: tuple[str, ...] = (),
    other_closing_codes: tuple[str, ...] = (),
) -> ShiftResult:
    """Preserve exact variance separately from the within-tolerance status."""
    expected, counted = expected_cash(shift), counted_cash(shift)
    variance = (
        counted - expected if counted is not None and expected is not None else None
    )
    if shift.closed_at is None:
        status = "open"
    elif variance is None:
        status = "incomplete"
    elif abs(variance) <= config.within_tolerance_cents:
        status = "balanced"
    else:
        status = "short" if variance < 0 else "over"
    result = ShiftResult(
        shift,
        expected,
        counted,
        variance,
        status,
        overlapping_codes,
        other_closing_codes,
    )
    return replace(result, flags=evaluate_rules(result, config))


def calculate_shifts(
    shifts: tuple[Shift, ...], config: Config
) -> tuple[ShiftResult, ...]:
    """Check full imported register context before callers select a date range."""
    by_register: dict[str, list[Shift]] = defaultdict(list)
    closings: dict[tuple[str, str], list[Shift]] = defaultdict(list)
    overlaps: dict[int, list[str]] = defaultdict(list)
    for shift in shifts:
        by_register[shift.register_id].append(shift)
        if shift.closed_at is not None:
            closings[(shift.register_id, shift.business_date)].append(shift)
    for register_shifts in by_register.values():
        ordered = sorted(
            register_shifts, key=lambda shift: (shift.opened_at, shift.shift_code)
        )
        for index, left in enumerate(ordered):
            if left.closed_at is not None and left.closed_at <= left.opened_at:
                continue
            for right in ordered[index + 1 :]:
                if left.closed_at is not None and right.opened_at >= left.closed_at:
                    break
                if right.closed_at is not None and right.closed_at <= right.opened_at:
                    continue
                overlaps[left.id].append(right.shift_code)
                overlaps[right.id].append(left.shift_code)
    return tuple(
        calculate_shift(
            shift,
            config,
            tuple(sorted(overlaps[shift.id])),
            tuple(
                sorted(
                    other.shift_code
                    for other in closings[(shift.register_id, shift.business_date)]
                    if other.id != shift.id
                )
            )
            if shift.closed_at is not None
            else (),
        )
        for shift in shifts
    )


def expected_deposit(results: tuple[ShiftResult, ...], config: Config) -> int | None:
    """Calculate a complete day's deposit without counting the same drawer twice."""
    if not results or any(
        result.status in ("open", "incomplete") or result.other_closing_codes
        for result in results
    ):
        return None
    registers = {result.shift.register_id for result in results}
    if len(registers) != len(results):
        return None
    return sum(
        result.counted_cents + result.shift.safe_drops_cents for result in results
    ) - config.retained_float_per_register_cents * len(registers)


def parse_range_date(value: str | None, option: str) -> str | None:
    """Validate exact calendar dates without using today's date as a fallback."""
    if value is None:
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise errors.ReconciliationError(
            errors.INVALID_RANGE_DATE.format(option=option, value=value)
        ) from error
    if parsed.isoformat() != value:
        raise errors.ReconciliationError(
            errors.INVALID_RANGE_DATE.format(option=option, value=value)
        )
    return value


def _require_database(path: str | Path) -> None:
    if not Path(path).exists():
        raise errors.ReconciliationError(errors.DATABASE_NOT_FOUND.format(path=path))


def reconcile(
    database_path: str | Path,
    config: Config,
    from_date: str | None = None,
    to_date: str | None = None,
) -> ReconciliationResult:
    """Save one inclusive range, rolling back all replacements if anything fails."""
    start = parse_range_date(from_date, "--from")
    end = parse_range_date(to_date, "--to")
    if start is not None and end is not None and start > end:
        raise errors.ReconciliationError(errors.REVERSED_RANGE)
    _require_database(database_path)
    with closing(db.connect(database_path)) as con:
        with con:
            shifts = db.load_shifts(con)
            if not shifts:
                raise errors.ReconciliationError(errors.NO_SHIFTS)
            start = start or min(shift.business_date for shift in shifts)
            end = end or max(shift.business_date for shift in shifts)
            if start > end:
                raise errors.ReconciliationError(errors.REVERSED_RANGE)
            selected = tuple(
                result
                for result in calculate_shifts(shifts, config)
                if start <= result.shift.business_date <= end
            )
            dates = tuple(sorted({result.shift.business_date for result in selected}))
            deposits = tuple(
                DailyDeposit(
                    day,
                    expected_deposit(
                        tuple(
                            result
                            for result in selected
                            if result.shift.business_date == day
                        ),
                        config,
                    ),
                )
                for day in dates
            )
            flags = tuple(flag for result in selected for flag in result.flags)
            db.save_reconciliation(
                con,
                start,
                end,
                config.snapshot(),
                datetime.now(UTC).isoformat(timespec="seconds"),
                dates,
                flags,
            )
    return ReconciliationResult(start, end, selected, deposits)


def explain_shift(database_path: str | Path, shift_code: str) -> ShiftExplanation:
    """Explain one completed shift using its saved policies and review leads."""
    _require_database(database_path)
    with closing(db.connect(database_path)) as con:
        with con:
            shifts = db.load_shifts(con)
            shift = next(
                (shift for shift in shifts if shift.shift_code == shift_code), None
            )
            if shift is None:
                raise errors.ReconciliationError(
                    errors.UNKNOWN_SHIFT.format(shift_code=shift_code)
                )
            snapshot = db.completion_snapshot(con, shift.business_date)
            if snapshot is None:
                raise errors.ReconciliationError(errors.NOT_RECONCILED)
            config = config_from_snapshot(snapshot)
            day_results = tuple(
                result
                for result in calculate_shifts(shifts, config)
                if result.shift.business_date == shift.business_date
            )
            result = next(
                result for result in day_results if result.shift.id == shift.id
            )
            saved_flags = tuple(
                flag
                for flag in db.load_flags(con, shift.business_date, shift.business_date)
                if flag.shift_id == shift.id
            )
            result = replace(result, flags=saved_flags)
            daily_deposit = expected_deposit(day_results, config)
            contribution = (
                (
                    result.counted_cents
                    + shift.safe_drops_cents
                    - config.retained_float_per_register_cents
                )
                if daily_deposit is not None
                else None
            )
    return ShiftExplanation(result, config, contribution, daily_deposit)
