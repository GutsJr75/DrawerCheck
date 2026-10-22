"""Small fictional input folders for import and CLI tests."""

from pathlib import Path

import pytest

from drawercheck.demo import generate_demo


@pytest.fixture
def csv_directory(tmp_path: Path) -> Path:
    """Provide all seven input CSVs with three days of fictional shifts."""
    directory = tmp_path / "inputs"
    generate_demo(directory, days=3)
    return directory
