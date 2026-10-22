"""Small fictional input folders for import and CLI tests."""

from pathlib import Path

import pytest

from drawercheck.demo import generate_demo
from drawercheck.importer import import_directory
from drawercheck.models import PosTotals, Shift


@pytest.fixture
def csv_directory(tmp_path: Path) -> Path:
    """Provide all seven input CSVs with three days of fictional shifts."""
    directory = tmp_path / "inputs"
    generate_demo(directory, days=3)
    return directory


@pytest.fixture
def worked_shift() -> Shift:
    """Provide the brief's independent count and POS worked example."""
    return Shift(
        id=1,
        shift_code="2026-09-03-R1",
        business_date="2026-09-03",
        register_id="R1",
        cashier_id="cashier_02",
        opened_at="2026-09-03T08:00:00",
        closed_at="2026-09-03T16:00:00",
        opening_float_cents=20000,
        verifier_id="manager_01",
        variance_note="Demo recount.",
        pos=PosTotals(125075, 345678, 1200, 2000, 0, 0, 0),
        counts=((10000, 4), (5000, 1), (2000, 2), (500, 1), (100, 3), (25, 3)),
        safe_drops_cents=90000,
    )


@pytest.fixture
def demo_database(tmp_path: Path) -> Path:
    """Import the full fictional month into an isolated database."""
    directory = tmp_path / "full-demo"
    generate_demo(directory)
    path = tmp_path / "full-demo.db"
    import_directory(directory, path)
    return path
