"""Check every dangerous spreadsheet prefix and ordinary cells."""

import pytest

from drawercheck.csv_safety import sanitize_cell


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@", "\t", "\r"])
def test_formula_prefix_is_preserved_and_protected(prefix: str) -> None:
    """A leading quote neutralizes formula-like input without deleting its contents."""
    value = prefix + "DEMO(1)"
    assert sanitize_cell(value) == "'" + value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "Demo Cashier",
        "2026-09-01",
        "123.45",
        "'already quoted",
        "Demo = 2",
        "É",
        " normal",
    ],
)
def test_ordinary_cells_are_unchanged(value: str) -> None:
    """Normal data and already quoted strings remain readable."""
    assert sanitize_cell(value) == value
