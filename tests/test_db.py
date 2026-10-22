"""Check connection ownership, transaction behavior, and foreign keys."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from drawercheck import db, errors


def test_connection_uses_named_rows_and_closes(tmp_path: Path) -> None:
    """The helper returns named columns and closing() closes the connection."""
    with closing(db.connect(tmp_path / "demo.db")) as con:
        row = con.execute("SELECT ? AS amount_cents", (125075,)).fetchone()
        assert isinstance(row, sqlite3.Row)
        assert row["amount_cents"] == 125075

    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        con.execute("SELECT 1")


def test_connection_closes_when_work_fails(tmp_path: Path) -> None:
    """A failure inside the closing block still releases the connection."""
    with pytest.raises(ValueError, match="example failure"):
        with closing(db.connect(tmp_path / "demo.db")) as con:
            with con:
                raise ValueError("example failure")

    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        con.execute("SELECT 1")


def test_transaction_commits_and_connection_remains_open(tmp_path: Path) -> None:
    """A successful transaction saves rows without closing its connection."""
    path = tmp_path / "demo.db"
    with closing(db.connect(path)) as con:
        with con:
            con.execute("CREATE TABLE amounts (cents INTEGER NOT NULL) STRICT")
            con.execute("INSERT INTO amounts (cents) VALUES (?)", (125075,))
        assert con.execute("SELECT cents FROM amounts").fetchone()["cents"] == 125075

    with closing(db.connect(path)) as con:
        assert con.execute("SELECT cents FROM amounts").fetchone()["cents"] == 125075


def test_failed_transaction_rolls_back_all_rows(tmp_path: Path) -> None:
    """A failed write removes all writes from that transaction."""
    with closing(db.connect(tmp_path / "demo.db")) as con:
        with con:
            con.execute("CREATE TABLE amounts (cents INTEGER NOT NULL UNIQUE) STRICT")

        with pytest.raises(sqlite3.IntegrityError):
            with con:
                con.execute("INSERT INTO amounts (cents) VALUES (?)", (125075,))
                con.execute("INSERT INTO amounts (cents) VALUES (?)", (125075,))

        assert con.execute("SELECT COUNT(*) FROM amounts").fetchone()[0] == 0


def test_foreign_keys_are_enforced_on_every_connection(tmp_path: Path) -> None:
    """Both the first connection and a reopened connection reject orphan rows."""
    path = tmp_path / "demo.db"
    with closing(db.connect(path)) as con:
        assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with con:
            con.execute("CREATE TABLE parents (id INTEGER PRIMARY KEY) STRICT")
            con.execute(
                "CREATE TABLE children (parent_id INTEGER REFERENCES parents(id)) STRICT"
            )
        with pytest.raises(sqlite3.IntegrityError):
            with con:
                con.execute("INSERT INTO children (parent_id) VALUES (?)", (1,))

    with closing(db.connect(path)) as con:
        assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            with con:
                con.execute("INSERT INTO children (parent_id) VALUES (?)", (1,))


def test_old_sqlite_is_rejected_before_opening_a_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unsupported SQLite version produces the shared explanatory error."""
    path = tmp_path / "demo.db"
    monkeypatch.setattr(sqlite3, "sqlite_version_info", (3, 36, 0))

    with pytest.raises(errors.DatabaseVersionError) as caught:
        db.connect(path)

    assert str(caught.value) == errors.SQLITE_TOO_OLD.format(version="3.36.0")
    assert not path.exists()
