"""Check exact cents, strict dollar input, and readable currency output."""

from decimal import FloatOperation, localcontext

import pytest

from drawercheck import errors
from drawercheck.money import MAX_CENTS, MIN_CENTS, format_cents, parse_dollars


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0.00", 0),
        ("0.10", 10),
        ("1250.75", 125075),
        ("-20.00", -2000),
        ("-0.00", 0),
        ("0001.20", 120),
        ("92233720368547758.07", MAX_CENTS),
        ("-92233720368547758.08", MIN_CENTS),
    ],
)
def test_parse_dollars_returns_integer_cents(value: str, expected: int) -> None:
    """Valid values produce exact integer cents, including the storage limits."""
    actual = parse_dollars(value)
    assert actual == expected
    assert isinstance(actual, int)


@pytest.mark.parametrize(
    "value",
    [
        "",
        "1",
        "1.0",
        "1.000",
        "1.230",
        "1e3",
        "1e3.00",
        "1_000.00",
        "NaN",
        "Infinity",
        "$1.00",
        "1,000.00",
        "+1.00",
        " 1.00",
        "1.00 ",
        "1.00\n",
        "\t1.00",
        ".10",
        "1.",
        "--1.00",
        "１２.３４",
    ],
)
def test_parse_dollars_rejects_bad_spelling(value: str) -> None:
    """Invalid spellings use the central error instead of silently rounding."""
    with pytest.raises(errors.MoneyValidationError) as caught:
        parse_dollars(value)
    assert str(caught.value) == errors.INVALID_MONEY.format(value=value)


@pytest.mark.parametrize(
    "value",
    ["92233720368547758.08", "-92233720368547758.09", "999999999999999999999999.99"],
)
def test_parse_dollars_rejects_storage_overflow(value: str) -> None:
    """Money outside SQLite's integer limits is rejected before storage."""
    with pytest.raises(errors.MoneyValidationError) as caught:
        parse_dollars(value)
    assert str(caught.value) == errors.MONEY_OUT_OF_RANGE.format(value=value)


def test_parse_dollars_stays_exact_when_decimal_precision_changes() -> None:
    """Money parsing does not depend on ambient precision or float conversion."""
    with localcontext() as context:
        context.prec = 2
        context.traps[FloatOperation] = True
        assert parse_dollars("1234.56") == 123456
        assert parse_dollars("92233720368547758.07") == MAX_CENTS


@pytest.mark.parametrize(
    ("cents", "expected"),
    [
        (0, "$0.00"),
        (1, "$0.01"),
        (10, "$0.10"),
        (100, "$1.00"),
        (125075, "$1,250.75"),
        (-1, "-$0.01"),
        (-2000, "-$20.00"),
        (9_007_199_254_740_993, "$90,071,992,547,409.93"),
        (MAX_CENTS, "$92,233,720,368,547,758.07"),
        (MIN_CENTS, "-$92,233,720,368,547,758.08"),
    ],
)
def test_format_cents(cents: int, expected: str) -> None:
    """Currency keeps its sign, grouping, and exact two-digit cents."""
    assert format_cents(cents) == expected
