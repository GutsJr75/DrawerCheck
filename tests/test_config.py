"""Verify exact policy loading, validation, and saved-policy round trips."""

from dataclasses import replace
from decimal import Decimal, localcontext
from pathlib import Path

import pytest

from drawercheck import errors
from drawercheck.config import Config, config_from_snapshot, load_config
from drawercheck.money import MAX_CENTS


def test_committed_config_matches_all_defaults() -> None:
    """The supplied example preserves every default from the brief."""
    settings, missing = load_config(Path(__file__).parents[1] / "config.toml")
    assert settings == Config()
    assert not missing


def test_missing_config_and_partial_config(tmp_path: Path) -> None:
    """Missing files and omitted settings use defaults without hiding malformed files."""
    path = tmp_path / "config.toml"
    assert load_config(path) == (Config(), True)
    path.write_text(
        "[deposits]\nmax_lag_days = 0\n[tolerance]\nreview_percent_of_cash_sales = 2\n"
    )
    settings, missing = load_config(path)
    assert not missing
    assert settings == replace(
        Config(), max_lag_days=0, review_percent_of_cash_sales=Decimal(2)
    )


@pytest.mark.parametrize(
    "content",
    [
        b"[tolerance",
        b"\xff",
        b"[other]\nvalue = 1",
        b"tolerance = 1",
        b"[tolerance]\nwarn_cent = 500",
        b"[deposits]\nmax_lag_days = true",
        b"[tolerance]\nwarn_cents = 500.0",
        b'[tolerance]\nwarn_cents = "500"',
        b"[tolerance]\nreview_percent_of_cash_sales = true",
        b'[tolerance]\nreview_percent_of_cash_sales = "1.0"',
        b"[tolerance]\nreview_percent_of_cash_sales = nan",
        b"[tolerance]\nreview_percent_of_cash_sales = inf",
        b"[tolerance]\nreview_percent_of_cash_sales = 0.0",
        b"[tolerance]\nreview_percent_of_cash_sales = -1.0",
    ],
)
def test_bad_config_is_an_error(tmp_path: Path, content: bytes) -> None:
    """Invalid files never silently fall back to defaults."""
    path = tmp_path / "config.toml"
    path.write_bytes(content)
    with pytest.raises(errors.ConfigError):
        load_config(path)


@pytest.mark.parametrize(
    "changes",
    [
        {"within_tolerance_cents": -1},
        {"within_tolerance_cents": 500},
        {"warn_cents": 2001},
        {"review_cents": 499},
        {"warn_cents": True},
        {"warn_cents": MAX_CENTS + 1},
        {"min_shifts": 0},
        {"window": 2},
        {"max_lag_days": -1},
        {"retained_float_per_register_cents": -1},
        {"require_verifier_and_note_at_or_above_cents": -1},
        {"suggest_drop_if_cash_sales_cents": -1},
        {"review_percent_of_cash_sales": 1.0},
        {"review_percent_of_cash_sales": Decimal("NaN")},
        {"review_percent_of_cash_sales": Decimal("Infinity")},
    ],
)
def test_programmatic_settings_are_validated(changes: dict) -> None:
    """Callers outside the CLI cannot accidentally bypass policy checks."""
    with pytest.raises(errors.ConfigError):
        replace(Config(), **changes)


@pytest.mark.parametrize(
    ("sales", "threshold"),
    [
        (0, 500),
        (49999, 500),
        (50000, 500),
        (100099, 1000),
        (125075, 1250),
        (199999, 1999),
        (200000, 2000),
        (MAX_CENTS, 2000),
    ],
)
def test_percentage_floor_rounding_and_cap(sales: int, threshold: int) -> None:
    """The percent calculation uses whole cents at each boundary."""
    assert Config().review_threshold(sales) == threshold


def test_decimal_context_cannot_change_settings_or_results(tmp_path: Path) -> None:
    """Low external Decimal precision cannot round a saved percentage or its threshold."""
    path = tmp_path / "config.toml"
    path.write_text("[tolerance]\nreview_percent_of_cash_sales = 1.234567\n")
    with localcontext() as context:
        context.prec = 2
        settings, _ = load_config(path)
        assert settings.review_percent_of_cash_sales == Decimal("1.234567")
        assert settings.review_threshold(100000) == 1234
        assert config_from_snapshot(settings.snapshot()) == settings
    assert (
        Config().snapshot()
        == replace(Config(), review_percent_of_cash_sales=Decimal("1")).snapshot()
    )


def test_config_permission_failure_is_not_a_missing_file(tmp_path: Path) -> None:
    """A directory supplied as a config path remains a real filesystem error."""
    with pytest.raises(OSError):
        load_config(tmp_path)


@pytest.mark.parametrize(
    "kind", ["huge_integer", "invalid_exponent", "syntax", "encoding"]
)
def test_config_error_distinguishes_numbers_from_file_format(
    tmp_path: Path, kind: str
) -> None:
    """Numeric conversion failures explain the number rather than blaming valid UTF-8 TOML."""
    path = tmp_path / "policy.toml"
    content = {
        "huge_integer": ("[tolerance]\nwarn_cents = " + "9" * 5000 + "\n").encode(),
        "invalid_exponent": b"[tolerance]\nreview_percent_of_cash_sales = 1e9999999999999999999\n",
        "syntax": b"[tolerance\n",
        "encoding": b"\xff",
    }[kind]
    path.write_bytes(content)
    with pytest.raises(errors.ConfigError) as caught:
        load_config(path)
    message = str(caught.value)
    assert str(path) in message
    if kind in ("huge_integer", "invalid_exponent"):
        assert "number" in message and "range" in message
        assert "UTF-8" not in message
    else:
        assert message == errors.CONFIG_INVALID.format(path=path)
