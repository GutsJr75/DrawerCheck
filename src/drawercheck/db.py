"""Open SQLite connections with explicit ownership and safe defaults."""

import sqlite3
from pathlib import Path

from drawercheck import errors

MIN_SQLITE_VERSION = (3, 37, 0)


def connect(path: str | Path) -> sqlite3.Connection:
    """Open a connection for use with closing() and an inner transaction block."""
    if sqlite3.sqlite_version_info < MIN_SQLITE_VERSION:
        version = ".".join(str(part) for part in sqlite3.sqlite_version_info)
        raise errors.DatabaseVersionError(errors.SQLITE_TOO_OLD.format(version=version))

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
