"""Command-line entry point for DrawerCheck."""

import argparse
import sqlite3
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from drawercheck import db, demo, errors, importer


class _ArgumentParser(argparse.ArgumentParser):
    """Report usage errors through the shared application messages."""

    def error(self, message: str) -> NoReturn:
        """Raise a usage error so main() can return exit code 1."""
        raise errors.UsageError(errors.INVALID_ARGUMENTS.format(detail=message))


def _build_parser() -> _ArgumentParser:
    parser = _ArgumentParser(
        prog="drawercheck",
        description="Offline cash-drawer checks for Demo Store #001 (fake data only).",
        epilog="Reconciliation and reports arrive in later milestones.",
    )
    commands = parser.add_subparsers(dest="command")
    initialize = commands.add_parser(
        "init-db", help="Create the SQLite database tables."
    )
    initialize.add_argument("--db", type=Path, default=Path("drawercheck.db"))

    generate = commands.add_parser(
        "demo-data", help="Write repeatable fictional CSV files."
    )
    generate.add_argument("--out", type=Path, default=Path("data/demo"))
    generate.add_argument("--days", type=int, default=30)
    generate.add_argument("--seed", type=int, default=42)

    load = commands.add_parser(
        "import", help="Validate and import the seven CSV files."
    )
    load.add_argument("--dir", dest="directory", type=Path, required=True)
    load.add_argument("--db", type=Path, default=Path("drawercheck.db"))
    return parser


def _run_command(arguments: argparse.Namespace) -> None:
    db.check_version()
    if arguments.command == "init-db":
        db.initialize(arguments.db)
        print(errors.DATABASE_INITIALIZED.format(path=arguments.db))
    elif arguments.command == "demo-data":
        counts = demo.generate_demo(arguments.out, arguments.days, arguments.seed)
        print(errors.DEMO_CREATED.format(days=arguments.days, path=arguments.out))
        for file_name, count in counts.items():
            print(errors.FILE_GENERATED.format(file_name=file_name, rows=count))
    elif arguments.command == "import":
        for result in importer.import_directory(arguments.directory, arguments.db):
            if result.skipped:
                print(errors.FILE_ALREADY_IMPORTED.format(file_name=result.file_name))
            else:
                print(
                    errors.FILE_IMPORTED.format(
                        file_name=result.file_name, rows=result.rows_imported
                    )
                )


def main(argv: Sequence[str] | None = None) -> int:
    """Run a command and translate expected failures into short error messages."""
    parser = _build_parser()
    try:
        arguments = parser.parse_args(argv)
        if arguments.command is None:
            parser.print_help()
            return 0
        _run_command(arguments)
    except errors.DrawerCheckError as error:
        print(error, file=sys.stderr)
        return 1
    except sqlite3.DatabaseError as error:
        print(errors.database_error_message(error), file=sys.stderr)
        return 1
    except OSError as error:
        print(
            errors.FILE_ACCESS_ERROR.format(
                path=error.filename or "the requested path",
                detail=error.strerror or str(error),
            ),
            file=sys.stderr,
        )
        return 1
    except SystemExit as exit_info:
        # argparse uses SystemExit for --help; keep main(argv) directly testable.
        return int(exit_info.code)

    return 0
