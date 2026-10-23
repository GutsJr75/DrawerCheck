"""Exercise exact, mismatched, missing, ambiguous, and unexpected bank entries."""

import csv
import json
from contextlib import closing
from dataclasses import replace
from io import StringIO
from pathlib import Path

import pytest

from drawercheck import db, errors
from drawercheck.config import Config
from drawercheck.models import BankDeposit, DailyDeposit
from drawercheck.reconcile import explain_shift, reconcile
from drawercheck.reports import csv_out, html, load_report, text
from drawercheck.rules import deposit_flags


def _entry(identifier: int, day: str, amount: int = 10000) -> BankDeposit:
    return BankDeposit(identifier, day, amount, f"DEMO-{identifier}")


@pytest.mark.parametrize("lag", [0, 1, 3, 31])
def test_exact_deposit_matches_at_inclusive_window_end(lag: int) -> None:
    """A single exact entry at the final permitted calendar day produces no flag."""
    from datetime import date, timedelta

    day = "2026-09-01"
    end = (date.fromisoformat(day) + timedelta(days=lag)).isoformat()
    entries = (_entry(1, end),)
    assert (
        deposit_flags(
            (DailyDeposit(day, 10000),), entries, replace(Config(), max_lag_days=lag)
        )
        == ()
    )
    assert entries == (_entry(1, end),)


@pytest.mark.parametrize(
    ("difference", "severity"),
    [
        (-1999, "warn"),
        (-2000, "review"),
        (1999, "warn"),
        (2000, "review"),
        (-1, "warn"),
        (1, "warn"),
    ],
)
def test_mismatch_sign_and_review_boundary(difference: int, severity: str) -> None:
    """A unique candidate is consumed and its signed difference controls the evidence."""
    flags = deposit_flags(
        (DailyDeposit("2026-09-01", 10000),),
        (_entry(1, "2026-09-02", 10000 + difference),),
        Config(),
    )
    assert len(flags) == 1 and flags[0].severity == severity
    assert flags[0].evidence["issue"] == "mismatch"
    assert flags[0].evidence["difference_cents"] == difference
    assert flags[0].evidence["deposit_id"] == 1 and flags[0].shift_id is None
    assert ("less than expected" if difference < 0 else "more than expected") in flags[
        0
    ].message
    assert "differs by" not in flags[0].message


def test_mismatch_uses_configured_review_threshold() -> None:
    """Deposit review uses the absolute configured review amount, not sales percentages."""
    flags = deposit_flags(
        (DailyDeposit("2026-09-01", 10000),),
        (_entry(1, "2026-09-01", 9500),),
        replace(Config(), review_cents=500),
    )
    assert flags[0].severity == "review"


@pytest.mark.parametrize("entry_date", ["2026-08-31", "2026-09-05"])
def test_outside_window_is_missing_and_unexpected(entry_date: str) -> None:
    """A deposit before or after the inclusive window cannot be borrowed."""
    flags = deposit_flags(
        (DailyDeposit("2026-09-01", 10000),), (_entry(1, entry_date),), Config()
    )
    assert [(flag.evidence["issue"], flag.severity) for flag in flags] == [
        ("missing", "review"),
        ("unexpected", "info"),
    ]
    assert flags[1].business_date == entry_date


def test_missing_entry_has_no_claim_about_elapsed_real_time() -> None:
    """Missing means absent from the supplied dataset, with no dependency on today's date."""
    (flag,) = deposit_flags((DailyDeposit("9999-12-31", 10000),), (), Config())
    assert flag.evidence["issue"] == "missing"
    assert flag.evidence["window_end"] == "9999-12-31"
    assert "imported records" in flag.message


def test_ambiguous_entries_are_not_combined_or_consumed() -> None:
    """Several nonmatching entries stay unmatched rather than becoming an invented match."""
    entries = (_entry(2, "2026-09-02", 6000), _entry(1, "2026-09-01", 4000))
    flags = deposit_flags((DailyDeposit("2026-09-01", 10000),), entries, Config())
    assert [flag.evidence["issue"] for flag in flags] == [
        "ambiguous",
        "unexpected",
        "unexpected",
    ]
    assert flags[0].evidence["candidate_deposit_ids"] == [1, 2]


def test_later_exact_match_is_reserved_before_earlier_mismatch() -> None:
    """Reserve a later day's exact entry before counting an earlier day's leftovers."""
    days = (DailyDeposit("2026-09-01", 10000), DailyDeposit("2026-09-02", 6000))
    flags = deposit_flags(
        days, (_entry(1, "2026-09-02", 6000), _entry(2, "2026-09-02", 4000)), Config()
    )
    assert len(flags) == 1 and flags[0].business_date == "2026-09-01"
    assert flags[0].evidence["issue"] == "mismatch"
    assert flags[0].evidence["deposit_id"] == 2
    assert flags[0].evidence["difference_cents"] == -6000


def test_later_exact_match_cannot_be_consumed_as_earlier_mismatch() -> None:
    """The exact-match pass protects an entry even when an earlier day has no other candidate."""
    days = (DailyDeposit("2026-09-01", 10000), DailyDeposit("2026-09-02", 6000))
    flags = deposit_flags(days, (_entry(1, "2026-09-02", 6000),), Config())
    assert len(flags) == 1 and flags[0].business_date == "2026-09-01"
    assert flags[0].evidence["issue"] == "missing"


def test_ambiguity_counts_only_entries_left_after_all_exact_matches() -> None:
    """Several remaining candidates still require review after reserving later exact matches."""
    days = (DailyDeposit("2026-09-01", 10000), DailyDeposit("2026-09-02", 6000))
    entries = (
        _entry(1, "2026-09-02", 6000),
        _entry(2, "2026-09-02", 4000),
        _entry(3, "2026-09-02", 3000),
    )
    flags = deposit_flags(days, entries, Config())
    assert [flag.evidence["issue"] for flag in flags] == [
        "ambiguous",
        "unexpected",
        "unexpected",
    ]
    assert flags[0].evidence["candidate_deposit_ids"] == [2, 3]
    assert "2 nonmatching entries" in flags[0].message


@pytest.mark.parametrize("difference", [-1, 1])
def test_one_cent_demo_difference_uses_remaining_candidate(
    demo_database: Path, difference: int
) -> None:
    """Ordinary daily deposits do not turn a one-cent difference into several review leads."""
    original = reconcile(demo_database, Config())
    with closing(db.connect(demo_database)) as con:
        with con:
            con.execute(
                "UPDATE bank_deposits SET amount_cents = amount_cents + ? WHERE reference = ?",
                (difference, "DEMO-DEPOSIT-2026-09-02"),
            )
    changed = reconcile(demo_database, Config())
    assert changed == reconcile(demo_database, Config())
    assert len(changed.flags) == 17
    assert (
        tuple(flag for flag in changed.flags if flag.business_date != "2026-09-02")
        == original.flags
    )
    flags = tuple(flag for flag in changed.flags if flag.business_date == "2026-09-02")
    assert len(flags) == 1 and flags[0].severity == "warn"
    assert flags[0].evidence["issue"] == "mismatch"
    assert flags[0].evidence["expected_cents"] == 248998
    assert flags[0].evidence["difference_cents"] == difference
    assert "$0.01" in flags[0].message
    filtered = reconcile(demo_database, Config(), "2026-09-02", "2026-09-02")
    assert filtered.flags == flags
    report = load_report(demo_database, date="2026-09-02")
    assert report.flags == flags
    direction = "less" if difference < 0 else "more"
    for render in (text.render, html.render):
        assert f"{direction} than expected" in render(report)
        assert "No unique deposit match" not in render(report)
    (row,) = csv.DictReader(StringIO(csv_out.render(report)))
    assert row["severity"] == "warn" and "$0.01" in row["message"]


def test_exact_preference_and_date_then_identity_ties() -> None:
    """An exact amount wins over mismatches, then the earliest date and lowest ID win."""
    entries = (
        _entry(4, "2026-09-03"),
        _entry(3, "2026-09-02"),
        _entry(2, "2026-09-02"),
        _entry(1, "2026-09-01", 9000),
    )
    flags = deposit_flags((DailyDeposit("2026-09-01", 10000),), entries, Config())
    assert [flag.evidence["deposit_id"] for flag in flags] == [1, 3, 4]
    assert all(flag.evidence["issue"] == "unexpected" for flag in flags)


@pytest.mark.parametrize("expected", [None, 0, -100])
def test_unknown_or_nonpositive_expected_amount_is_not_matched(
    expected: int | None,
) -> None:
    """Missing cash cannot be replaced with zero or matched to a bank entry."""
    flags = deposit_flags(
        (DailyDeposit("2026-09-01", expected),), (_entry(1, "2026-09-01"),), Config()
    )
    assert len(flags) == 1 and flags[0].evidence["issue"] == "unexpected"


def test_same_amount_on_two_days_demonstrates_greedy_limitation() -> None:
    """The early day consumes an entry whose reference actually names the later day."""
    days = (DailyDeposit("2026-09-02", 10000), DailyDeposit("2026-09-01", 10000))
    entry = replace(_entry(1, "2026-09-02"), reference="DEMO intended for September 2")
    flags = deposit_flags(days, (entry,), Config())
    assert len(flags) == 1 and flags[0].business_date == "2026-09-02"
    assert flags[0].evidence["issue"] == "missing"


def test_final_calendar_day_can_match_without_overflow() -> None:
    """Clipping the lag window preserves an exact final-day match."""
    assert (
        deposit_flags(
            (DailyDeposit("9999-12-31", 10000),), (_entry(1, "9999-12-31"),), Config()
        )
        == ()
    )


def test_filtered_matching_does_not_reuse_prior_days_deposit(
    demo_database: Path,
) -> None:
    """Filtered matching agrees with the full history even when the bank entry is already used."""
    with closing(db.connect(demo_database)) as con:
        with con:
            con.execute("DELETE FROM bank_deposits")
    initial = reconcile(demo_database, Config())
    amount = initial.deposits[0].expected_cents
    with closing(db.connect(demo_database)) as con:
        with con:
            con.execute(
                "INSERT INTO bank_deposits (deposit_date, amount_cents, reference) VALUES (?, ?, ?)",
                ("2026-09-02", amount, "DEMO overlapping window"),
            )
    full = reconcile(demo_database, Config())
    filtered = reconcile(demo_database, Config(), "2026-09-02", "2026-09-02")
    assert filtered.flags == tuple(
        flag for flag in full.flags if flag.business_date == "2026-09-02"
    )
    assert [
        flag.evidence["issue"]
        for flag in filtered.flags
        if flag.rule_code == "R08_DEPOSIT"
    ] == ["missing"]


def test_bank_only_date_is_saved_and_exported_without_invented_shifts(
    demo_database: Path,
) -> None:
    """An unmatched entry after the last shift remains visible in reports and filtered runs."""
    with closing(db.connect(demo_database)) as con:
        with con:
            con.execute(
                "INSERT INTO bank_deposits (deposit_date, amount_cents, reference) VALUES (?, ?, ?)",
                ("2026-10-10", 12345, "DEMO extra"),
            )
    run = reconcile(demo_database, Config())
    assert run.to_date == "2026-10-10" and len(run.shifts) == 60
    filtered = reconcile(demo_database, Config(), "2026-10-10", "2026-10-10")
    assert not filtered.shifts and len(filtered.flags) == 1
    assert filtered.flags[0].evidence["issue"] == "unexpected"
    report = load_report(demo_database, date="2026-10-10")
    assert report.days[0].shifts == 0 and report.days[0].expected_deposit_cents is None
    assert not report.cashiers
    for render in (text.render, html.render):
        assert "Unexpected deposit" in render(report)
    (row,) = csv.DictReader(StringIO(csv_out.render(report)))
    assert row["date"] == "2026-10-10" and row["shift_code"] == ""
    with closing(db.connect(demo_database)) as con:
        assert db.completion_snapshot(con, "2026-10-10") == Config().snapshot()


def test_bank_only_date_requires_completion(demo_database: Path) -> None:
    """A saved shift run cannot conceal a bank-only date that was never checked."""
    with closing(db.connect(demo_database)) as con:
        with con:
            con.execute(
                "INSERT INTO bank_deposits (deposit_date, amount_cents) VALUES (?, ?)",
                ("2026-10-10", 12345),
            )
    reconcile(demo_database, Config(), "2026-09-01", "2026-09-30")
    with pytest.raises(errors.ReconciliationError, match="2026-10-10"):
        load_report(demo_database)


@pytest.mark.parametrize("old_policy", [2, 3])
def test_older_saved_results_require_refresh(
    demo_database: Path, old_policy: int
) -> None:
    """Old report policies cannot silently claim that the new rules have run."""
    reconcile(demo_database, Config())
    snapshot = json.loads(Config().snapshot())
    snapshot["policy_version"] = old_policy
    with closing(db.connect(demo_database)) as con:
        with con:
            con.execute(
                "UPDATE reconciled_dates SET config_json = ?",
                (json.dumps(snapshot, sort_keys=True),),
            )
    with pytest.raises(errors.ReconciliationError, match="earlier review policy"):
        load_report(demo_database)
    with pytest.raises(errors.ReconciliationError, match="earlier review policy"):
        explain_shift(demo_database, "2026-09-03-R1")
    reconcile(demo_database, Config(), "2026-09-21", "2026-09-21")
    with closing(db.connect(demo_database)) as con:
        assert [
            row[0] for row in con.execute("SELECT business_date FROM reconciled_dates")
        ] == ["2026-09-21"]
        assert {
            flag.business_date
            for flag in db.load_flags(con, "0001-01-01", "9999-12-31")
        } == {"2026-09-21"}
