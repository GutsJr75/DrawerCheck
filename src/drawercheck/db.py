"""Open SQLite connections with explicit ownership and safe defaults."""

import sqlite3
from contextlib import closing
from pathlib import Path

from drawercheck import errors

MIN_SQLITE_VERSION = (3, 37, 0)

_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS cashiers (
        id TEXT PRIMARY KEY, display_name TEXT NOT NULL
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS registers (
        id TEXT PRIMARY KEY, label TEXT NOT NULL
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS shifts (
        id INTEGER PRIMARY KEY,
        shift_code TEXT NOT NULL UNIQUE,
        business_date TEXT NOT NULL,
        register_id TEXT NOT NULL REFERENCES registers(id),
        cashier_id TEXT NOT NULL REFERENCES cashiers(id),
        opened_at TEXT NOT NULL,
        closed_at TEXT,
        opening_float_cents INTEGER NOT NULL CHECK (opening_float_cents >= 0),
        verifier_id TEXT REFERENCES cashiers(id),
        variance_note TEXT
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS pos_totals (
        shift_id INTEGER PRIMARY KEY REFERENCES shifts(id),
        cash_sales_cents INTEGER NOT NULL CHECK (cash_sales_cents >= 0),
        card_sales_cents INTEGER NOT NULL CHECK (card_sales_cents >= 0),
        cash_refunds_cents INTEGER NOT NULL CHECK (cash_refunds_cents >= 0),
        paid_outs_cents INTEGER NOT NULL CHECK (paid_outs_cents >= 0),
        paid_ins_cents INTEGER NOT NULL CHECK (paid_ins_cents >= 0),
        void_count INTEGER NOT NULL CHECK (void_count >= 0),
        no_sale_count INTEGER NOT NULL CHECK (no_sale_count >= 0)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS safe_drops (
        id INTEGER PRIMARY KEY,
        shift_id INTEGER NOT NULL REFERENCES shifts(id),
        amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
        dropped_at TEXT NOT NULL,
        bag_number TEXT
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS cash_counts (
        shift_id INTEGER NOT NULL REFERENCES shifts(id),
        denomination_cents INTEGER NOT NULL CHECK (
            denomination_cents IN (10000, 5000, 2000, 1000, 500, 200, 100,
                                   50, 25, 10, 5, 1)
        ),
        quantity INTEGER NOT NULL CHECK (quantity >= 0),
        PRIMARY KEY (shift_id, denomination_cents)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS bank_deposits (
        id INTEGER PRIMARY KEY,
        deposit_date TEXT NOT NULL,
        amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
        reference TEXT
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS flags (
        id INTEGER PRIMARY KEY,
        shift_id INTEGER REFERENCES shifts(id),
        business_date TEXT NOT NULL,
        rule_code TEXT NOT NULL,
        severity TEXT NOT NULL CHECK (severity IN ('info', 'warn', 'review')),
        message TEXT NOT NULL,
        evidence_json TEXT NOT NULL
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS import_log (
        id INTEGER PRIMARY KEY,
        file_name TEXT NOT NULL,
        sha256 TEXT NOT NULL UNIQUE,
        rows_imported INTEGER NOT NULL,
        imported_at TEXT NOT NULL
    ) STRICT""",
    "CREATE INDEX IF NOT EXISTS shifts_business_date ON shifts(business_date)",
    "CREATE INDEX IF NOT EXISTS shifts_cashier_id ON shifts(cashier_id)",
)


def check_version() -> None:
    """Reject SQLite installations that cannot create STRICT tables."""
    if sqlite3.sqlite_version_info < MIN_SQLITE_VERSION:
        version = ".".join(str(part) for part in sqlite3.sqlite_version_info)
        raise errors.DatabaseVersionError(errors.SQLITE_TOO_OLD.format(version=version))


def connect(path: str | Path) -> sqlite3.Connection:
    """Open a connection for use with closing() and an inner transaction block."""
    check_version()
    con = sqlite3.connect(path, autocommit=True)
    try:
        # SQLite only allows this setting to change outside a transaction.
        con.execute("PRAGMA foreign_keys = ON")
        con.row_factory = sqlite3.Row
        con.autocommit = False
    except Exception:
        con.close()
        raise
    return con


def create_schema(con: sqlite3.Connection) -> None:
    """Create the tables and indexes inside the caller's transaction."""
    for statement in _SCHEMA:
        con.execute(statement)


def initialize(path: str | Path) -> None:
    """Create an empty database, preserving any existing records."""
    with closing(connect(path)) as con:
        with con:
            create_schema(con)
