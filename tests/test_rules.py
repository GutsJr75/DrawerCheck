"""Exercise each M3 rule on both sides of its exact boundaries."""

from dataclasses import replace

import pytest

from drawercheck.config import Config
from drawercheck.models import Shift
from drawercheck.reconcile import calculate_shift
from drawercheck.rules import (
    denomination_flags,
    integrity_flags,
    variance_flags,
    verification_flags,
)


def _with_variance(shift: Shift, variance: int) -> Shift:
    return replace(shift, counts=((1, 51875 + variance),))


@pytest.mark.parametrize(
    ("variance", "severity"),
    [
        (0, None),
        (99, None),
        (-100, None),
        (100, None),
        (101, "info"),
        (-101, "info"),
        (499, "info"),
        (500, "warn"),
        (-500, "warn"),
        (1249, "warn"),
        (1250, "review"),
        (-1250, "review"),
        (2000, "review"),
    ],
)
def test_variance_boundaries(
    worked_shift: Shift, variance: int, severity: str | None
) -> None:
    """R01 respects tolerance, warning, and the rounded percent review threshold."""
    result = calculate_shift(_with_variance(worked_shift, variance), Config())
    flags = variance_flags(result, Config())
    assert [flag.severity for flag in flags] == ([severity] if severity else [])
    if flags:
        assert flags[0].evidence["variance_cents"] == variance
        assert flags[0].evidence["review_threshold_cents"] == 1250


@pytest.mark.parametrize("variance", [100, -100, 500, -1000, 2000, -5000, 10000])
def test_bill_hint_is_independent_of_tolerance(
    worked_shift: Shift, variance: int
) -> None:
    """R02 includes the one-dollar bill even when R01 is within tolerance."""
    result = calculate_shift(_with_variance(worked_shift, variance), Config())
    flags = denomination_flags(result, Config())
    assert len(flags) == 1
    assert flags[0].severity == "info"
    assert flags[0].evidence["denomination_cents"] == abs(variance)
    if variance == 100:
        assert not variance_flags(result, Config())
        assert result.status == "balanced"


@pytest.mark.parametrize("variance", [0, 50, 200, 499, 2700, 4500])
def test_non_bill_differences_have_no_hint(worked_shift: Shift, variance: int) -> None:
    """R02 does not include coins or the two-dollar count denomination."""
    assert not denomination_flags(
        calculate_shift(_with_variance(worked_shift, variance), Config()), Config()
    )


@pytest.mark.parametrize(
    ("verifier", "note", "missing"),
    [
        (None, None, ["verifier", "variance note"]),
        ("manager_01", None, ["variance note"]),
        (None, "Demo recount.", ["verifier"]),
        ("manager_01", "Demo recount.", []),
        (" ", "\t", ["verifier", "variance note"]),
    ],
)
def test_verification_fields(
    worked_shift: Shift, verifier: str | None, note: str | None, missing: list[str]
) -> None:
    """R05 requires both a verifier and a nonblank note at the threshold."""
    shift = replace(worked_shift, verifier_id=verifier, variance_note=note)
    flags = verification_flags(calculate_shift(shift, Config()), Config())
    assert len(flags) == bool(missing)
    if missing:
        assert flags[0].severity == "review"
        assert flags[0].evidence["missing"] == missing


def test_below_verification_threshold(worked_shift: Shift) -> None:
    """R05 does not require missing fields below the configured boundary."""
    shift = replace(
        _with_variance(worked_shift, -1999), verifier_id=None, variance_note=None
    )
    assert not verification_flags(calculate_shift(shift, Config()), Config())


@pytest.mark.parametrize(
    ("changes", "issue"),
    [
        ({"counts": ()}, "not_counted"),
        ({"pos": None}, "missing_pos"),
        ({"closed_at": "2026-09-03T08:00:00"}, "invalid_time_order"),
        ({"closed_at": "2026-09-03T07:59:59"}, "invalid_time_order"),
        ({"safe_drops_cents": 200000}, "negative_expected"),
    ],
)
def test_integrity_conditions(worked_shift: Shift, changes: dict, issue: str) -> None:
    """Each incomplete or inconsistent condition produces its own factual lead."""
    result = calculate_shift(replace(worked_shift, **changes), Config())
    flags = integrity_flags(result, Config())
    assert [flag.evidence["issue"] for flag in flags] == [issue]
    assert flags[0].severity == "review"


@pytest.mark.parametrize(
    "changes",
    [{}, {"counts": ((100, 0),)}, {"closed_at": None, "counts": (), "pos": None}],
)
def test_valid_or_open_shift_has_no_integrity_flag(
    worked_shift: Shift, changes: dict
) -> None:
    """A real zero count is valid, and an open shift does not require closing inputs."""
    assert not integrity_flags(
        calculate_shift(replace(worked_shift, **changes), Config()), Config()
    )


@pytest.mark.parametrize(
    "changes", [{"counts": ()}, {"pos": None}, {"closed_at": None}]
)
def test_unknown_variance_suppresses_money_rules(
    worked_shift: Shift, changes: dict
) -> None:
    """Missing cash cannot create a shortage, bill hint, or missing-verifier lead."""
    result = calculate_shift(replace(worked_shift, **changes), Config())
    assert result.variance_cents is None
    assert not variance_flags(result, Config())
    assert not denomination_flags(result, Config())
    assert not verification_flags(result, Config())
