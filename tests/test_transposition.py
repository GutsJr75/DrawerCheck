"""Check the R03 heuristic without treating divisibility as proof of a typo."""

import json
from contextlib import closing
from dataclasses import replace
from pathlib import Path

import pytest

from drawercheck import db, errors
from drawercheck.config import Config, config_from_snapshot
from drawercheck.models import Shift
from drawercheck.reconcile import calculate_shift, explain_shift, reconcile
from drawercheck.reports import csv_out, html, load_report, text
from drawercheck.rules import transposition_flags


@pytest.mark.parametrize("variance", [900, -900, 2700, -2700, 4500, -4500])
def test_whole_dollar_multiples_of_nine_are_hints(
    worked_shift: Shift, variance: int
) -> None:
    """Both signs and the requested +$27 example produce an info-level lead."""
    shift = replace(worked_shift, counts=((1, 51875 + variance),))
    result = calculate_shift(shift, Config())
    flags = [
        flag for flag in result.flags if flag.rule_code == "R03_TRANSPOSITION_HINT"
    ]
    assert len(flags) == 1
    assert flags[0].severity == "info"
    assert flags[0].message == (
        "Could be two digits swapped when typing a total. Hint only."
    )
    assert flags[0].evidence == {"variance_cents": variance, "heuristic": True}


@pytest.mark.parametrize("variance", [0, 9, -9, 899, -899, 901, -901, 999, 1000, 2799])
def test_small_fractional_or_nonmatching_differences_have_no_hint(
    worked_shift: Shift, variance: int
) -> None:
    """Cents divisible by nine do not count unless the dollar amount qualifies."""
    result = calculate_shift(
        replace(worked_shift, counts=((1, 51875 + variance),)), Config()
    )
    assert not transposition_flags(result, Config())


@pytest.mark.parametrize(
    "changes", [{"counts": ()}, {"pos": None}, {"closed_at": None}]
)
def test_unknown_or_open_shift_never_guesses_a_typo(
    worked_shift: Shift, changes: dict
) -> None:
    """An unknown variance cannot be used by the hint."""
    result = calculate_shift(replace(worked_shift, **changes), Config())
    assert result.variance_cents is None
    assert not transposition_flags(result, Config())


def test_large_integer_difference_is_not_rounded(worked_shift: Shift) -> None:
    """A qualifying amount beyond exact float precision is checked as an integer."""
    variance = (2**53 // 900 + 1) * 900
    result = calculate_shift(
        replace(worked_shift, counts=((1, 51875 + variance),)), Config()
    )
    assert (
        transposition_flags(result, Config())[0].evidence["variance_cents"] == variance
    )
    assert not transposition_flags(
        replace(result, variance_cents=variance + 1), Config()
    )


def test_hint_is_saved_explained_exported_and_stable_when_filtered(
    demo_database: Path,
) -> None:
    """The same R03 evidence survives saving, explanation, exports, and reruns."""
    reconcile(demo_database, Config())
    explanation = explain_shift(demo_database, "2026-09-08-R2")
    hint = next(
        flag
        for flag in explanation.result.flags
        if flag.rule_code == "R03_TRANSPOSITION_HINT"
    )
    assert hint.evidence == {"variance_cents": -4500, "heuristic": True}
    report = load_report(demo_database)
    for render in (text.render, html.render, csv_out.render):
        assert hint.rule_code in render(report)
        assert hint.message in render(report)
    run = reconcile(demo_database, Config(), "2026-09-08", "2026-09-08")
    assert [flag for flag in run.flags if flag.rule_code == hint.rule_code] == [hint]


def test_pre_r03_policy_is_rejected_and_rerun_clears_other_old_dates(
    demo_database: Path,
) -> None:
    """Version-four saved results cannot silently mix with the new rule set."""
    reconcile(demo_database, Config())
    old = json.loads(Config().snapshot())
    old["policy_version"] = 4
    with pytest.raises(errors.ReconciliationError, match="earlier review policy"):
        config_from_snapshot(json.dumps(old))
    with closing(db.connect(demo_database)) as con:
        with con:
            con.execute(
                "UPDATE reconciled_dates SET config_json = ?", (json.dumps(old),)
            )
    with pytest.raises(errors.ReconciliationError, match="earlier review policy"):
        explain_shift(demo_database, "2026-09-08-R2")
    reconcile(demo_database, Config(), "2026-09-08", "2026-09-08")
    with closing(db.connect(demo_database)) as con:
        days = con.execute("SELECT business_date FROM reconciled_dates").fetchall()
        assert [row["business_date"] for row in days] == ["2026-09-08"]
