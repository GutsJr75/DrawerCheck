"""Exercise CSV validation, transaction rollback, and repeated imports."""

import csv
import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from drawercheck import db, errors
from drawercheck.csv_contract import CSV_HEADERS, DENOMINATIONS_CENTS
from drawercheck.importer import import_directory

_SNAPSHOT_QUERIES = {
    "cashiers": "SELECT * FROM cashiers ORDER BY id",
    "registers": "SELECT * FROM registers ORDER BY id",
    "shifts": "SELECT * FROM shifts ORDER BY id",
    "pos_totals": "SELECT * FROM pos_totals ORDER BY shift_id",
    "safe_drops": "SELECT * FROM safe_drops ORDER BY id",
    "cash_counts": "SELECT * FROM cash_counts ORDER BY shift_id, denomination_cents",
    "bank_deposits": "SELECT * FROM bank_deposits ORDER BY id",
    "flags": "SELECT * FROM flags ORDER BY id",
    "import_log": "SELECT * FROM import_log ORDER BY id",
}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _write(
    path: Path, rows: list[dict[str, str]], headers: tuple[str, ...] | None = None
) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers or CSV_HEADERS[path.name])
        writer.writeheader()
        writer.writerows(rows)


def _change(directory: Path, file_name: str, column: str, value: str) -> None:
    path = directory / file_name
    rows = _rows(path)
    rows[0][column] = value
    _write(path, rows)


def _snapshot(path: Path) -> dict[str, list[tuple]]:
    with closing(db.connect(path)) as con:
        return {
            table: [tuple(row) for row in con.execute(query)]
            for table, query in _SNAPSHOT_QUERIES.items()
        }


def _seed_flag(path: Path) -> None:
    with closing(db.connect(path)) as con:
        with con:
            con.execute(
                """INSERT INTO flags (business_date, rule_code, severity, message, evidence_json)
                   VALUES (?, ?, ?, ?, ?)""",
                ("2026-09-01", "DEMO_REVIEW", "info", "Demo review record.", "{}"),
            )


def test_import_creates_schema_and_stores_exact_money(
    csv_directory: Path, tmp_path: Path
) -> None:
    """A fresh database receives all records, references, and integer money."""
    path = tmp_path / "demo.db"
    results = import_directory(csv_directory, path)
    assert [result.file_name for result in results] == list(CSV_HEADERS)
    assert all(not result.skipped for result in results)
    for result in results:
        assert result.rows_imported == len(_rows(csv_directory / result.file_name))

    with closing(db.connect(path)) as con:
        row = con.execute(
            """SELECT p.cash_sales_cents, typeof(p.cash_sales_cents) AS storage_type
               FROM pos_totals p JOIN shifts s ON s.id = p.shift_id
               WHERE s.shift_code = ?""",
            ("2026-09-03-R1",),
        ).fetchone()
        assert row["cash_sales_cents"] == 125075
        assert row["storage_type"] == "integer"
        assert con.execute("PRAGMA foreign_key_check").fetchall() == []
        for file_name in CSV_HEADERS:
            logged = con.execute(
                "SELECT sha256 FROM import_log WHERE file_name = ?", (file_name,)
            ).fetchone()
            assert (
                logged[0]
                == hashlib.sha256((csv_directory / file_name).read_bytes()).hexdigest()
            )


def test_repeated_import_preserves_every_table(
    csv_directory: Path, tmp_path: Path
) -> None:
    """Identical bytes do not change records, flags, or the import log."""
    path = tmp_path / "demo.db"
    import_directory(csv_directory, path)
    _seed_flag(path)
    before = _snapshot(path)
    results = import_directory(csv_directory, path)
    assert all(result.skipped and result.rows_imported == 0 for result in results)
    assert _snapshot(path) == before


@pytest.mark.parametrize(
    ("file_name", "column", "value"),
    [
        ("cashiers.csv", "display_name", ""),
        ("registers.csv", "label", ""),
        ("shifts.csv", "business_date", "2026-02-30"),
        ("pos_totals.csv", "cash_sales", "1.234"),
        ("safe_drops.csv", "amount", "-1.00"),
        ("cash_counts.csv", "quantity", "-1"),
        ("bank_deposits.csv", "deposit_date", "2026-02-30"),
    ],
)
def test_bad_row_has_location_and_rolls_back_all_files(
    csv_directory: Path, tmp_path: Path, file_name: str, column: str, value: str
) -> None:
    """A failure in any file preserves every existing table and log row."""
    path = tmp_path / "demo.db"
    db.initialize(path)
    with closing(db.connect(path)) as con:
        with con:
            con.execute(
                "INSERT INTO cashiers (id, display_name) VALUES (?, ?)",
                ("existing_01", "Demo Existing Cashier"),
            )
    _seed_flag(path)
    before = _snapshot(path)
    _change(csv_directory, file_name, column, value)
    with pytest.raises(errors.ImportValidationError) as caught:
        import_directory(csv_directory, path)
    error = caught.value
    assert (error.file_name, error.line_number, error.column) == (file_name, 2, column)
    assert str(error).startswith(f"{file_name}: line 2, column {column}:")
    assert _snapshot(path) == before


def test_failure_also_rolls_back_new_schema(
    csv_directory: Path, tmp_path: Path
) -> None:
    """A late validation error leaves no tables in a newly opened database."""
    path = tmp_path / "demo.db"
    _change(csv_directory, "bank_deposits.csv", "amount", "0.00")
    with pytest.raises(errors.ImportValidationError):
        import_directory(csv_directory, path)
    with closing(db.connect(path)) as con:
        assert (
            con.execute(
                "SELECT name FROM sqlite_schema WHERE type = 'table'"
            ).fetchall()
            == []
        )


@pytest.mark.parametrize("file_name", list(CSV_HEADERS))
def test_duplicate_records_name_both_lines(
    csv_directory: Path, tmp_path: Path, file_name: str
) -> None:
    """Every input's business key rejects a repeated row with both locations."""
    path = csv_directory / file_name
    rows = _rows(path)
    second_line = len(rows) + 2
    rows.append(rows[0].copy())
    _write(path, rows)
    with pytest.raises(errors.ImportValidationError) as caught:
        import_directory(csv_directory, tmp_path / "demo.db")
    assert caught.value.file_name == file_name
    assert caught.value.line_number == second_line
    assert "first on line 2" in str(caught.value)
    assert f"repeated on line {second_line}" in str(caught.value)


def test_count_duplicate_uses_numeric_denomination(
    csv_directory: Path, tmp_path: Path
) -> None:
    """Different spellings of the same denomination cannot bypass the key."""
    path = csv_directory / "cash_counts.csv"
    rows = _rows(path)
    repeated = rows[0].copy()
    repeated["denomination"] = "0100.00"
    rows.append(repeated)
    _write(path, rows)
    with pytest.raises(errors.ImportValidationError, match="Duplicate record"):
        import_directory(csv_directory, tmp_path / "demo.db")


@pytest.mark.parametrize(
    ("content", "line", "column", "detail"),
    [
        (b"", 1, "<header>", "empty"),
        (b"\n,\n \n", 1, "<header>", "empty"),
        (b"\xef\xbb\xbf", 1, "<header>", "empty"),
        (b"cashier_01,Demo Cashier\n", 1, "<header>", "Missing required columns"),
        (b"cashier_id\ncashier_01\n", 1, "<header>", "display_name"),
        (b"cashier_ID,display_name\ncashier_01,Demo\n", 1, "<header>", "cashier_id"),
        (b"cashier_id,display_name,extra\n", 1, "<header>", "Unexpected columns"),
        (b"cashier_id,display_name,cashier_id\n", 1, "<header>", "Duplicate header"),
        (
            b"cashier_id,display_name\ncashier_01\n",
            2,
            "<row>",
            "Expected 2 columns; found 1",
        ),
        (b"cashier_id,display_name\ncashier_01,Demo,extra\n", 2, "<row>", "found 3"),
        (b'cashier_id,display_name\ncashier_01,"Demo\n', 2, "<row>", "Malformed CSV"),
        (b'cashier_id,display_name\ncashier_01,"Demo"x\n', 2, "<row>", "Malformed CSV"),
        (b"cashier_id,display_name\ncashier_01,\xff\n", 2, "<encoding>", "UTF-8"),
    ],
)
def test_malformed_csv_is_explained(
    csv_directory: Path,
    tmp_path: Path,
    content: bytes,
    line: int,
    column: str,
    detail: str,
) -> None:
    """File and record structure failures have readable source locations."""
    (csv_directory / "cashiers.csv").write_bytes(content)
    with pytest.raises(errors.ImportValidationError) as caught:
        import_directory(csv_directory, tmp_path / "demo.db")
    error = caught.value
    assert (error.file_name, error.line_number, error.column) == (
        "cashiers.csv",
        line,
        column,
    )
    assert detail in str(error)


@pytest.mark.parametrize(
    "variation",
    ["bom", "lf", "crlf", "blank", "quoted", "multiline", "unicode", "reordered"],
)
def test_common_spreadsheet_csv_variations_import(
    csv_directory: Path, tmp_path: Path, variation: str
) -> None:
    """BOMs, quoting, reordered headers, and line endings keep the same records."""
    source = csv_directory / "cashiers.csv"
    rows = _rows(source)
    name = "Demo Cashier 01"
    if variation == "quoted":
        name = 'Demo, Cashier "01"'
    elif variation == "multiline":
        name = "Demo\nCashier 01"
    elif variation == "unicode":
        name = "Demo Caissier É"
    rows[0]["display_name"] = name
    headers = (
        tuple(reversed(CSV_HEADERS[source.name])) if variation == "reordered" else None
    )
    _write(source, rows, headers)
    data = source.read_bytes()
    if variation == "bom":
        data = b"\xef\xbb\xbf" + data
    elif variation == "lf":
        data = data.replace(b"\r\n", b"\n")
    elif variation == "blank":
        data = b"\n\n" + data.replace(b"\r\n", b"\r\n\r\n,,\r\n")
    source.write_bytes(data)
    path = tmp_path / "demo.db"
    import_directory(csv_directory, path)
    with closing(db.connect(path)) as con:
        assert (
            con.execute(
                "SELECT display_name FROM cashiers WHERE id = ?", ("cashier_01",)
            ).fetchone()[0]
            == name
        )
        assert con.execute("SELECT COUNT(*) FROM cashiers").fetchone()[0] == 5


def test_multiline_record_errors_use_physical_start_lines(
    csv_directory: Path, tmp_path: Path
) -> None:
    """An earlier quoted newline does not shift later error locations."""
    (csv_directory / "cashiers.csv").write_text(
        'cashier_id,display_name\ncashier_01,"Demo\nCashier 01"\ncashier_02,\n',
        encoding="utf-8",
    )
    with pytest.raises(errors.ImportValidationError) as caught:
        import_directory(csv_directory, tmp_path / "demo.db")
    assert caught.value.line_number == 4
    assert caught.value.column == "display_name"


def test_header_only_files_import_zero_rows(
    csv_directory: Path, tmp_path: Path
) -> None:
    """Seven header-only files are valid and log zero imported records."""
    for file_name in CSV_HEADERS:
        _write(csv_directory / file_name, [])
    path = tmp_path / "demo.db"
    results = import_directory(csv_directory, path)
    assert all(result.rows_imported == 0 and not result.skipped for result in results)
    snapshot = _snapshot(path)
    assert len(snapshot.pop("import_log")) == 7
    assert all(not records for records in snapshot.values())


def test_missing_file_does_not_open_database(
    csv_directory: Path, tmp_path: Path
) -> None:
    """A missing member of the seven-file contract fails before writing."""
    (csv_directory / "bank_deposits.csv").unlink()
    path = tmp_path / "demo.db"
    with pytest.raises(FileNotFoundError):
        import_directory(csv_directory, path)
    assert not path.exists()


@pytest.mark.parametrize(
    ("file_name", "column"),
    [
        ("shifts.csv", "register_id"),
        ("shifts.csv", "cashier_id"),
        ("shifts.csv", "verifier_id"),
        ("pos_totals.csv", "shift_code"),
        ("safe_drops.csv", "shift_code"),
        ("cash_counts.csv", "shift_code"),
    ],
)
def test_unknown_references_name_the_column(
    csv_directory: Path, tmp_path: Path, file_name: str, column: str
) -> None:
    """References to absent records have precise errors before SQLite rejects them."""
    _change(csv_directory, file_name, column, "DEMO-MISSING")
    with pytest.raises(errors.ImportValidationError) as caught:
        import_directory(csv_directory, tmp_path / "demo.db")
    assert caught.value.column == column
    assert caught.value.line_number == 2
    assert "DEMO-MISSING" in str(caught.value)


@pytest.mark.parametrize("value", ["3.00", "0.02", "1000.00", "0.00"])
def test_unknown_denominations_are_rejected(
    csv_directory: Path, tmp_path: Path, value: str
) -> None:
    """Only the specified bills and coins are valid count denominations."""
    _change(csv_directory, "cash_counts.csv", "denomination", value)
    with pytest.raises(errors.ImportValidationError) as caught:
        import_directory(csv_directory, tmp_path / "demo.db")
    assert caught.value.column == "denomination"
    assert errors.UNKNOWN_DENOMINATION.format(value=value) in str(caught.value)


@pytest.mark.parametrize(
    "value", ["-1", "1.0", "+1", " 1", "1e3", "١", "9223372036854775808", "9" * 5000]
)
def test_invalid_quantities_are_rejected(
    csv_directory: Path, tmp_path: Path, value: str
) -> None:
    """Quantities cannot be fractions, signed text, or overflowing integers."""
    _change(csv_directory, "cash_counts.csv", "quantity", value)
    with pytest.raises(errors.ImportValidationError) as caught:
        import_directory(csv_directory, tmp_path / "demo.db")
    assert caught.value.column == "quantity"


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("business_date", "20260901"),
        ("business_date", "2026-02-30"),
        ("opened_at", "2026-09-01 08:00:00"),
        ("opened_at", "2026-09-01T08:00"),
        ("opened_at", "2026-09-01T08:00:00Z"),
        ("opened_at", "2026-09-01T08:00:00+01:00"),
        ("closed_at", "2026-09-01T20:00:00.000"),
        ("closed_at", "2026-02-30T20:00:00"),
    ],
)
def test_dates_and_times_require_exact_format(
    csv_directory: Path, tmp_path: Path, column: str, value: str
) -> None:
    """Valid-looking alternate ISO forms are outside the fixed input contract."""
    _change(csv_directory, "shifts.csv", column, value)
    with pytest.raises(errors.ImportValidationError) as caught:
        import_directory(csv_directory, tmp_path / "demo.db")
    assert caught.value.column == column


def test_empty_optional_shift_fields_become_null(
    csv_directory: Path, tmp_path: Path
) -> None:
    """An open shift can omit its closing time, verifier, and note."""
    _change(csv_directory, "shifts.csv", "closed_at", "")
    path = tmp_path / "demo.db"
    import_directory(csv_directory, path)
    with closing(db.connect(path)) as con:
        row = con.execute(
            "SELECT closed_at, verifier_id, variance_note FROM shifts WHERE shift_code = ?",
            ("2026-09-01-R1",),
        ).fetchone()
        assert tuple(row) == (None, None, None)


def test_changed_existing_records_are_not_silently_updated(
    csv_directory: Path, tmp_path: Path
) -> None:
    """Changed snapshots cannot overwrite records that were already imported."""
    path = tmp_path / "demo.db"
    import_directory(csv_directory, path)
    before = _snapshot(path)
    _change(csv_directory, "cashiers.csv", "display_name", "Demo Changed Name")
    with pytest.raises(errors.ImportValidationError, match="already exists"):
        import_directory(csv_directory, path)
    assert _snapshot(path) == before


def test_new_records_clear_old_results_atomically(
    csv_directory: Path, tmp_path: Path
) -> None:
    """New facts invalidate saved flags and any existing completion markers."""
    path = tmp_path / "demo.db"
    import_directory(csv_directory, path)
    _seed_flag(path)
    with closing(db.connect(path)) as con:
        with con:
            con.execute(
                "CREATE TABLE reconciled_dates (business_date TEXT PRIMARY KEY) STRICT"
            )
            con.execute("INSERT INTO reconciled_dates VALUES (?)", ("2026-09-01",))
    _write(
        csv_directory / "bank_deposits.csv",
        [{"deposit_date": "2026-10-01", "amount": "1.00", "reference": "DEMO-NEW"}],
    )
    results = import_directory(csv_directory, path)
    assert sum(result.rows_imported for result in results) == 1
    with closing(db.connect(path)) as con:
        assert con.execute("SELECT COUNT(*) FROM flags").fetchone()[0] == 0
        assert con.execute("SELECT COUNT(*) FROM reconciled_dates").fetchone()[0] == 0


def test_schema_protects_denomination_and_integer_types(
    csv_directory: Path, tmp_path: Path
) -> None:
    """Direct writes still obey denomination checks and STRICT integer storage."""
    path = tmp_path / "demo.db"
    import_directory(csv_directory, path)
    with closing(db.connect(path)) as con:
        shift_id = con.execute("SELECT id FROM shifts ORDER BY id LIMIT 1").fetchone()[
            0
        ]
        with con:
            con.execute("DELETE FROM cash_counts WHERE shift_id = ?", (shift_id,))
        with pytest.raises(sqlite3.IntegrityError):
            with con:
                con.execute(
                    "INSERT INTO cash_counts VALUES (?, ?, ?)", (shift_id, 300, 1)
                )
        with pytest.raises(sqlite3.IntegrityError):
            with con:
                con.execute(
                    "INSERT INTO cash_counts VALUES (?, ?, ?)", (shift_id, 100, "1.5")
                )
        with con:
            for denomination in DENOMINATIONS_CENTS:
                con.execute(
                    "INSERT INTO cash_counts VALUES (?, ?, ?)",
                    (shift_id, denomination, 0),
                )
