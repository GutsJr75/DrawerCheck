"""Check rolling cashier history without losing missing or out-of-range shifts."""

from dataclasses import replace
from pathlib import Path

import pytest

from drawercheck.config import Config
from drawercheck.models import Shift, ShiftResult
from drawercheck.reconcile import (
    calculate_shift,
    calculate_shifts,
    explain_shift,
    reconcile,
)
from drawercheck.rules import repeat_short_flags


def _result(shift: Shift, number: int, variance: int | None) -> ShiftResult:
    day = f"2026-09-{number:02d}"
    return calculate_shift(
        replace(
            shift,
            id=number,
            shift_code=f"{day}-R1",
            business_date=day,
            opened_at=f"{day}T08:00:00",
            closed_at=f"{day}T16:00:00",
            counts=() if variance is None else ((1, 51875 + variance),),
        ),
        Config(),
    )


@pytest.mark.parametrize(
    ("variances", "triggered"),
    [
        ((-500, -500, -500), True),
        ((-499, -500, -500), False),
        ((500, -500, -500), False),
        ((None, -500, -500), False),
        ((-500, -500, 0), False),
    ],
)
def test_pattern_threshold_and_current_inclusion(
    worked_shift: Shift, variances: tuple[int | None, ...], triggered: bool
) -> None:
    """Only known shortages at least as large as warn_cents count, including today."""
    results = tuple(
        _result(worked_shift, index, value) for index, value in enumerate(variances, 1)
    )
    flags = repeat_short_flags(results[-1], Config(), results[:-1])
    assert bool(flags) is triggered
    if flags:
        assert flags[0].severity == "warn"
        assert "3 of the last 3 shifts" in flags[0].message
        assert [item["variance_cents"] for item in flags[0].evidence["shortages"]] == [
            -500
        ] * 3


@pytest.mark.parametrize("current_variance", [0, 500, None])
def test_pattern_can_remain_on_later_nonshort_shift(
    worked_shift: Shift, current_variance: int | None
) -> None:
    """A qualifying history remains a review lead even when the current shift is not short."""
    history = tuple(_result(worked_shift, index, -600) for index in range(1, 4))
    current = _result(worked_shift, 4, current_variance)
    assert repeat_short_flags(current, Config(), history)
    assert current.variance_cents == current_variance


@pytest.mark.parametrize("open_shift", [False, True])
def test_unknown_and_open_shifts_occupy_window(
    worked_shift: Shift, open_shift: bool
) -> None:
    """An unknown shift displaces an older shortage instead of being silently skipped."""
    history = tuple(_result(worked_shift, index, -600) for index in range(1, 4))
    unknown = _result(worked_shift, 4, None)
    if open_shift:
        unknown = calculate_shift(replace(unknown.shift, closed_at=None), Config())
    current = _result(worked_shift, 5, -600)
    flags = repeat_short_flags(
        current, replace(Config(), window=3), (*history, unknown)
    )
    assert not flags


def test_pattern_excludes_other_cashiers_future_and_duplicate_current(
    worked_shift: Shift,
) -> None:
    """History is ordered and scoped by cashier and never counts today's shift twice."""
    current = _result(worked_shift, 4, -600)
    other = _result(replace(worked_shift, cashier_id="cashier_other"), 2, -600)
    future = _result(worked_shift, 5, -600)
    prior = _result(worked_shift, 1, -600)
    assert not repeat_short_flags(current, Config(), (future, other, current, prior))
    second = _result(worked_shift, 3, -600)
    flags = repeat_short_flags(
        current, Config(), (future, second, other, current, prior)
    )
    assert flags[0].evidence["window_shift_codes"] == [
        prior.shift.shift_code,
        second.shift.shift_code,
        current.shift.shift_code,
    ]


def test_pattern_window_expires_and_uses_custom_settings(worked_shift: Shift) -> None:
    """An old shortage falls out of the configured window and custom thresholds apply."""
    history = tuple(
        _result(worked_shift, index, -600 if index <= 3 else 0) for index in range(1, 6)
    )
    current = _result(worked_shift, 6, 0)
    assert repeat_short_flags(current, replace(Config(), window=6), history)
    assert not repeat_short_flags(current, replace(Config(), window=5), history)
    assert not repeat_short_flags(current, replace(Config(), warn_cents=700), history)
    singleton = _result(worked_shift, 1, -500)
    assert repeat_short_flags(singleton, replace(Config(), min_shifts=1, window=1))


def test_shift_history_uses_date_time_and_code_order(worked_shift: Shift) -> None:
    """Input order cannot change rolling history, including shifts on the same date."""
    base = _result(worked_shift, 1, -600).shift
    shifts = tuple(
        replace(
            base, id=index, shift_code=code, register_id=f"R{index}", opened_at=opened
        )
        for index, code, opened in [
            (1, "A", "2026-09-01T08:00:00"),
            (2, "B", "2026-09-01T08:00:00"),
            (3, "C", "2026-09-01T09:00:00"),
        ]
    )
    results = calculate_shifts(tuple(reversed(shifts)), Config())
    flags = [
        flag
        for result in results
        for flag in result.flags
        if flag.rule_code == "R04_REPEAT_SHORT"
    ]
    assert len(flags) == 1 and flags[0].shift_id == 3
    assert flags[0].evidence["window_shift_codes"] == ["A", "B", "C"]


def test_filtered_pattern_uses_prior_history_and_saved_explanation(
    demo_database: Path,
) -> None:
    """A single-day run and explain retain shortages before the selected start date."""
    full = reconcile(demo_database, Config())
    filtered = reconcile(demo_database, Config(), "2026-09-14", "2026-09-14")
    assert filtered.flags == tuple(
        flag for flag in full.flags if flag.business_date == "2026-09-14"
    )
    explanation = explain_shift(demo_database, "2026-09-14-R1")
    flag = next(
        flag
        for flag in explanation.result.flags
        if flag.rule_code == "R04_REPEAT_SHORT"
    )
    assert len(flag.evidence["window_shift_codes"]) == 10
    assert [item["variance_cents"] for item in flag.evidence["shortages"]] == [
        -600,
        -800,
        -700,
    ]
