"""Generate repeatable fictional CSVs with deliberately chosen review cases."""

import csv
import random
from dataclasses import dataclass, replace
from datetime import date, timedelta
from pathlib import Path

from drawercheck import errors
from drawercheck.csv_contract import CSV_HEADERS, DENOMINATIONS_CENTS
from drawercheck.money import format_cents

START_DATE = date(2026, 9, 1)
_FLOAT_CENTS = 20000
_PATTERN_DATES = {date(2026, 9, day) for day in (1, 2, 4, 5, 6, 7, 9, 10, 11, 14, 18)}
_VARIANCES = {
    (date(2026, 9, 3), "R1"): -2000,
    (date(2026, 9, 8), "R2"): -4500,
    (date(2026, 9, 5), "R1"): -600,
    (date(2026, 9, 9), "R1"): -800,
    (date(2026, 9, 14), "R1"): -700,
    (date(2026, 9, 18), "R1"): -900,
    (date(2026, 9, 12), "R1"): 500,
}


@dataclass(frozen=True)
class _DemoShift:
    """Generated input amounts, including the intended difference for testing."""

    business_date: date
    register_id: str
    cashier_id: str
    cash_sales_cents: int
    card_sales_cents: int
    cash_refunds_cents: int
    paid_outs_cents: int
    paid_ins_cents: int
    safe_drop_cents: int
    variance_cents: int
    void_count: int
    no_sale_count: int
    closed_at: str
    verifier_id: str = ""
    variance_note: str = ""

    @property
    def shift_code(self) -> str:
        """Identify the one closing shift for this register and business date."""
        return f"{self.business_date}-{self.register_id}"

    @property
    def counted_cents(self) -> int:
        """Construct the count needed to create this demo's intended difference."""
        expected = (
            _FLOAT_CENTS
            + self.cash_sales_cents
            + self.paid_ins_cents
            - self.cash_refunds_cents
            - self.paid_outs_cents
            - self.safe_drop_cents
        )
        return expected + self.variance_cents


def _dollars(cents: int) -> str:
    return format_cents(cents).replace("$", "").replace(",", "")


def _r1_cashier(business_date: date, offset: int) -> str:
    if business_date in _PATTERN_DATES:
        return "cashier_03"
    if business_date == date(2026, 9, 3):
        return "cashier_02"
    if business_date == date(2026, 9, 12):
        return "cashier_04"
    return "cashier_04" if offset % 2 else "cashier_02"


def _make_shift(
    business_date: date,
    offset: int,
    register_number: int,
    cashier_id: str,
    rng: random.Random,
) -> _DemoShift:
    register_id = f"R{register_number}"
    variance = _VARIANCES.get((business_date, register_id), rng.randint(-99, 99))
    shift = _DemoShift(
        business_date=business_date,
        register_id=register_id,
        cashier_id=cashier_id,
        cash_sales_cents=100000
        + offset * 20000
        + (register_number - 1) * 10000
        + rng.randint(0, 999),
        card_sales_cents=rng.randint(50000, 200000),
        cash_refunds_cents=rng.randint(0, 1000),
        paid_outs_cents=rng.randint(0, 500),
        paid_ins_cents=rng.randint(0, 500),
        safe_drop_cents=rng.randint(4, 8) * 10000,
        variance_cents=variance,
        void_count=rng.randint(0, 4),
        no_sale_count=rng.randint(0, 4),
        closed_at=f"{business_date}T20:00:00",
    )
    if shift.shift_code == "2026-09-03-R1":
        shift = replace(
            shift,
            cash_sales_cents=125075,
            cash_refunds_cents=1200,
            paid_outs_cents=2000,
            paid_ins_cents=0,
            safe_drop_cents=90000,
            verifier_id="manager_01",
            variance_note="Demo recount recorded for review.",
        )
    if shift.shift_code == "2026-09-27-R2":
        shift = replace(shift, closed_at="2026-09-27T07:00:00")
    return shift


def _add_shift(rows: dict[str, list[tuple[str | int, ...]]], shift: _DemoShift) -> None:
    day = shift.business_date.isoformat()
    rows["shifts.csv"].append(
        (
            shift.shift_code,
            day,
            shift.register_id,
            shift.cashier_id,
            f"{day}T08:00:00",
            shift.closed_at,
            _dollars(_FLOAT_CENTS),
            shift.verifier_id,
            shift.variance_note,
        )
    )
    rows["pos_totals.csv"].append(
        (
            shift.shift_code,
            _dollars(shift.cash_sales_cents),
            _dollars(shift.card_sales_cents),
            _dollars(shift.cash_refunds_cents),
            _dollars(shift.paid_outs_cents),
            _dollars(shift.paid_ins_cents),
            shift.void_count,
            shift.no_sale_count,
        )
    )
    rows["safe_drops.csv"].append(
        (
            shift.shift_code,
            _dollars(shift.safe_drop_cents),
            f"{day}T16:00:00",
            f"DEMO-BAG-{shift.shift_code}",
        )
    )
    if shift.shift_code == "2026-09-25-R1":
        return
    remaining = shift.counted_cents
    for denomination in DENOMINATIONS_CENTS:
        quantity, remaining = divmod(remaining, denomination)
        rows["cash_counts.csv"].append(
            (shift.shift_code, _dollars(denomination), quantity)
        )


def _add_deposit(
    rows: dict[str, list[tuple[str | int, ...]]],
    business_date: date,
    shifts: list[_DemoShift],
) -> None:
    if business_date in (date(2026, 9, 16), date(2026, 9, 25)):
        return
    amount = sum(
        shift.counted_cents + shift.safe_drop_cents - _FLOAT_CENTS for shift in shifts
    )
    if business_date == date(2026, 9, 21):
        amount -= 10000
    deposit_date = business_date
    if date(2026, 9, 17) <= business_date <= date(2026, 9, 19):
        deposit_date = date(2026, 9, 20)
    elif date(2026, 9, 22) <= business_date <= date(2026, 9, 24):
        deposit_date = date(2026, 9, 25)
    rows["bank_deposits.csv"].append(
        (
            deposit_date.isoformat(),
            _dollars(amount),
            f"DEMO-DEPOSIT-{business_date}",
        )
    )


def generate_demo(
    directory: str | Path, days: int = 30, seed: int = 42
) -> dict[str, int]:
    """Write the seven fictional demo CSVs and return their data-row counts."""
    if not isinstance(days, int) or not 1 <= days <= (date.max - START_DATE).days + 1:
        raise errors.UsageError(errors.INVALID_DEMO_DAYS)
    rng = random.Random(seed)
    rows: dict[str, list[tuple[str | int, ...]]] = {name: [] for name in CSV_HEADERS}
    rows["cashiers.csv"] = [
        (f"cashier_{number:02d}", f"Demo Cashier {number:02d}")
        for number in range(1, 5)
    ] + [("manager_01", "Demo Manager 01")]
    rows["registers.csv"] = [("R1", "Demo Register 1"), ("R2", "Demo Register 2")]

    for offset in range(days):
        business_date = START_DATE + timedelta(days=offset)
        cashier_r1 = _r1_cashier(business_date, offset)
        cashier_r2 = (
            "cashier_01"
            if cashier_r1 == "cashier_04" or business_date.day % 2 == 0
            else "cashier_04"
        )
        shifts = [
            _make_shift(business_date, offset, 1, cashier_r1, rng),
            _make_shift(business_date, offset, 2, cashier_r2, rng),
        ]
        for shift in shifts:
            _add_shift(rows, shift)
        _add_deposit(rows, business_date, shifts)

    rows["bank_deposits.csv"].sort()
    output = Path(directory)
    output.mkdir(parents=True, exist_ok=True)
    for file_name, headers in CSV_HEADERS.items():
        with (output / file_name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(headers)
            writer.writerows(rows[file_name])
    return {file_name: len(records) for file_name, records in rows.items()}
