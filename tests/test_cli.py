"""Check the milestone's help command and clear usage failures."""

import pytest

from drawercheck import errors
from drawercheck.cli import main


@pytest.mark.parametrize("argv", [["--help"], []])
def test_help_returns_success(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """Help is available directly through main() without terminating the test."""
    assert main(argv) == 0
    output = capsys.readouterr()
    assert "usage: drawercheck" in output.out
    assert "Demo Store #001" in output.out
    assert "M1 foundation" in output.out
    assert output.err == ""


def test_unknown_argument_returns_one(capsys: pytest.CaptureFixture[str]) -> None:
    """Invalid arguments use the shared error, stderr, and exit code 1."""
    assert main(["--unknown"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err.strip() == errors.INVALID_ARGUMENTS.format(
        detail="unrecognized arguments: --unknown"
    )
    assert "Traceback" not in output.err
