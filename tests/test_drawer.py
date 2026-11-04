"""Check one manually entered drawer against the walkthrough answers and the CSV path."""

from dataclasses import astuple
from pathlib import Path

import pytest
from drawer_cases import SIGN_OFF, drawer_payload, write_case_csvs

from drawercheck import errors
from drawercheck.config import Config
from drawercheck.drawer import check_drawer, parse_drawer
from drawercheck.importer import import_directory
from drawercheck.reconcile import reconcile
from drawercheck.reports import load_report

WALKTHROUGH = {
    # case: (payload changes, expected, counted, difference, status, leads)
    "A": ({}, 52086, 52061, -25, "balanced", []),
    "B": (
        {},
        68565,
        66565,
        -2000,
        "short",
        [
            ("R01_VARIANCE", "review"),
            ("R02_SINGLE_DENOMINATION", "info"),
            ("R05_MISSING_VERIFIER_OR_NOTE", "review"),
        ],
    ),
    "B signed": (
        SIGN_OFF,
        68565,
        66565,
        -2000,
        "short",
        [("R01_VARIANCE", "review"), ("R02_SINGLE_DENOMINATION", "info")],
    ),
    "C": ({}, None, 43780, None, "incomplete", [("R09_DATA_INTEGRITY", "review")]),
}


def _check(case: str, **changes: object):
    return check_drawer(drawer_payload(case, **changes), Config())


def _problems(payload: dict) -> dict[str, str]:
    with pytest.raises(errors.DrawerInputError) as caught:
        parse_drawer(payload)
    return dict(caught.value.problems)


def _states(check) -> dict[str, str]:
    return {entry.rule_code: entry.state for entry in check.coverage}


@pytest.mark.parametrize("name", WALKTHROUGH)
def test_walkthrough_cases_match_their_expected_answers(name: str) -> None:
    """M11_BLOCK1.md: the answers confirmed with the CLI, now from manual entry."""
    changes, expected, counted, difference, status, leads = WALKTHROUGH[name]
    result = _check(name[0], **changes).result
    assert result.expected_cents == expected
    assert result.counted_cents == counted
    assert result.variance_cents == difference
    assert result.status == status
    assert [(flag.rule_code, flag.severity) for flag in result.flags] == leads


@pytest.mark.parametrize("signed", [False, True])
def test_manual_entry_and_csv_import_give_identical_results(
    tmp_path: Path, signed: bool
) -> None:
    """The same drawers through both paths share amounts, status, and every lead."""
    write_case_csvs(tmp_path / "csv", signed=signed)
    database = tmp_path / "run.db"
    import_directory(tmp_path / "csv", database)
    reconcile(database, Config())
    imported = {
        result.shift.register_id: result for result in load_report(database).shifts
    }
    for case in ("A", "B", "C"):
        changes = SIGN_OFF if signed and case == "B" else {}
        manual = _check(case, **changes).result
        csv_result = imported[manual.shift.register_id]
        assert manual.shift.shift_code == csv_result.shift.shift_code
        for field in ("expected_cents", "counted_cents", "variance_cents", "status"):
            assert getattr(manual, field) == getattr(csv_result, field)
        assert [astuple(flag)[1:] for flag in manual.flags] == [
            astuple(flag)[1:] for flag in csv_result.flags
        ]


def test_coverage_comes_from_inputs_with_a_known_difference() -> None:
    """Case B: leads found, R03 ran without one, R04 and R08 never run."""
    check = _check("B")
    assert _states(check) == {
        "R01_VARIANCE": "ran_lead",
        "R02_SINGLE_DENOMINATION": "ran_lead",
        "R03_TRANSPOSITION_HINT": "ran_no_lead",
        "R05_MISSING_VERIFIER_OR_NOTE": "ran_lead",
        "R09_DATA_INTEGRITY": "ran_no_lead",
        "R04_REPEAT_SHORT": "not_run",
        "R08_DEPOSIT": "not_run",
    }
    r09 = next(
        entry for entry in check.coverage if entry.rule_code == "R09_DATA_INTEGRITY"
    )
    assert r09.partial
    assert "Whether expected cash is negative." in r09.checked
    assert len(r09.unavailable) == 3


def test_a_cleared_sign_off_lead_says_the_signer_is_not_confirmed() -> None:
    """Supplying a verifier and note clears R05 without vouching for anyone."""
    check = _check("B", **SIGN_OFF)
    r05 = next(
        entry
        for entry in check.coverage
        if entry.rule_code == "R05_MISSING_VERIFIER_OR_NOTE"
    )
    assert r05.state == "ran_no_lead"
    assert "does not confirm who signed" in r05.detail
    assert check.result.variance_cents == -2000


def test_without_a_report_difference_checks_do_not_run() -> None:
    """Case C: no difference, so R01 to R05 are not run and R09 says what it lacks."""
    check = _check("C")
    states = _states(check)
    for code in (
        "R01_VARIANCE",
        "R02_SINGLE_DENOMINATION",
        "R03_TRANSPOSITION_HINT",
        "R05_MISSING_VERIFIER_OR_NOTE",
    ):
        assert states[code] == "not_run"
    r09 = next(
        entry for entry in check.coverage if entry.rule_code == "R09_DATA_INTEGRITY"
    )
    assert r09.state == "ran_lead"
    assert "Whether expected cash is negative." not in r09.checked
    assert r09.unavailable[0] == (
        "Whether expected cash is negative: expected cash is unknown."
    )
    assert check.result.shift.pos is None


def test_repeated_shortage_and_deposit_rules_never_produce_leads() -> None:
    """An isolated drawer cannot imply a pattern or a missing bank deposit."""
    for case in ("A", "B", "C"):
        codes = {flag.rule_code for flag in _check(case).result.flags}
        assert not codes & {"R04_REPEAT_SHORT", "R08_DEPOSIT"}


def test_an_all_zero_count_is_a_confirmed_empty_drawer() -> None:
    """Zeros on every line mean $0.00 counted, not an unknown count."""
    zeros = {key: "0" for key in drawer_payload("A")["counts"]}
    result = _check("A", counts=zeros).result
    assert result.counted_cents == 0
    assert result.variance_cents == -52086
    assert result.status == "short"


def test_a_blank_count_line_is_an_error_not_zero() -> None:
    """Blank never silently becomes 0."""
    payload = drawer_payload("A")
    payload["counts"]["20.00"] = ""
    assert _problems(payload) == {
        "counts.20.00": "Enter how many $20 bills were counted, as a whole number. Write 0 if none."
    }


def test_every_field_problem_is_reported_together() -> None:
    """The page can list every correction at once and focus the first."""
    payload = drawer_payload(
        "B",
        business_date="2026-02-30",
        register_id=" R2",
        opening_float="200",
        verifier_id="manager\t01",
    )
    payload["counts"]["0.25"] = "7.5"
    payload["register_report"]["paid_outs"] = ""
    payload["safe_drops"][1]["amount"] = "0.00"
    assert list(_problems(payload)) == [
        "business_date",
        "register_id",
        "opening_float",
        "counts.0.25",
        "register_report.paid_outs",
        "safe_drops.2.amount",
        "verifier_id",
    ]


@pytest.mark.parametrize(
    "value", ["20", "20.0", "$20.00", "1,316.40", "-1.00", " 1.00", "1e3", "20.005"]
)
def test_money_must_be_plain_dollars_and_cents(value: str) -> None:
    """Strict two-decimal amounts, the same rule as the CSV importer."""
    problems = _problems(drawer_payload("A", opening_float=value))
    assert problems == {
        "opening_float": errors.DRAWER_MONEY.format(label="the starting cash")
    }


@pytest.mark.parametrize("value", ["1000000.00", "9" * 40 + ".00"])
def test_money_above_the_manual_limit_is_rejected(value: str) -> None:
    """Each amount is at most $999,999.99 in this path."""
    problems = _problems(drawer_payload("A", opening_float=value))
    assert problems["opening_float"] == (
        "The starting cash must be $999,999.99 or less."
    )


def test_the_largest_allowed_amount_and_quantity_are_accepted() -> None:
    """The limits are inclusive."""
    payload = drawer_payload("A", opening_float="999999.99")
    payload["counts"]["0.01"] = "99999"
    shift, _ = parse_drawer(payload)
    assert shift.opening_float_cents == 99_999_999
    assert dict(shift.counts)[1] == 99_999


@pytest.mark.parametrize(
    "value", ["-1", "1.5", " 3", "three", "100000", "1" + "0" * 30]
)
def test_count_quantities_must_be_whole_numbers_within_the_limit(value: str) -> None:
    """Quantities are digits only, from 0 to 99,999."""
    payload = drawer_payload("A")
    payload["counts"]["5.00"] = value
    assert "$5 bills" in _problems(payload)["counts.5.00"]


def test_leading_zeros_in_a_quantity_are_accepted() -> None:
    """The importer accepts leading zeros too."""
    payload = drawer_payload("A")
    payload["counts"]["0.10"] = "0030"
    shift, _ = parse_drawer(payload)
    assert dict(shift.counts)[10] == 30


def test_unavailable_times_get_a_cannot_check_message() -> None:
    """Nobody is asked to guess a time."""
    problems = _problems(drawer_payload("A", opened_at=None, closed_at=None))
    assert problems == {
        "opened_at": errors.DRAWER_TIMES_UNAVAILABLE,
        "closed_at": errors.DRAWER_TIMES_UNAVAILABLE,
    }


@pytest.mark.parametrize(
    "value",
    [
        "2026-11-02 20:00",
        "2026-11-02T20:00:00",
        "2026-11-02T20:00+00:00",
        "2026-11-02T25:00",
        "20:00",
    ],
)
def test_times_must_be_a_local_date_and_minute(value: str) -> None:
    """The wire format is YYYY-MM-DDTHH:MM, stored with :00 seconds."""
    assert "closed_at" in _problems(drawer_payload("A", closed_at=value))


def test_times_keep_minutes_and_may_cross_midnight() -> None:
    """A real closing time after midnight is accepted without changes."""
    shift, _ = parse_drawer(drawer_payload("A", closed_at="2026-11-03T00:30"))
    assert shift.opened_at == "2026-11-02T08:00:00"
    assert shift.closed_at == "2026-11-03T00:30:00"


def test_closing_before_opening_is_accepted_and_flagged() -> None:
    """Genuine but inconsistent times become an R09 lead, as in the CSV path."""
    flags = _check("A", closed_at="2026-11-02T07:00").result.flags
    assert [flag.evidence["issue"] for flag in flags] == ["invalid_time_order"]


def test_negative_expected_cash_is_flagged() -> None:
    """Drops larger than the cash available produce the existing R09 lead."""
    payload = drawer_payload(
        "A", safe_drops=[{"amount": "999999.99", "bag_number": ""}]
    )
    result = check_drawer(payload, Config()).result
    assert result.expected_cents < 0
    assert "negative_expected" in [flag.evidence.get("issue") for flag in result.flags]


def test_no_safe_drops_and_an_unavailable_drop_log_stay_distinct() -> None:
    """An empty list is a confirmed none; null cannot be checked in this version."""
    shift, drops = parse_drawer(drawer_payload("A", safe_drops=[]))
    assert shift.safe_drops_cents == 0 and drops == ()
    problems = _problems(drawer_payload("A", safe_drops=None))
    assert problems == {"safe_drops": errors.DRAWER_DROPS_UNAVAILABLE}


def test_drops_are_added_by_python_and_limited() -> None:
    """Python totals the listed drops; more than 20 is refused."""
    shift, drops = parse_drawer(drawer_payload("B"))
    assert shift.safe_drops_cents == 80000
    assert [drop.bag_number for drop in drops] == [
        "DEMO-BAG-1102-R2-A",
        "DEMO-BAG-1102-R2-B",
    ]
    many = [{"amount": "1.00", "bag_number": ""}] * 21
    assert _problems(drawer_payload("A", safe_drops=many)) == {
        "safe_drops": "Enter at most 20 safe drops."
    }


def test_a_partly_entered_report_is_not_accepted() -> None:
    """Either all four report lines, or the whole report marked not available."""
    payload = drawer_payload("A")
    payload["register_report"]["cash_refunds"] = ""
    assert _problems(payload) == {"register_report.cash_refunds": "Enter cash refunds."}


def test_unused_report_figures_are_stored_as_unknown_not_zero() -> None:
    """Manual entry does not collect card sales, voids, or no-sale counts."""
    shift, _ = parse_drawer(drawer_payload("A"))
    assert shift.pos.card_sales_cents is None
    assert shift.pos.void_count is None
    assert shift.pos.no_sale_count is None
    assert shift.pos.cash_sales_cents == 84235


def test_a_recount_is_not_available_in_this_block() -> None:
    """Recounts arrive in block 7."""
    payload = drawer_payload("A", recount=drawer_payload("A")["counts"])
    assert _problems(payload) == {"recount": errors.DRAWER_RECOUNT_UNAVAILABLE}


@pytest.mark.parametrize(
    "change",
    [
        lambda payload: payload.pop("variance_note"),
        lambda payload: payload.update(extra="1"),
        lambda payload: payload["counts"].pop("0.01"),
        lambda payload: payload["counts"].update({"0.03": "1"}),
        lambda payload: payload.update(opening_float=200),
        lambda payload: payload["counts"].update({"1.00": 56}),
        lambda payload: payload.update(register_report=["842.35"]),
        lambda payload: payload.update(safe_drops={"amount": "1.00"}),
        lambda payload: payload.update(safe_drops=[{"amount": "1.00"}]),
        lambda payload: payload.update(verifier_id=None),
    ],
)
def test_a_wrongly_shaped_request_gets_one_plain_message(change) -> None:
    """Missing, extra, or non-string fields cannot be named on the page."""
    payload = drawer_payload("A")
    change(payload)
    with pytest.raises(errors.DrawerRequestError, match="unexpected, missing"):
        parse_drawer(payload)
    with pytest.raises(errors.DrawerRequestError):
        parse_drawer(["not", "an", "object"])


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("register_id", "", "Enter the register."),
        ("cashier_id", "   ", "Enter the cashier ID."),
        (
            "cashier_id",
            "cashier 01 ",
            errors.DRAWER_IDENTIFIER.format(label="The cashier ID"),
        ),
        ("register_id", "R\n2", errors.DRAWER_IDENTIFIER.format(label="The register")),
        ("register_id", "R" * 257, "The register can be at most 256 characters."),
        (
            "cashier_id",
            "cash\u200bier",
            errors.DRAWER_UNSAFE_TEXT.format(label="The cashier ID"),
        ),
        (
            "business_date",
            "20261102",
            errors.DRAWER_DATE.format(label="the business date"),
        ),
    ],
)
def test_text_fields_follow_the_importer_rules(
    field: str, value: str, message: str
) -> None:
    """IDs cannot hide spaces or control characters, and are at most 256 characters."""
    assert _problems(drawer_payload("A", **{field: value})) == {field: message}


def test_optional_sign_off_text_is_kept_or_treated_as_not_supplied() -> None:
    """A multiline note is kept; whitespace-only values mean not supplied."""
    shift, _ = parse_drawer(
        drawer_payload("B", verifier_id="  ", variance_note="Line one.\nLine two.")
    )
    assert shift.verifier_id is None
    assert shift.variance_note == "Line one.\nLine two."
    assert _problems(drawer_payload("B", variance_note="x" * 257)) == {
        "variance_note": "The note can be at most 256 characters."
    }
