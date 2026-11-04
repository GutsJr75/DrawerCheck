"""Check one manually entered drawer with the same calculations and rules as imports."""

import re
from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import Literal

from drawercheck import errors
from drawercheck.config import Config
from drawercheck.csv_contract import DENOMINATIONS_CENTS
from drawercheck.models import PosTotals, Shift, ShiftResult
from drawercheck.money import format_cents, parse_dollars
from drawercheck.reconcile import shift_outcome
from drawercheck.rules import (
    denomination_flags,
    integrity_flags,
    transposition_flags,
    variance_flags,
    verification_flags,
)
from drawercheck.text_safety import has_unsafe_controls

MAX_TEXT_CHARACTERS = 256
MAX_AMOUNT_CENTS = 99_999_999
MAX_QUANTITY = 99_999
MAX_SAFE_DROPS = 20
# "100.00" -> 10000, in the count sheet's order from the largest bill down.
COUNT_KEYS = {format_cents(cents)[1:]: cents for cents in DENOMINATIONS_CENTS}
DRAWER_KEYS = frozenset(
    {
        "business_date",
        "register_id",
        "cashier_id",
        "opened_at",
        "closed_at",
        "opening_float",
        "counts",
        "recount",
        "register_report",
        "safe_drops",
        "verifier_id",
        "variance_note",
    }
)
REPORT_KEYS = ("cash_sales", "cash_refunds", "paid_ins", "paid_outs")
DROP_KEYS = frozenset({"amount", "bag_number"})
# The CSV path's rule order without R04, so both paths list leads identically.
DRAWER_RULES = (
    variance_flags,
    denomination_flags,
    transposition_flags,
    verification_flags,
    integrity_flags,
)
DIFFERENCE_RULES = (
    "R01_VARIANCE",
    "R02_SINGLE_DENOMINATION",
    "R03_TRANSPOSITION_HINT",
    "R05_MISSING_VERIFIER_OR_NOTE",
)
_MONEY_PATTERN = re.compile(r"[0-9]+\.[0-9]{2}")
_DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

RAN_NO_LEAD = "Ran on the known difference. No lead."
RAN_LEAD = "Ran on the known difference. A lead was found."
NOT_RUN_DIFFERENCE = (
    "Not run: the difference is unknown, because expected cash is unknown."
)
SIGN_OFF_NOT_CONFIRMED = " A clear result does not confirm who signed."
OWN_RECORDS_ONLY = "Ran on this drawer's own records only."
NOT_RUN_HISTORY = "Not run: no earlier shifts are available for this cashier."
NOT_RUN_DEPOSIT = "Not run: one drawer is not a whole day with bank records."
CHECKED_REPORT = "Whether the register report figures are present."
CHECKED_TIMES = "Whether the closing time is after the opening time."
CHECKED_NEGATIVE = "Whether expected cash is negative."
UNAVAILABLE_NEGATIVE = "Whether expected cash is negative: expected cash is unknown."
UNAVAILABLE_WIDER = (
    "Whether other drawers on this register overlap: no other drawers were entered.",
    "Whether this register has a second closing that day: no other drawers were entered.",
    "Whether any register has no drawer that day: no register list was entered.",
)


@dataclass(frozen=True)
class SafeDrop:
    """One entered safe drop; Python adds the amounts."""

    amount_cents: int
    bag_number: str | None


@dataclass(frozen=True)
class Coverage:
    """Whether one rule ran on this drawer, decided from its inputs."""

    rule_code: str
    state: Literal["ran_no_lead", "ran_lead", "not_run"]
    detail: str
    partial: bool = False
    checked: tuple[str, ...] = ()
    unavailable: tuple[str, ...] = ()


@dataclass(frozen=True)
class DrawerCheck:
    """The outcome, entered drops, and check coverage for one drawer."""

    result: ShiftResult
    safe_drops: tuple[SafeDrop, ...]
    coverage: tuple[Coverage, ...]


def _sentence(label: str) -> str:
    # str.capitalize() would also lowercase "ID".
    return label[0].upper() + label[1:]


def _shape(value: object, keys: frozenset[str] | tuple[str, ...]) -> dict:
    if not isinstance(value, dict) or set(value) != set(keys):
        raise errors.DrawerRequestError(errors.DRAWER_SHAPE)
    return value


def _string(value: object) -> str:
    if not isinstance(value, str):
        raise errors.DrawerRequestError(errors.DRAWER_SHAPE)
    return value


class _Fields:
    """Collect every field problem so the page can list them together."""

    def __init__(self) -> None:
        self.problems: list[tuple[str, str]] = []

    def fail(self, field: str, message: str) -> None:
        self.problems.append((field, message))

    def text(
        self, field: str, name: str, value: object, *, required: bool, identifier: bool
    ) -> str | None:
        value = _string(value)
        label = errors.DRAWER_LABELS[name]
        if has_unsafe_controls(value):
            return self.fail(
                field, errors.DRAWER_UNSAFE_TEXT.format(label=_sentence(label))
            )
        if len(value) > MAX_TEXT_CHARACTERS:
            return self.fail(
                field,
                errors.DRAWER_TOO_LONG.format(
                    label=_sentence(label), limit=MAX_TEXT_CHARACTERS
                ),
            )
        if not value.strip():
            if required:
                self.fail(field, errors.DRAWER_REQUIRED.format(label=label))
            return None
        if identifier and (
            value != value.strip() or any(character in value for character in "\n\r\t")
        ):
            return self.fail(
                field, errors.DRAWER_IDENTIFIER.format(label=_sentence(label))
            )
        return value

    def business_date(self, value: object) -> str | None:
        value = _string(value)
        label = errors.DRAWER_LABELS["business_date"]
        try:
            valid = _DATE_PATTERN.fullmatch(value) and date.fromisoformat(value)
        except ValueError:
            valid = None
        if not valid:
            return self.fail("business_date", errors.DRAWER_DATE.format(label=label))
        return value

    def time(self, field: str, value: object) -> str | None:
        if value is None:
            return self.fail(field, errors.DRAWER_TIMES_UNAVAILABLE)
        value = _string(value)
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            parsed = None
        if (
            parsed is None
            or parsed.tzinfo is not None
            or parsed.isoformat(timespec="minutes") != value
        ):
            label = errors.DRAWER_LABELS[field]
            return self.fail(field, errors.DRAWER_TIME.format(label=label))
        # Reports print minutes; the core stores local times with seconds.
        return parsed.isoformat(timespec="seconds")

    def money(
        self, field: str, name: str, value: object, *, positive: bool = False
    ) -> int | None:
        value = _string(value)
        label = errors.DRAWER_LABELS[name]
        if not value.strip():
            return self.fail(field, errors.DRAWER_REQUIRED.format(label=label))
        if _MONEY_PATTERN.fullmatch(value) is None:
            return self.fail(field, errors.DRAWER_MONEY.format(label=label))
        try:
            cents = parse_dollars(value)
        except errors.MoneyValidationError:
            cents = MAX_AMOUNT_CENTS + 1
        if cents > MAX_AMOUNT_CENTS:
            return self.fail(
                field,
                errors.DRAWER_MONEY_LIMIT.format(
                    label=_sentence(label), limit=format_cents(MAX_AMOUNT_CENTS)
                ),
            )
        if positive and cents == 0:
            return self.fail(field, errors.DRAWER_DROP_POSITIVE)
        return cents

    def quantity(self, field: str, denomination: int, value: object) -> int | None:
        value = _string(value)
        what = errors.drawer_count_name(denomination)
        if re.fullmatch(r"[0-9]+", value) is None:
            return self.fail(field, errors.DRAWER_COUNT.format(what=what))
        digits = value.lstrip("0") or "0"
        if len(digits) > len(str(MAX_QUANTITY)) or int(digits) > MAX_QUANTITY:
            return self.fail(
                field, errors.DRAWER_COUNT_LIMIT.format(what=what, limit=MAX_QUANTITY)
            )
        return int(digits)


def _pos_totals(fields: _Fields, value: object) -> PosTotals | None:
    if value is None:
        return None
    report = _shape(value, REPORT_KEYS)
    amounts = {
        key: fields.money(f"register_report.{key}", key, report[key])
        for key in REPORT_KEYS
    }
    if None in amounts.values():
        return None
    # Manual entry does not collect card sales, voids, or no-sale counts.
    return PosTotals(
        amounts["cash_sales"],
        None,
        amounts["cash_refunds"],
        amounts["paid_outs"],
        amounts["paid_ins"],
        None,
        None,
    )


def _safe_drops(fields: _Fields, value: object) -> tuple[SafeDrop, ...]:
    if value is None:
        fields.fail("safe_drops", errors.DRAWER_DROPS_UNAVAILABLE)
        return ()
    if not isinstance(value, list):
        raise errors.DrawerRequestError(errors.DRAWER_SHAPE)
    if len(value) > MAX_SAFE_DROPS:
        fields.fail("safe_drops", errors.DRAWER_DROP_LIMIT.format(limit=MAX_SAFE_DROPS))
        return ()
    drops = []
    for number, item in enumerate(value, start=1):
        entry = _shape(item, DROP_KEYS)
        amount = fields.money(
            f"safe_drops.{number}.amount", "amount", entry["amount"], positive=True
        )
        bag = fields.text(
            f"safe_drops.{number}.bag_number",
            "bag_number",
            entry["bag_number"],
            required=False,
            identifier=False,
        )
        if amount is not None:
            drops.append(SafeDrop(amount, bag))
    return tuple(drops)


def parse_drawer(payload: object) -> tuple[Shift, tuple[SafeDrop, ...]]:
    """Validate manual entries and build an in-memory shift, rejecting any guesswork."""
    data = _shape(payload, DRAWER_KEYS)
    fields = _Fields()
    business_date = fields.business_date(data["business_date"])
    register_id = fields.text(
        "register_id",
        "register_id",
        data["register_id"],
        required=True,
        identifier=True,
    )
    cashier_id = fields.text(
        "cashier_id", "cashier_id", data["cashier_id"], required=True, identifier=True
    )
    opened_at = fields.time("opened_at", data["opened_at"])
    closed_at = fields.time("closed_at", data["closed_at"])
    opening_float = fields.money(
        "opening_float", "opening_float", data["opening_float"]
    )
    count_values = _shape(data["counts"], tuple(COUNT_KEYS))
    counts = tuple(
        (cents, fields.quantity(f"counts.{key}", cents, count_values[key]))
        for key, cents in COUNT_KEYS.items()
    )
    if data["recount"] is not None:
        fields.fail("recount", errors.DRAWER_RECOUNT_UNAVAILABLE)
    pos = _pos_totals(fields, data["register_report"])
    drops = _safe_drops(fields, data["safe_drops"])
    verifier_id = fields.text(
        "verifier_id",
        "verifier_id",
        data["verifier_id"],
        required=False,
        identifier=True,
    )
    note = fields.text(
        "variance_note",
        "variance_note",
        data["variance_note"],
        required=False,
        identifier=False,
    )
    if fields.problems:
        raise errors.DrawerInputError(tuple(fields.problems))
    shift = Shift(
        id=1,
        shift_code=f"{business_date}-{register_id}",
        business_date=business_date,
        register_id=register_id,
        cashier_id=cashier_id,
        opened_at=opened_at,
        closed_at=closed_at,
        opening_float_cents=opening_float,
        verifier_id=verifier_id,
        variance_note=note,
        pos=pos,
        counts=counts,
        safe_drops_cents=sum(drop.amount_cents for drop in drops),
    )
    return shift, drops


def check_coverage(result: ShiftResult) -> tuple[Coverage, ...]:
    """Report which rules ran from the inputs, never from whether a lead appeared."""
    codes = {flag.rule_code for flag in result.flags}
    entries = []
    for code in DIFFERENCE_RULES:
        if result.variance_cents is None:
            entries.append(Coverage(code, "not_run", NOT_RUN_DIFFERENCE))
        elif code in codes:
            entries.append(Coverage(code, "ran_lead", RAN_LEAD))
        else:
            detail = RAN_NO_LEAD
            if code == "R05_MISSING_VERIFIER_OR_NOTE":
                detail += SIGN_OFF_NOT_CONFIRMED
            entries.append(Coverage(code, "ran_no_lead", detail))
    expected_known = result.expected_cents is not None
    entries.append(
        Coverage(
            "R09_DATA_INTEGRITY",
            "ran_lead" if "R09_DATA_INTEGRITY" in codes else "ran_no_lead",
            OWN_RECORDS_ONLY,
            partial=True,
            checked=(CHECKED_REPORT, CHECKED_TIMES)
            + ((CHECKED_NEGATIVE,) if expected_known else ()),
            unavailable=(() if expected_known else (UNAVAILABLE_NEGATIVE,))
            + UNAVAILABLE_WIDER,
        )
    )
    entries.append(Coverage("R04_REPEAT_SHORT", "not_run", NOT_RUN_HISTORY))
    entries.append(Coverage("R08_DEPOSIT", "not_run", NOT_RUN_DEPOSIT))
    return tuple(entries)


def check_drawer(payload: object, config: Config) -> DrawerCheck:
    """Check one entered drawer with the applicable rules, called one by one."""
    shift, drops = parse_drawer(payload)
    outcome = shift_outcome(shift, config)
    flags = tuple(flag for rule in DRAWER_RULES for flag in rule(outcome, config))
    result = replace(outcome, flags=flags)
    return DrawerCheck(result, drops, check_coverage(result))
