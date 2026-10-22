"""Command-line entry point for DrawerCheck."""

import argparse
import sys
from collections.abc import Sequence
from typing import NoReturn

from drawercheck import errors


class _ArgumentParser(argparse.ArgumentParser):
    """Report usage errors through the shared application messages."""

    def error(self, message: str) -> NoReturn:
        """Raise a usage error so main() can return exit code 1."""
        raise errors.UsageError(errors.INVALID_ARGUMENTS.format(detail=message))


def main(argv: Sequence[str] | None = None) -> int:
    """Print help or a clear usage error and return the process exit code."""
    parser = _ArgumentParser(
        prog="drawercheck",
        description="Offline cash-drawer checks for Demo Store #001 (fake data only).",
        epilog="M1 foundation: import, reconciliation, and reports arrive later.",
    )
    try:
        parser.parse_args(argv)
    except errors.UsageError as error:
        print(error, file=sys.stderr)
        return 1
    except SystemExit as exit_info:
        # argparse uses SystemExit for --help; keep main(argv) directly testable.
        return int(exit_info.code)

    parser.print_help()
    return 0
