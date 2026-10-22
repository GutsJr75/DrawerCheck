"""Pure review rules that never read files or change the database."""

from typing import Literal

from drawercheck.config import Config
from drawercheck.models import Flag, ShiftResult
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


def variance_flags(result: ShiftResult, config: Config) -> tuple[Flag, ...]:
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


def denomination_flags(result: ShiftResult, config: Config) -> tuple[Flag, ...]:
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


def verification_flags(result: ShiftResult, config: Config) -> tuple[Flag, ...]:
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


def integrity_flags(result: ShiftResult, config: Config) -> tuple[Flag, ...]:
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


RULES = (variance_flags, denomination_flags, verification_flags, integrity_flags)


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


def evaluate_rules(result: ShiftResult, config: Config) -> tuple[Flag, ...]:
    """Apply only the four rules authorized for the core reconciliation milestone."""
    return tuple(flag for rule in RULES for flag in rule(result, config))
