"""Command-line entry point for DrawerCheck."""

import argparse
import json
import sqlite3
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn, TextIO

from drawercheck import db, demo, errors, importer
from drawercheck.config import load_config
from drawercheck.models import ShiftExplanation
from drawercheck.money import format_cents
from drawercheck.reconcile import explain_shift, reconcile
from drawercheck.reports import csv_out, html, load_report, text, write_report
from drawercheck.text_safety import terminal_text


class _ArgumentParser(argparse.ArgumentParser):
    """Report usage errors through the shared application messages."""

    def error(self, message: str) -> NoReturn:
        """Raise a usage error so main() can return exit code 1."""
        raise errors.UsageError(errors.INVALID_ARGUMENTS.format(detail=message))


def _build_parser() -> _ArgumentParser:
    parser = _ArgumentParser(
        prog="drawercheck",
        description="Offline cash-drawer checks for Demo Store #001 (fake data only).",
        epilog="Includes repeated-shortage checks and simplified bank-deposit matching.",
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

    check = commands.add_parser(
        "reconcile", help="Calculate cash differences and save review flags."
    )
    check.add_argument("--from", dest="from_date")
    check.add_argument("--to", dest="to_date")
    check.add_argument("--db", type=Path, default=Path("drawercheck.db"))
    check.add_argument("--config", type=Path, default=Path("config.toml"))

    explain = commands.add_parser(
        "explain", help="Show a reconciled shift's math and review flags."
    )
    explain.add_argument("shift_code")
    explain.add_argument("--db", type=Path, default=Path("drawercheck.db"))

    report = commands.add_parser(
        "report", help="Create a text, offline HTML, or protected CSV report."
    )
    report.add_argument("--date")
    report.add_argument("--from", dest="from_date")
    report.add_argument("--to", dest="to_date")
    report.add_argument("--format", choices=("text", "html", "csv"), default="text")
    report.add_argument("--out", type=Path)
    report.add_argument("--db", type=Path, default=Path("drawercheck.db"))
    return parser


def _print_line(message: object, *, file: TextIO | None = None) -> None:
    print(terminal_text(message), file=file)


def _money_or_unknown(cents: int | None) -> str:
    return "unknown" if cents is None else format_cents(cents)


def _print_explanation(explanation: ShiftExplanation) -> None:
    result, config = explanation.result, explanation.config
    shift = result.shift
    _print_line("DEMO DATA ONLY: Demo Store #001")
    _print_line(
        f"Shift: {shift.shift_code} | Register: {shift.register_id} | Cashier: {shift.cashier_id}"
    )
    status = (
        "balanced within tolerance" if result.status == "balanced" else result.status
    )
    _print_line(f"Status: {status}")
    _print_line(f"Opened: {shift.opened_at} | Closed: {shift.closed_at or 'open'}")
    _print_line(
        "Expected drawer = opening float + cash sales + paid-ins - refunds - paid-outs - safe drops"
    )
    _print_line(f"  Opening float: {format_cents(shift.opening_float_cents)}")
    for label, name in (
        ("Cash sales", "cash_sales_cents"),
        ("Paid-ins", "paid_ins_cents"),
        ("Cash refunds", "cash_refunds_cents"),
        ("Paid-outs", "paid_outs_cents"),
    ):
        _print_line(
            f"  {label}: {_money_or_unknown(getattr(shift.pos, name) if shift.pos else None)}"
        )
    _print_line(f"  Safe drops: {format_cents(shift.safe_drops_cents)}")
    _print_line(f"  Expected drawer: {_money_or_unknown(result.expected_cents)}")
    _print_line("Counted drawer = denomination x quantity, added together")
    for denomination, quantity in shift.counts:
        _print_line(f"  {format_cents(denomination)} x {quantity}")
    if not shift.counts:
        _print_line("  No cash-count rows; cash is unknown.")
    _print_line(f"  Counted drawer: {_money_or_unknown(result.counted_cents)}")
    _print_line(
        f"Variance = counted - expected: {_money_or_unknown(result.variance_cents)}"
    )
    _print_line(f"Tolerance: {format_cents(config.within_tolerance_cents)}")
    threshold = (
        config.review_threshold(shift.pos.cash_sales_cents) if shift.pos else None
    )
    _print_line(f"Review threshold: {_money_or_unknown(threshold)}")
    _print_line("Thresholds are saved example policies, not industry standards.")
    _print_line(
        f"Verifier: {shift.verifier_id or 'missing'} | Note: {shift.variance_note or 'missing'}"
    )
    _print_line("Deposit contribution = counted + safe drops - retained float")
    _print_line(
        f"  Retained float per register: {format_cents(config.retained_float_per_register_cents)}"
    )
    _print_line(
        f"  Shift deposit contribution: {_money_or_unknown(explanation.deposit_contribution_cents)}"
    )
    _print_line(
        f"  Expected daily deposit (all registers): {_money_or_unknown(explanation.daily_deposit_cents)}"
    )
    _print_line(
        "Includes repeated-shortage checks and simplified bank matching. Review daily leads for deposit exceptions."
    )
    _print_line("Review leads, not findings about a person:")
    if not result.flags:
        _print_line("  No review flags for this shift.")
    for flag in result.flags:
        _print_line(f"  [{flag.severity}] {flag.rule_code}: {flag.message}")
        _print_line(f"    Evidence: {json.dumps(flag.evidence, sort_keys=True)}")

    if explanation.daily_flags:
        _print_line("Daily review leads:")
        for flag in explanation.daily_flags:
            _print_line(f"  [{flag.severity}] {flag.rule_code}: {flag.message}")
            _print_line(f"    Evidence: {json.dumps(flag.evidence, sort_keys=True)}")


def _run_command(arguments: argparse.Namespace) -> None:
    db.check_version()
    if arguments.command == "init-db":
        db.initialize(arguments.db)
        _print_line(errors.DATABASE_INITIALIZED.format(path=arguments.db))
    elif arguments.command == "demo-data":
        counts = demo.generate_demo(arguments.out, arguments.days, arguments.seed)
        _print_line(errors.DEMO_CREATED.format(days=arguments.days, path=arguments.out))
        for file_name, count in counts.items():
            _print_line(errors.FILE_GENERATED.format(file_name=file_name, rows=count))
    elif arguments.command == "import":
        for result in importer.import_directory(arguments.directory, arguments.db):
            if result.skipped:
                _print_line(
                    errors.FILE_ALREADY_IMPORTED.format(file_name=result.file_name)
                )
            else:
                _print_line(
                    errors.FILE_IMPORTED.format(
                        file_name=result.file_name, rows=result.rows_imported
                    )
                )
    elif arguments.command == "reconcile":
        config, missing = load_config(arguments.config)
        if missing:
            _print_line(errors.CONFIG_MISSING.format(path=arguments.config))
        result = reconcile(arguments.db, config, arguments.from_date, arguments.to_date)
        _print_line(
            errors.RECONCILED.format(
                shifts=len(result.shifts),
                start=result.from_date,
                end=result.to_date,
                flags=len(result.flags),
            )
        )
    elif arguments.command == "explain":
        _print_explanation(explain_shift(arguments.db, arguments.shift_code))
    elif arguments.command == "report":
        report = load_report(
            arguments.db, arguments.from_date, arguments.to_date, date=arguments.date
        )
        content = {"text": text.render, "html": html.render, "csv": csv_out.render}[
            arguments.format
        ](report)
        if arguments.out is None:
            sys.stdout.write(content)
        else:
            write_report(arguments.out, content, arguments.db)
            _print_line(
                errors.REPORT_WRITTEN.format(
                    format=arguments.format.upper(), path=arguments.out
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
        _print_line(error, file=sys.stderr)
        return 1
    except sqlite3.DatabaseError as error:
        _print_line(errors.database_error_message(error), file=sys.stderr)
        return 1
    except OSError as error:
        _print_line(
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
