"""Validate and import the seven CSV files in one SQLite transaction."""

import csv
import hashlib
import re
import sqlite3
from collections.abc import Mapping
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, date, datetime
from io import StringIO
from pathlib import Path
from typing import NoReturn

from drawercheck import db, errors
from drawercheck.csv_contract import CSV_HEADERS, DENOMINATIONS_CENTS
from drawercheck.money import MAX_CENTS, parse_dollars
from drawercheck.text_safety import has_unsafe_controls

_IDENTIFIER_COLUMNS = {"cashier_id", "register_id", "shift_code", "verifier_id"}

_KEY_COLUMNS = {
    "cashiers.csv": ("cashier_id",),
    "registers.csv": ("register_id",),
    "shifts.csv": ("shift_code",),
    "pos_totals.csv": ("shift_code",),
    "safe_drops.csv": ("shift_code", "amount", "dropped_at", "bag_number"),
    "cash_counts.csv": ("shift_code", "denomination"),
    "bank_deposits.csv": ("deposit_date", "amount", "reference"),
}


@dataclass(frozen=True)
class ImportResult:
    """The committed row count or skip status for one input file."""

    file_name: str
    rows_imported: int
    skipped: bool = False


@dataclass(frozen=True)
class _CsvRow:
    """One row and the source location used by its value checks."""

    file_name: str
    line_number: int
    values: dict[str, str]

    def fail(self, column: str, detail: str) -> NoReturn:
        """Raise a validation error with this row's source location."""
        raise errors.ImportValidationError(
            self.file_name, self.line_number, column, detail
        )

    def _text(self, column: str) -> str:
        value = self.values[column]
        if has_unsafe_controls(value):
            self.fail(column, errors.UNSAFE_TEXT)
        if column in _IDENTIFIER_COLUMNS and (
            value != value.strip() or any(character in value for character in "\n\r\t")
        ):
            self.fail(column, errors.INVALID_IDENTIFIER)
        return value

    def required(self, column: str) -> str:
        """Read required text without silently changing its contents."""
        value = self._text(column)
        if not value.strip():
            self.fail(column, errors.REQUIRED_VALUE)
        return value

    def optional(self, column: str) -> str | None:
        """Represent an empty optional field as SQL NULL."""
        value = self._text(column)
        return value if value.strip() else None

    def money(self, column: str, *, positive: bool = False) -> int:
        """Read exact cents and enforce the column's allowed sign."""
        try:
            cents = parse_dollars(self.required(column))
        except errors.MoneyValidationError as error:
            self.fail(column, str(error))
        if positive and cents <= 0:
            self.fail(column, errors.POSITIVE_MONEY)
        if cents < 0:
            self.fail(column, errors.NONNEGATIVE_MONEY)
        return cents

    def integer(self, column: str) -> int:
        """Read an unsigned whole number within SQLite's storage limit."""
        value = self.required(column)
        if re.fullmatch(r"[0-9]+", value) is None:
            self.fail(column, errors.INVALID_INTEGER)
        digits = value.lstrip("0") or "0"
        if len(digits) > 19:
            self.fail(column, errors.INTEGER_OUT_OF_RANGE)
        number = int(digits)
        if number > MAX_CENTS:
            self.fail(column, errors.INTEGER_OUT_OF_RANGE)
        return number

    def date_value(self, column: str) -> str:
        """Read a real date written exactly as YYYY-MM-DD."""
        value = self.required(column)
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            self.fail(column, errors.INVALID_DATE)
        if parsed.isoformat() != value:
            self.fail(column, errors.INVALID_DATE)
        return value

    def timestamp(self, column: str) -> str:
        """Read a local timestamp with seconds and no timezone."""
        value = self.required(column)
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            self.fail(column, errors.INVALID_TIMESTAMP)
        if parsed.tzinfo is not None or parsed.isoformat(timespec="seconds") != value:
            self.fail(column, errors.INVALID_TIMESTAMP)
        return value


def _check_headers(file_name: str, line_number: int, headers: list[str]) -> None:
    duplicates = sorted({name for name in headers if headers.count(name) > 1})
    missing = [name for name in CSV_HEADERS[file_name] if name not in headers]
    extra = [name for name in headers if name not in CSV_HEADERS[file_name]]
    if duplicates:
        detail = errors.DUPLICATE_HEADER.format(columns=", ".join(duplicates))
    elif missing:
        detail = errors.MISSING_COLUMNS.format(columns=", ".join(missing))
    elif extra:
        detail = errors.EXTRA_COLUMNS.format(columns=", ".join(extra))
    else:
        return
    raise errors.ImportValidationError(file_name, line_number, "<header>", detail)


def _read_rows(
    file_name: str,
    data: bytes,
    max_rows: int | None = None,
    max_field_characters: int | None = None,
) -> list[_CsvRow]:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        prefix = error.object[: error.start]
        line_number = len(re.findall(rb"\r\n|\r|\n", prefix)) + 1
        raise errors.ImportValidationError(
            file_name, line_number, "<encoding>", errors.INVALID_ENCODING
        ) from error

    rows = []
    headers = None
    with StringIO(text, newline="") as stream:
        reader = csv.reader(stream, strict=True)
        while True:
            line_number = reader.line_num + 1
            try:
                values = next(reader)
            except StopIteration:
                break
            except csv.Error as error:
                reason = "malformed_csv"
                if str(error) == "unexpected end of data":
                    reason = "unclosed_quote"
                elif str(error).startswith("field larger than field limit"):
                    reason = "long_csv_value"
                raise errors.ImportValidationError(
                    file_name,
                    line_number,
                    "<row>",
                    errors.MALFORMED_CSV.format(detail=error),
                    reason=reason,
                ) from error
            if not values or all(not value.strip() for value in values):
                continue
            if headers is None:
                _check_headers(file_name, line_number, values)
                headers = values
            elif len(values) != len(headers):
                raise errors.ImportValidationError(
                    file_name,
                    line_number,
                    "<row>",
                    errors.WRONG_ROW_WIDTH.format(
                        expected=len(headers), actual=len(values)
                    ),
                )
            else:
                if max_rows is not None and len(rows) >= max_rows:
                    raise errors.ImportRowLimitError(file_name, max_rows)
                if max_field_characters is not None:
                    for column, value in zip(headers, values):
                        if len(value) > max_field_characters:
                            raise errors.ImportValidationError(
                                file_name,
                                line_number,
                                column,
                                errors.CSV_VALUE_LENGTH.format(
                                    limit=max_field_characters
                                ),
                            )
                rows.append(_CsvRow(file_name, line_number, dict(zip(headers, values))))
    if headers is None:
        raise errors.ImportValidationError(file_name, 1, "<header>", errors.EMPTY_CSV)
    return rows


def _check_duplicate(
    row: _CsvRow, seen: dict[tuple[str | int | None, ...], int]
) -> None:
    columns = _KEY_COLUMNS[row.file_name]
    key = tuple(
        row.money(column, positive=column == "amount")
        if column in ("amount", "denomination")
        else row.optional(column)
        for column in columns
    )
    if key in seen:
        row.fail(
            ", ".join(columns),
            errors.DUPLICATE_ROW.format(
                columns=", ".join(columns), first=seen[key], second=row.line_number
            ),
        )
    seen[key] = row.line_number


def _new_record(
    con: sqlite3.Connection,
    row: _CsvRow,
    column: str,
    query: str,
    values: tuple[str | int | None, ...],
) -> None:
    if con.execute(query, values).fetchone() is not None:
        row.fail(column, errors.RECORD_EXISTS)


def _reference(
    con: sqlite3.Connection, row: _CsvRow, column: str, query: str
) -> str | int:
    value = row.required(column)
    record = con.execute(query, (value,)).fetchone()
    if record is None:
        row.fail(column, errors.UNKNOWN_REFERENCE.format(column=column, value=value))
    return record[0]


def _shift_id(con: sqlite3.Connection, row: _CsvRow) -> int:
    return int(
        _reference(con, row, "shift_code", "SELECT id FROM shifts WHERE shift_code = ?")
    )


def _import_cashier(con: sqlite3.Connection, row: _CsvRow) -> None:
    cashier_id = row.required("cashier_id")
    _new_record(
        con, row, "cashier_id", "SELECT 1 FROM cashiers WHERE id = ?", (cashier_id,)
    )
    con.execute(
        "INSERT INTO cashiers (id, display_name) VALUES (?, ?)",
        (cashier_id, row.required("display_name")),
    )


def _import_register(con: sqlite3.Connection, row: _CsvRow) -> None:
    register_id = row.required("register_id")
    _new_record(
        con, row, "register_id", "SELECT 1 FROM registers WHERE id = ?", (register_id,)
    )
    con.execute(
        "INSERT INTO registers (id, label) VALUES (?, ?)",
        (register_id, row.required("label")),
    )


def _import_shift(con: sqlite3.Connection, row: _CsvRow) -> None:
    shift_code = row.required("shift_code")
    _new_record(
        con,
        row,
        "shift_code",
        "SELECT 1 FROM shifts WHERE shift_code = ?",
        (shift_code,),
    )
    register_id = _reference(
        con, row, "register_id", "SELECT id FROM registers WHERE id = ?"
    )
    cashier_id = _reference(
        con, row, "cashier_id", "SELECT id FROM cashiers WHERE id = ?"
    )
    verifier_id = row.optional("verifier_id")
    if verifier_id is not None:
        _reference(con, row, "verifier_id", "SELECT id FROM cashiers WHERE id = ?")
    closed_at = (
        row.timestamp("closed_at") if row.optional("closed_at") is not None else None
    )
    con.execute(
        """INSERT INTO shifts (
            shift_code, business_date, register_id, cashier_id, opened_at,
            closed_at, opening_float_cents, verifier_id, variance_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            shift_code,
            row.date_value("business_date"),
            register_id,
            cashier_id,
            row.timestamp("opened_at"),
            closed_at,
            row.money("opening_float"),
            verifier_id,
            row.optional("variance_note"),
        ),
    )


def _import_pos(con: sqlite3.Connection, row: _CsvRow) -> None:
    shift_id = _shift_id(con, row)
    _new_record(
        con,
        row,
        "shift_code",
        "SELECT 1 FROM pos_totals WHERE shift_id = ?",
        (shift_id,),
    )
    con.execute(
        """INSERT INTO pos_totals (
            shift_id, cash_sales_cents, card_sales_cents, cash_refunds_cents,
            paid_outs_cents, paid_ins_cents, void_count, no_sale_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            shift_id,
            row.money("cash_sales"),
            row.money("card_sales"),
            row.money("cash_refunds"),
            row.money("paid_outs"),
            row.money("paid_ins"),
            row.integer("void_count"),
            row.integer("no_sale_count"),
        ),
    )


def _import_drop(con: sqlite3.Connection, row: _CsvRow) -> None:
    values = (
        _shift_id(con, row),
        row.money("amount", positive=True),
        row.timestamp("dropped_at"),
        row.optional("bag_number"),
    )
    _new_record(
        con,
        row,
        "shift_code",
        """SELECT 1 FROM safe_drops WHERE shift_id = ? AND amount_cents = ?
           AND dropped_at = ? AND bag_number IS ?""",
        values,
    )
    con.execute(
        "INSERT INTO safe_drops (shift_id, amount_cents, dropped_at, bag_number) VALUES (?, ?, ?, ?)",
        values,
    )


def _import_count(con: sqlite3.Connection, row: _CsvRow) -> None:
    shift_id = _shift_id(con, row)
    denomination = row.money("denomination")
    if denomination not in DENOMINATIONS_CENTS:
        row.fail(
            "denomination",
            errors.UNKNOWN_DENOMINATION.format(value=row.values["denomination"]),
        )
    _new_record(
        con,
        row,
        "denomination",
        "SELECT 1 FROM cash_counts WHERE shift_id = ? AND denomination_cents = ?",
        (shift_id, denomination),
    )
    con.execute(
        "INSERT INTO cash_counts (shift_id, denomination_cents, quantity) VALUES (?, ?, ?)",
        (shift_id, denomination, row.integer("quantity")),
    )


def _import_deposit(con: sqlite3.Connection, row: _CsvRow) -> None:
    values = (
        row.date_value("deposit_date"),
        row.money("amount", positive=True),
        row.optional("reference"),
    )
    _new_record(
        con,
        row,
        "deposit_date",
        "SELECT 1 FROM bank_deposits WHERE deposit_date = ? AND amount_cents = ? AND reference IS ?",
        values,
    )
    con.execute(
        "INSERT INTO bank_deposits (deposit_date, amount_cents, reference) VALUES (?, ?, ?)",
        values,
    )


_IMPORTERS = {
    "cashiers.csv": _import_cashier,
    "registers.csv": _import_register,
    "shifts.csv": _import_shift,
    "pos_totals.csv": _import_pos,
    "safe_drops.csv": _import_drop,
    "cash_counts.csv": _import_count,
    "bank_deposits.csv": _import_deposit,
}


def import_directory(
    directory: str | Path,
    database_path: str | Path,
    *,
    row_limits: Mapping[str, int] | None = None,
    max_field_characters: int | None = None,
) -> list[ImportResult]:
    """Import all seven CSVs atomically and return committed per-file results."""
    sources = []
    for file_name in CSV_HEADERS:
        data = (Path(directory) / file_name).read_bytes()
        sources.append(
            (
                file_name,
                hashlib.sha256(data).hexdigest(),
                _read_rows(
                    file_name,
                    data,
                    row_limits.get(file_name) if row_limits else None,
                    max_field_characters,
                ),
            )
        )

    results = []
    with closing(db.connect(database_path)) as con:
        with con:
            db.create_schema(con)
            for file_name, digest, rows in sources:
                if con.execute(
                    "SELECT 1 FROM import_log WHERE sha256 = ?", (digest,)
                ).fetchone():
                    results.append(ImportResult(file_name, 0, skipped=True))
                    continue
                seen = {}
                for row in rows:
                    _check_duplicate(row, seen)
                    try:
                        _IMPORTERS[file_name](con, row)
                    except sqlite3.IntegrityError as error:
                        raise errors.ImportValidationError(
                            file_name, row.line_number, "<row>", errors.RECORD_CONFLICT
                        ) from error
                con.execute(
                    """INSERT INTO import_log (file_name, sha256, rows_imported, imported_at)
                       VALUES (?, ?, ?, ?)""",
                    (
                        file_name,
                        digest,
                        len(rows),
                        datetime.now(UTC).isoformat(timespec="seconds"),
                    ),
                )
                results.append(ImportResult(file_name, len(rows)))
            if any(result.rows_imported for result in results):
                con.execute("DELETE FROM flags")
                if con.execute(
                    "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = ?",
                    ("reconciled_dates",),
                ).fetchone():
                    con.execute("DELETE FROM reconciled_dates")
    return results
