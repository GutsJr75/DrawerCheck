"""Expected application errors and their user-facing messages."""

import sqlite3

INVALID_MONEY = (
    "Invalid money value {value!r}. "
    "Use dollars with exactly two decimal places, such as 1250.75."
)
MONEY_OUT_OF_RANGE = (
    "Money value {value!r} is outside the supported range of integer cents."
)
SQLITE_TOO_OLD = (
    "SQLite 3.37.0 or newer is required; found {version}. "
    "Use a Python installation with a newer SQLite."
)
INVALID_ARGUMENTS = "Invalid command: {detail}. Run 'drawercheck --help' for usage."
IMPORT_VALIDATION = "{file_name}: line {line_number}, column {column}: {detail}"
EMPTY_CSV = "The file is empty or has no header."
MISSING_COLUMNS = "Missing required columns: {columns}."
EXTRA_COLUMNS = "Unexpected columns: {columns}."
DUPLICATE_HEADER = "Duplicate header columns: {columns}."
WRONG_ROW_WIDTH = "Expected {expected} columns; found {actual}."
MALFORMED_CSV = "Malformed CSV: {detail}."
INVALID_ENCODING = "Use UTF-8 encoding; this file contains invalid UTF-8 bytes."
REQUIRED_VALUE = "A value is required."
NONNEGATIVE_MONEY = "The amount must be zero or greater."
POSITIVE_MONEY = "The amount must be greater than zero."
INVALID_INTEGER = "Use a whole number that is zero or greater."
INTEGER_OUT_OF_RANGE = "The whole number is too large for SQLite integer storage."
INVALID_DATE = "Use a valid date in YYYY-MM-DD format."
INVALID_TIMESTAMP = "Use a valid local date and time in YYYY-MM-DDTHH:MM:SS format."
UNKNOWN_REFERENCE = (
    "Unknown {column} {value!r}. Add its matching record to the input CSVs."
)
UNKNOWN_DENOMINATION = (
    "Unknown denomination {value!r}. Use an allowed bill or coin value."
)
DUPLICATE_ROW = (
    "Duplicate record for {columns}: first on line {first}, repeated on line {second}."
)
RECORD_EXISTS = (
    "This record already exists. Import new records only, or use a fresh database."
)
RECORD_CONFLICT = "This record conflicts with existing data or a database constraint."
INVALID_DEMO_DAYS = (
    "Demo days must be a positive whole number within the supported date range."
)
FILE_ACCESS_ERROR = "Cannot access {path}: {detail}."
DATABASE_LOCKED = "Database is locked. Close other database commands and try again."
DATABASE_READ_ONLY = "Database is read-only. Choose a writable path with --db."
DATABASE_ERROR = (
    "Cannot use the database: {detail}. Check the path and file permissions."
)

DATABASE_INITIALIZED = "Database initialized: {path}"
DEMO_CREATED = "Demo data only: created {days} days for Demo Store #001 in {path}."
FILE_IMPORTED = "{file_name}: imported {rows} rows."
FILE_GENERATED = "{file_name}: generated {rows} rows."
FILE_ALREADY_IMPORTED = "{file_name}: already imported; skipped."
CONFIG_MISSING = "Config {path} not found; using built-in example defaults."
CONFIG_INVALID = "Invalid config {path}. Use a valid UTF-8 TOML file."
CONFIG_NUMBER_OUT_OF_RANGE = (
    "Config {path} contains an out-of-range number. "
    "Check the integer size or exponent against the documented config limits."
)
CONFIG_SECTION = "Invalid config section {section!r}. Use a documented section."
CONFIG_KEY = "Unknown config setting {section}.{name}. Check config.toml."
CONFIG_INTEGER = (
    "Config {name} must be a nonnegative whole number within SQLite's integer range."
)
CONFIG_PERCENT = (
    "Config review_percent_of_cash_sales must be greater than 0 and at most 100, "
    "with at most six decimal places."
)
CONFIG_LAG = "Config max_lag_days must be a whole number from 0 through 31."
UNSAFE_TEXT = "Text contains an unsafe control or formatting character."
INVALID_IDENTIFIER = (
    "IDs and shift codes cannot contain line breaks or tabs, "
    "or start or end with whitespace."
)
CONFIG_THRESHOLDS = (
    "Config must satisfy within_tolerance_cents < warn_cents <= review_cents."
)
CONFIG_HISTORY = "Config repeat_short must satisfy 1 <= min_shifts <= window."
DATABASE_NOT_FOUND = "Database {path} not found. Run 'drawercheck import' first."
DATABASE_NOT_INITIALIZED = (
    "Database is not initialized for DrawerCheck. "
    "Run 'drawercheck import --dir data/demo' with the same --db path first."
)
NO_SHIFTS = "No shifts found. Import shift data before reconciliation."
NO_SHIFTS_IN_RANGE = "No shifts match the requested date range."
INVALID_RANGE_DATE = "Invalid {option} date {value!r}. Use YYYY-MM-DD."
REVERSED_RANGE = "The --from date must be on or before the --to date."
UNKNOWN_SHIFT = "Unknown shift code {shift_code!r}. Check the imported shift codes."
NOT_RECONCILED = "No flags found. Run `drawercheck reconcile` first."
RESULTS_OUTDATED = (
    "Saved results use an earlier review policy. Run 'drawercheck reconcile' again."
)
RECONCILED = (
    "Reconciled {shifts} shifts from {start} to {end}; saved {flags} review flags."
)


class DrawerCheckError(Exception):
    """An expected problem that can be explained without a traceback."""


class MoneyValidationError(DrawerCheckError, ValueError):
    """A dollar value cannot be represented as supported integer cents."""


class DatabaseVersionError(DrawerCheckError):
    """The installed SQLite is too old for STRICT tables."""


class UsageError(DrawerCheckError):
    """The command-line arguments are invalid."""


class ConfigError(DrawerCheckError, ValueError):
    """Example policies are malformed or internally inconsistent."""


class ReconciliationError(DrawerCheckError):
    """A calculation or explanation cannot run on the requested data."""


class ImportValidationError(DrawerCheckError):
    """A CSV record is invalid, with its exact source location."""

    def __init__(
        self, file_name: str, line_number: int, column: str, detail: str
    ) -> None:
        """Store source details and build the shared validation message."""
        self.file_name = file_name
        self.line_number = line_number
        self.column = column
        self.detail = detail
        super().__init__(
            IMPORT_VALIDATION.format(
                file_name=file_name,
                line_number=line_number,
                column=column,
                detail=detail,
            )
        )


def database_error_message(error: sqlite3.DatabaseError) -> str:
    """Translate expected SQLite failures into plain-English CLI messages."""
    code = getattr(error, "sqlite_errorcode", 0) & 255
    detail = str(error)
    if (
        code in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED)
        or "locked" in detail.lower()
    ):
        return DATABASE_LOCKED
    if (
        code == sqlite3.SQLITE_READONLY
        or "readonly" in detail.lower()
        or "read-only" in detail.lower()
    ):
        return DATABASE_READ_ONLY
    return DATABASE_ERROR.format(detail=detail)
