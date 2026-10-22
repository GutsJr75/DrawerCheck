"""Open SQLite connections with explicit ownership and safe defaults."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from drawercheck import errors
from drawercheck.models import Flag, PosTotals, Shift

MIN_SQLITE_VERSION = (3, 37, 0)
_RECONCILED_DATES_SCHEMA = """CREATE TABLE IF NOT EXISTS reconciled_dates (
    business_date TEXT PRIMARY KEY,
    config_json TEXT NOT NULL,
    completed_at TEXT NOT NULL
) STRICT"""

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
    _RECONCILED_DATES_SCHEMA,
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


def require_import_schema(con: sqlite3.Connection) -> None:
    """Give setup guidance when an existing database lacks the original input tables."""
    tables = {
        row["name"]
        for row in con.execute("SELECT name FROM sqlite_schema WHERE type = 'table'")
    }
    required = {
        "cashiers",
        "registers",
        "shifts",
        "pos_totals",
        "safe_drops",
        "cash_counts",
        "bank_deposits",
        "flags",
        "import_log",
    }
    if not required <= tables:
        raise errors.ReconciliationError(errors.DATABASE_NOT_INITIALIZED)


def load_register_ids(con: sqlite3.Connection) -> tuple[str, ...]:
    """Read the roster of registers expected on each imported business date."""
    return tuple(
        row["id"] for row in con.execute("SELECT id FROM registers ORDER BY id")
    )


def load_cashier_names(con: sqlite3.Connection) -> dict[str, str]:
    """Read display names separately from stable cashier identifiers."""
    return {
        row["id"]: row["display_name"]
        for row in con.execute("SELECT id, display_name FROM cashiers ORDER BY id")
    }


def load_shifts(con: sqlite3.Connection) -> tuple[Shift, ...]:
    """Read independent records without SQL sums that could overflow integer cents."""
    pos = {
        row["shift_id"]: PosTotals(
            **{key: row[key] for key in row.keys() if key != "shift_id"}
        )
        for row in con.execute("SELECT * FROM pos_totals")
    }
    counts: dict[int, list[tuple[int, int]]] = {}
    for row in con.execute(
        "SELECT * FROM cash_counts ORDER BY denomination_cents DESC"
    ):
        counts.setdefault(row["shift_id"], []).append(
            (row["denomination_cents"], row["quantity"])
        )
    drops: dict[int, int] = {}
    for row in con.execute("SELECT shift_id, amount_cents FROM safe_drops ORDER BY id"):
        drops[row["shift_id"]] = drops.get(row["shift_id"], 0) + row["amount_cents"]
    return tuple(
        Shift(
            **dict(row),
            pos=pos.get(row["id"]),
            counts=tuple(counts.get(row["id"], ())),
            safe_drops_cents=drops.get(row["id"], 0),
        )
        for row in con.execute(
            "SELECT * FROM shifts ORDER BY business_date, opened_at, shift_code"
        )
    )


def save_reconciliation(
    con: sqlite3.Connection,
    start: str,
    end: str,
    snapshot: str,
    completed_at: str,
    dates: tuple[str, ...],
    flags: tuple[Flag, ...],
) -> None:
    """Replace a range inside the caller's transaction, keeping one effective policy."""
    # Older M2 databases do not yet have completion markers.
    con.execute(_RECONCILED_DATES_SCHEMA)
    if con.execute(
        "SELECT 1 FROM reconciled_dates WHERE config_json != ? LIMIT 1", (snapshot,)
    ).fetchone():
        con.execute("DELETE FROM flags")
        con.execute("DELETE FROM reconciled_dates")
    con.execute("DELETE FROM flags WHERE business_date BETWEEN ? AND ?", (start, end))
    con.execute(
        "DELETE FROM reconciled_dates WHERE business_date BETWEEN ? AND ?", (start, end)
    )
    con.executemany(
        """INSERT INTO flags (shift_id, business_date, rule_code, severity, message, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?)""",
        [
            (
                flag.shift_id,
                flag.business_date,
                flag.rule_code,
                flag.severity,
                flag.message,
                json.dumps(flag.evidence, sort_keys=True),
            )
            for flag in flags
        ],
    )
    con.executemany(
        "INSERT INTO reconciled_dates (business_date, config_json, completed_at) VALUES (?, ?, ?)",
        [(day, snapshot, completed_at) for day in dates],
    )


def completion_snapshot(con: sqlite3.Connection, business_date: str) -> str | None:
    """Distinguish a completed zero-flag day from one that has never been checked."""
    if not con.execute(
        "SELECT 1 FROM sqlite_schema WHERE type = 'table' AND name = ?",
        ("reconciled_dates",),
    ).fetchone():
        return None
    row = con.execute(
        "SELECT config_json FROM reconciled_dates WHERE business_date = ?",
        (business_date,),
    ).fetchone()
    return row["config_json"] if row else None


def load_flags(con: sqlite3.Connection, start: str, end: str) -> tuple[Flag, ...]:
    """Read saved evidence in stable date, shift, and rule order."""
    return tuple(
        Flag(
            row["shift_id"],
            row["business_date"],
            row["rule_code"],
            row["severity"],
            row["message"],
            json.loads(row["evidence_json"]),
        )
        for row in con.execute(
            """SELECT * FROM flags WHERE business_date BETWEEN ? AND ?
            ORDER BY business_date, shift_id, rule_code, id""",
            (start, end),
        )
    )
