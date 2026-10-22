"""Verify the generated inputs without pretending the future rules exist yet."""

import csv
import random
from collections import defaultdict
from datetime import date
from pathlib import Path

import pytest

from drawercheck import errors
from drawercheck.csv_contract import CSV_HEADERS, DENOMINATIONS_CENTS
from drawercheck.demo import generate_demo
from drawercheck.money import parse_dollars


def _rows(directory: Path, name: str) -> list[dict[str, str]]:
    with (directory / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _amounts(directory: Path) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    shifts = {row["shift_code"]: row for row in _rows(directory, "shifts.csv")}
    drops = defaultdict(int)
    for row in _rows(directory, "safe_drops.csv"):
        drops[row["shift_code"]] += parse_dollars(row["amount"])
    counted = {}
    for row in _rows(directory, "cash_counts.csv"):
        code = row["shift_code"]
        counted[code] = counted.get(code, 0) + parse_dollars(row["denomination"]) * int(
            row["quantity"]
        )
    expected = {}
    for row in _rows(directory, "pos_totals.csv"):
        code = row["shift_code"]
        expected[code] = (
            parse_dollars(shifts[code]["opening_float"])
            + parse_dollars(row["cash_sales"])
            + parse_dollars(row["paid_ins"])
            - parse_dollars(row["cash_refunds"])
            - parse_dollars(row["paid_outs"])
            - drops[code]
        )
    return expected, counted, drops


def test_demo_is_repeatable_and_does_not_change_global_random(tmp_path: Path) -> None:
    """A seed determines the files without changing other code's random state."""
    first, second = tmp_path / "first", tmp_path / "second"
    state = random.getstate()
    counts = generate_demo(first)
    assert random.getstate() == state
    assert generate_demo(second) == counts
    for name in CSV_HEADERS:
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_committed_demo_matches_default_generator(tmp_path: Path) -> None:
    """Committed fake inputs are the actual default generator's output."""
    generate_demo(tmp_path)
    committed = Path(__file__).resolve().parents[1] / "data" / "demo"
    for name in CSV_HEADERS:
        assert (tmp_path / name).read_bytes() == (committed / name).read_bytes()


@pytest.mark.parametrize("seed", [42, 17])
def test_demo_preserves_all_shift_scenarios(tmp_path: Path, seed: int) -> None:
    """The fixed scenarios survive changes to the surrounding generated data."""
    generate_demo(tmp_path, seed=seed)
    shifts = {row["shift_code"]: row for row in _rows(tmp_path, "shifts.csv")}
    expected, counted, _ = _amounts(tmp_path)
    variances = {
        code: counted[code] - value
        for code, value in expected.items()
        if code in counted
    }
    expected_variances = {
        "2026-09-03-R1": -2000,
        "2026-09-08-R2": -4500,
        "2026-09-05-R1": -600,
        "2026-09-09-R1": -800,
        "2026-09-14-R1": -700,
        "2026-09-18-R1": -900,
        "2026-09-12-R1": 500,
    }
    for code, difference in expected_variances.items():
        assert variances[code] == difference
    for code, difference in variances.items():
        if code not in expected_variances:
            assert abs(difference) < 100

    assert expected["2026-09-03-R1"] == 51875
    assert counted["2026-09-03-R1"] == 49875
    assert shifts["2026-09-03-R1"]["cashier_id"] == "cashier_02"
    assert shifts["2026-09-03-R1"]["verifier_id"] == "manager_01"
    assert shifts["2026-09-03-R1"]["variance_note"]
    assert shifts["2026-09-08-R2"]["cashier_id"] == "cashier_01"
    assert shifts["2026-09-08-R2"]["verifier_id"] == ""
    assert shifts["2026-09-08-R2"]["variance_note"] == ""
    assert shifts["2026-09-12-R1"]["cashier_id"] == "cashier_04"
    assert "2026-09-25-R1" not in counted
    assert shifts["2026-09-27-R2"]["closed_at"] < shifts["2026-09-27-R2"]["opened_at"]

    history = sorted(
        code for code, row in shifts.items() if row["cashier_id"] == "cashier_03"
    )
    qualifying = []
    for index, code in enumerate(history):
        window = history[max(0, index - 9) : index + 1]
        if sum(variances[item] <= -500 for item in window) >= 3:
            qualifying.append(code)
    assert qualifying == ["2026-09-14-R1", "2026-09-18-R1"]


def test_demo_deposits_have_deliberate_windows_and_amounts(tmp_path: Path) -> None:
    """The missing/mismatch examples do not accidentally consume later deposits."""
    generate_demo(tmp_path)
    shifts = {row["shift_code"]: row for row in _rows(tmp_path, "shifts.csv")}
    _, counted, drops = _amounts(tmp_path)
    expected_by_date = defaultdict(int)
    for code, amount in counted.items():
        expected_by_date[shifts[code]["business_date"]] += amount + drops[code] - 20000
    deposits = _rows(tmp_path, "bank_deposits.csv")
    assert not any(
        "2026-09-16" <= row["deposit_date"] <= "2026-09-19" for row in deposits
    )
    mismatch_window = [
        row for row in deposits if "2026-09-21" <= row["deposit_date"] <= "2026-09-24"
    ]
    assert len(mismatch_window) == 1
    assert (
        parse_dollars(mismatch_window[0]["amount"])
        == expected_by_date["2026-09-21"] - 10000
    )
    amounts = []
    for row in deposits:
        business_day = row["reference"].removeprefix("DEMO-DEPOSIT-")
        assert business_day not in ("2026-09-16", "2026-09-25")
        lag = (
            date.fromisoformat(row["deposit_date"]) - date.fromisoformat(business_day)
        ).days
        assert 0 <= lag <= 3
        amount = parse_dollars(row["amount"])
        assert amount == expected_by_date[business_day] - (
            10000 if business_day == "2026-09-21" else 0
        )
        amounts.append(amount)
    assert len(set(amounts)) == len(amounts)


def test_demo_uses_fixed_fake_identities_and_allowed_denominations(
    tmp_path: Path,
) -> None:
    """The default folder contains two registers and one closing shift per day."""
    counts = generate_demo(tmp_path)
    assert set(path.name for path in tmp_path.iterdir()) == set(CSV_HEADERS)
    assert counts["shifts.csv"] == 60
    assert counts["cash_counts.csv"] == 59 * 12
    assert {row["cashier_id"] for row in _rows(tmp_path, "cashiers.csv")} == {
        "cashier_01",
        "cashier_02",
        "cashier_03",
        "cashier_04",
        "manager_01",
    }
    shifts = _rows(tmp_path, "shifts.csv")
    assert min(row["business_date"] for row in shifts) == "2026-09-01"
    assert max(row["business_date"] for row in shifts) == "2026-09-30"
    assert len({(row["business_date"], row["register_id"]) for row in shifts}) == 60
    for row in _rows(tmp_path, "cash_counts.csv"):
        assert parse_dollars(row["denomination"]) in DENOMINATIONS_CENTS
        assert int(row["quantity"]) >= 0


def test_other_seeds_change_ordinary_data(tmp_path: Path) -> None:
    """The seed is actually used, rather than ignored by a fixed fixture."""
    first, second = tmp_path / "first", tmp_path / "second"
    generate_demo(first, seed=42)
    generate_demo(second, seed=43)
    assert (first / "pos_totals.csv").read_bytes() != (
        second / "pos_totals.csv"
    ).read_bytes()


@pytest.mark.parametrize("days", [1, 2, 17, 31])
def test_custom_day_counts_are_valid(tmp_path: Path, days: int) -> None:
    """Short runs need no absent scenarios and longer runs cross month boundaries."""
    counts = generate_demo(tmp_path, days=days)
    assert counts["shifts.csv"] == days * 2


@pytest.mark.parametrize("days", [0, -1, 100000000, 1.5])
def test_bad_day_counts_do_not_write_files(tmp_path: Path, days: int) -> None:
    """Invalid generation ranges fail before creating or overwriting output."""
    output = tmp_path / "demo"
    with pytest.raises(errors.UsageError, match="Demo days"):
        generate_demo(output, days=days)
    assert not output.exists()


def test_generation_preserves_unrelated_files(tmp_path: Path) -> None:
    """Generating the seven named inputs does not clear the output folder."""
    notes = tmp_path / "notes.txt"
    notes.write_text("Demo notes.")
    generate_demo(tmp_path, days=1)
    assert notes.read_text() == "Demo notes."
