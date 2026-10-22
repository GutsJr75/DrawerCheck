"""Load example policies and preserve exact settings for saved results."""

import json
import tomllib
from dataclasses import asdict, dataclass
from decimal import Decimal, DecimalException
from pathlib import Path

from drawercheck import errors
from drawercheck.money import MAX_CENTS

_POLICY_VERSION = 2

_SECTIONS = {
    "tolerance": (
        "within_tolerance_cents",
        "warn_cents",
        "review_cents",
        "review_percent_of_cash_sales",
    ),
    "repeat_short": ("min_shifts", "window"),
    "verification": ("require_verifier_and_note_at_or_above_cents",),
    "drops": ("suggest_drop_if_cash_sales_cents",),
    "deposits": ("retained_float_per_register_cents", "max_lag_days"),
}


def _bounded_percentage(value: Decimal) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite() or not 0 < value <= 100:
        raise errors.ConfigError(errors.CONFIG_PERCENT)
    sign, digits, exponent = value.as_tuple()
    # Trim zeros without normalize(), which can round using the caller's context.
    # Check precision before formatting or constructing a fraction.
    end = len(digits)
    while end > 1 and digits[end - 1] == 0:
        end -= 1
        exponent += 1
    if exponent < -6:
        raise errors.ConfigError(errors.CONFIG_PERCENT)
    return Decimal((sign, digits[:end], exponent))


@dataclass(frozen=True)
class Config:
    """Example thresholds, with all money expressed as integer cents."""

    within_tolerance_cents: int = 100
    warn_cents: int = 500
    review_cents: int = 2000
    review_percent_of_cash_sales: Decimal = Decimal("1.0")
    min_shifts: int = 3
    window: int = 10
    require_verifier_and_note_at_or_above_cents: int = 2000
    suggest_drop_if_cash_sales_cents: int = 40000
    retained_float_per_register_cents: int = 20000
    max_lag_days: int = 3

    def __post_init__(self) -> None:
        """Reject invalid policies regardless of how they were constructed."""
        for name, value in asdict(self).items():
            if name == "review_percent_of_cash_sales":
                object.__setattr__(self, name, _bounded_percentage(value))
            elif type(value) is not int or not 0 <= value <= MAX_CENTS:
                raise errors.ConfigError(errors.CONFIG_INTEGER.format(name=name))
        if not self.within_tolerance_cents < self.warn_cents <= self.review_cents:
            raise errors.ConfigError(errors.CONFIG_THRESHOLDS)
        if not 1 <= self.min_shifts <= self.window:
            raise errors.ConfigError(errors.CONFIG_HISTORY)
        if self.max_lag_days > 31:
            raise errors.ConfigError(errors.CONFIG_LAG)

    def review_threshold(self, cash_sales_cents: int) -> int:
        """Round percentage cents down, applying the warning floor and review cap."""
        numerator, denominator = self.review_percent_of_cash_sales.as_integer_ratio()
        percentage_cents = cash_sales_cents * numerator // (denominator * 100)
        return max(self.warn_cents, min(self.review_cents, percentage_cents))

    def snapshot(self) -> str:
        """Serialize the effective policies without binary floats."""
        values = asdict(self)
        values["policy_version"] = _POLICY_VERSION
        percentage = format(self.review_percent_of_cash_sales, "f")
        if "." in percentage:
            percentage = percentage.rstrip("0").rstrip(".")
        values["review_percent_of_cash_sales"] = percentage
        return json.dumps(values, sort_keys=True)


def load_config(path: str | Path) -> tuple[Config, bool]:
    """Return validated policies and whether a missing file required defaults."""
    try:
        with Path(path).open("rb") as stream:
            document = tomllib.load(stream, parse_float=Decimal)
    except FileNotFoundError:
        return Config(), True
    except (ValueError, DecimalException) as error:
        raise errors.ConfigError(errors.CONFIG_INVALID.format(path=path)) from error

    values = {}
    for section, entries in document.items():
        if section not in _SECTIONS or not isinstance(entries, dict):
            raise errors.ConfigError(errors.CONFIG_SECTION.format(section=section))
        for name, value in entries.items():
            if name not in _SECTIONS[section]:
                raise errors.ConfigError(
                    errors.CONFIG_KEY.format(section=section, name=name)
                )
            if name == "review_percent_of_cash_sales" and type(value) is int:
                value = Decimal(value)
            values[name] = value
    return Config(**values), False


def config_from_snapshot(snapshot: str) -> Config:
    """Restore a saved exact percentage and its associated policies."""
    values = json.loads(snapshot)
    if values.pop("policy_version", None) != _POLICY_VERSION:
        raise errors.ReconciliationError(errors.RESULTS_OUTDATED)
    values["review_percent_of_cash_sales"] = Decimal(
        values["review_percent_of_cash_sales"]
    )
    return Config(**values)
