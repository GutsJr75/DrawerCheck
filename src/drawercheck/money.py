"""Parse dollar strings and format integer cents without using floats."""

import re
from decimal import Decimal

from drawercheck import errors

MIN_CENTS = -(2**63)
MAX_CENTS = 2**63 - 1
_DOLLAR_PATTERN = re.compile(r"-?[0-9]+\.[0-9]{2}")


def parse_dollars(value: str) -> int:
    """Convert an exact two-decimal dollar string to integer cents."""
    if _DOLLAR_PATTERN.fullmatch(value) is None:
        raise errors.MoneyValidationError(errors.INVALID_MONEY.format(value=value))

    dollars = Decimal(value)
    numerator, denominator = dollars.as_integer_ratio()
    # The exact fraction avoids rounding, even if Decimal precision was changed.
    cents = numerator * 100 // denominator
    if not MIN_CENTS <= cents <= MAX_CENTS:
        raise errors.MoneyValidationError(errors.MONEY_OUT_OF_RANGE.format(value=value))
    return cents


def format_cents(cents: int) -> str:
    """Format integer cents as currency, such as $1,234.56 or -$20.00."""
    sign = "-" if cents < 0 else ""
    dollars, remaining_cents = divmod(abs(cents), 100)
    return f"{sign}${dollars:,}.{remaining_cents:02d}"
