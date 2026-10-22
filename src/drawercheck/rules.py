"""Pure review rules that never read files or change the database."""

from datetime import date, timedelta
from typing import Literal

from drawercheck.config import Config
from drawercheck.models import BankDeposit, DailyDeposit, Flag, ShiftResult
from drawercheck.money import format_cents


def _flag(
    result: ShiftResult,
    code: str,
    severity: Literal["info", "warn", "review"],
    message: str,
    evidence: dict[str, object],
) -> Flag:
    return Flag(
        result.shift.id, result.shift.business_date, code, severity, message, evidence
    )


def variance_flags(
    result: ShiftResult, config: Config, history: tuple[ShiftResult, ...] = ()
) -> tuple[Flag, ...]:
    """Classify a known variance using tolerance and exact percentage boundaries."""
    variance = result.variance_cents
    if variance is None or abs(variance) <= config.within_tolerance_cents:
        return ()
    threshold = config.review_threshold(result.shift.pos.cash_sales_cents)
    severity: Literal["info", "warn", "review"] = "info"
    if abs(variance) >= threshold:
        severity = "review"
    elif abs(variance) >= config.warn_cents:
        severity = "warn"
    direction = "Short" if variance < 0 else "Over"
    return (
        _flag(
            result,
            "R01_VARIANCE",
            severity,
            f"{direction} by {format_cents(abs(variance))}. Recount recommended.",
            {
                "variance_cents": variance,
                "within_tolerance_cents": config.within_tolerance_cents,
                "warn_cents": config.warn_cents,
                "review_threshold_cents": threshold,
            },
        ),
    )


def denomination_flags(
    result: ShiftResult, config: Config, history: tuple[ShiftResult, ...] = ()
) -> tuple[Flag, ...]:
    """Suggest checking one bill when its value exactly matches the difference."""
    variance = result.variance_cents
    if variance is None or abs(variance) not in (100, 500, 1000, 2000, 5000, 10000):
        return ()
    dollars = abs(variance) // 100
    return (
        _flag(
            result,
            "R02_SINGLE_DENOMINATION",
            "info",
            f"Variance equals one ${dollars} bill. Check for a miscounted or misplaced bill.",
            {"variance_cents": variance, "denomination_cents": abs(variance)},
        ),
    )


def verification_flags(
    result: ShiftResult, config: Config, history: tuple[ShiftResult, ...] = ()
) -> tuple[Flag, ...]:
    """Request review when a qualifying difference lacks a verifier or note."""
    variance = result.variance_cents
    if (
        variance is None
        or abs(variance) < config.require_verifier_and_note_at_or_above_cents
    ):
        return ()
    missing = []
    if not (result.shift.verifier_id or "").strip():
        missing.append("verifier")
    if not (result.shift.variance_note or "").strip():
        missing.append("variance note")
    if not missing:
        return ()
    return (
        _flag(
            result,
            "R05_MISSING_VERIFIER_OR_NOTE",
            "review",
            f"Missing {' and '.join(missing)} for a difference of {format_cents(abs(variance))}. Review recommended.",
            {
                "variance_cents": variance,
                "missing": missing,
                "required_at_cents": config.require_verifier_and_note_at_or_above_cents,
            },
        ),
    )


def integrity_flags(
    result: ShiftResult, config: Config, history: tuple[ShiftResult, ...] = ()
) -> tuple[Flag, ...]:
    """Identify missing closing inputs and inconsistent shift records."""
    shift = result.shift
    issues: list[tuple[str, dict[str, object]]] = []
    if shift.closed_at is not None:
        if not shift.counts:
            issues.append(
                (
                    "Shift not counted: no cash-count rows. Counted cash is unknown.",
                    {"issue": "not_counted"},
                )
            )
        if shift.pos is None:
            issues.append(
                (
                    "Missing POS totals. Expected cash is unknown.",
                    {"issue": "missing_pos"},
                )
            )
        if shift.closed_at <= shift.opened_at:
            issues.append(
                (
                    "Closing time is not after opening time. Review the timestamps.",
                    {
                        "issue": "invalid_time_order",
                        "opened_at": shift.opened_at,
                        "closed_at": shift.closed_at,
                    },
                )
            )
        if result.expected_cents is not None and result.expected_cents < 0:
            issues.append(
                (
                    "Expected cash is negative. Review the cash movements.",
                    {
                        "issue": "negative_expected",
                        "expected_cents": result.expected_cents,
                    },
                )
            )
        if result.other_closing_codes:
            issues.append(
                (
                    "Multiple closing shifts for this register and business date. The daily deposit is incomplete.",
                    {
                        "issue": "multiple_closings",
                        "other_shift_codes": list(result.other_closing_codes),
                    },
                )
            )
    if result.overlapping_codes:
        issues.append(
            (
                "Shifts overlap on this register. Review the timestamps.",
                {
                    "issue": "overlap",
                    "other_shift_codes": list(result.overlapping_codes),
                },
            )
        )
    return tuple(
        _flag(result, "R09_DATA_INTEGRITY", "review", message, evidence)
        for message, evidence in issues
    )


def repeat_short_flags(
    result: ShiftResult, config: Config, history: tuple[ShiftResult, ...] = ()
) -> tuple[Flag, ...]:
    """Review qualifying shortages in this cashier's rolling window including this shift."""

    def _order(item: ShiftResult) -> tuple[str, str, str]:
        shift = item.shift
        return shift.business_date, shift.opened_at, shift.shift_code

    prior = sorted(
        (
            item
            for item in history
            if item.shift.cashier_id == result.shift.cashier_id
            and _order(item) < _order(result)
        ),
        key=_order,
    )
    window = (*prior, result)[-config.window :]
    shortages = tuple(
        item
        for item in window
        if item.variance_cents is not None and item.variance_cents <= -config.warn_cents
    )
    if len(shortages) < config.min_shifts:
        return ()
    return (
        _flag(
            result,
            "R04_REPEAT_SHORT",
            "warn",
            f"Short in {len(shortages)} of the last {len(window)} shifts for this cashier. "
            "Pattern for manager review. Check counts and cash records for possible errors.",
            {
                "cashier_id": result.shift.cashier_id,
                "window_shift_codes": [item.shift.shift_code for item in window],
                "shortages": [
                    {
                        "shift_code": item.shift.shift_code,
                        "variance_cents": item.variance_cents,
                    }
                    for item in shortages
                ],
                "min_shifts": config.min_shifts,
                "window": config.window,
                "warn_cents": config.warn_cents,
            },
        ),
    )


RULES = (
    variance_flags,
    denomination_flags,
    repeat_short_flags,
    verification_flags,
    integrity_flags,
)


def missing_register_flags(
    business_date: str,
    expected_register_ids: tuple[str, ...],
    present_register_ids: tuple[str, ...],
) -> tuple[Flag, ...]:
    """Flag an absent expected register once per business date without inventing a shift."""
    missing = sorted(set(expected_register_ids) - set(present_register_ids))
    return tuple(
        Flag(
            None,
            business_date,
            "R09_DATA_INTEGRITY",
            "review",
            f"No shift recorded for expected register {register_id}. The daily deposit is incomplete.",
            {"issue": "missing_register_shift", "register_id": register_id},
        )
        for register_id in missing
    )


def evaluate_rules(
    result: ShiftResult, config: Config, history: tuple[ShiftResult, ...] = ()
) -> tuple[Flag, ...]:
    """Apply the required shift rules with the available earlier cashier history."""
    return tuple(flag for rule in RULES for flag in rule(result, config, history))


def deposit_flags(
    days: tuple[DailyDeposit, ...], deposits: tuple[BankDeposit, ...], config: Config
) -> tuple[Flag, ...]:
    """Match daily amounts greedily once, retaining ambiguous entries for review."""
    remaining = {
        entry.id: entry
        for entry in sorted(deposits, key=lambda entry: (entry.deposit_date, entry.id))
    }
    flags = []
    for day in sorted(days, key=lambda item: item.business_date):
        expected = day.expected_cents
        if expected is None or expected <= 0:
            continue
        start = date.fromisoformat(day.business_date)
        end = start + timedelta(days=min(config.max_lag_days, (date.max - start).days))
        candidates = [
            entry
            for entry in remaining.values()
            if day.business_date <= entry.deposit_date <= end.isoformat()
        ]
        exact = next(
            (entry for entry in candidates if entry.amount_cents == expected), None
        )
        if exact is not None:
            del remaining[exact.id]
            continue
        evidence: dict[str, object] = {
            "expected_cents": expected,
            "window_start": day.business_date,
            "window_end": end.isoformat(),
            "max_lag_days": config.max_lag_days,
        }
        severity: Literal["warn", "review"] = "review"
        if len(candidates) == 1:
            entry = candidates[0]
            del remaining[entry.id]
            difference = entry.amount_cents - expected
            severity = "review" if abs(difference) >= config.review_cents else "warn"
            evidence.update(
                {
                    "issue": "mismatch",
                    "deposit_id": entry.id,
                    "deposit_date": entry.deposit_date,
                    "actual_cents": entry.amount_cents,
                    "difference_cents": difference,
                }
            )
            message = (
                f"Bank deposit differs by {format_cents(difference)}: "
                f"expected {format_cents(expected)}, recorded {format_cents(entry.amount_cents)}. "
                "Review the imported records."
            )
        elif not candidates:
            evidence["issue"] = "missing"
            message = (
                f"Missing deposit in imported records for expected {format_cents(expected)} "
                f"from {day.business_date} through {end.isoformat()}. Review the records."
            )
        else:
            evidence.update(
                {
                    "issue": "ambiguous",
                    "candidate_deposit_ids": [entry.id for entry in candidates],
                }
            )
            message = (
                f"No unique deposit match for expected {format_cents(expected)}: "
                f"{len(candidates)} nonmatching entries in the date window. Review the records."
            )
        flags.append(
            Flag(None, day.business_date, "R08_DEPOSIT", severity, message, evidence)
        )
    for entry in remaining.values():
        flags.append(
            Flag(
                None,
                entry.deposit_date,
                "R08_DEPOSIT",
                "info",
                f"Unexpected deposit of {format_cents(entry.amount_cents)} remains unmatched in imported records. Review the records.",
                {
                    "issue": "unexpected",
                    "deposit_id": entry.id,
                    "deposit_date": entry.deposit_date,
                    "actual_cents": entry.amount_cents,
                    "reference": entry.reference,
                },
            )
        )
    return tuple(flags)
