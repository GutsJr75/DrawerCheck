"""Keep duplicate lookups efficient for concentrated records and older databases."""

from contextlib import closing
from pathlib import Path

import pytest

from drawercheck import db


@pytest.mark.parametrize("upgrade", [False, True])
@pytest.mark.parametrize("table", ["bank_deposits", "safe_drops"])
def test_duplicate_lookup_has_bounded_database_work(
    demo_database: Path, table: str, upgrade: bool
) -> None:
    """A missing duplicate key must not scan thousands of similar existing rows."""
    with closing(db.connect(demo_database)) as con:
        if upgrade:
            with con:
                con.execute("DROP INDEX IF EXISTS bank_deposits_record")
                con.execute("DROP INDEX IF EXISTS safe_drops_record")
    if upgrade:
        db.initialize(demo_database)
        db.initialize(demo_database)
    with closing(db.connect(demo_database)) as con:
        with con:
            if table == "bank_deposits":
                con.executemany(
                    "INSERT INTO bank_deposits (deposit_date, amount_cents, reference) VALUES (?, ?, ?)",
                    [("2026-10-01", 1, f"DEMO-{index}") for index in range(2000)],
                )
                query = "SELECT 1 FROM bank_deposits WHERE deposit_date = ? AND amount_cents = ? AND reference IS ?"
                values = ("2026-10-01", 1, "DEMO-MISSING")
            else:
                shift_id = con.execute(
                    "SELECT id FROM shifts ORDER BY id LIMIT 1"
                ).fetchone()[0]
                con.executemany(
                    "INSERT INTO safe_drops (shift_id, amount_cents, dropped_at, bag_number) VALUES (?, ?, ?, ?)",
                    [
                        (shift_id, 1, "2026-09-01T09:00:00", f"DEMO-{index}")
                        for index in range(2000)
                    ],
                )
                query = "SELECT 1 FROM safe_drops WHERE shift_id = ? AND amount_cents = ? AND dropped_at = ? AND bag_number IS ?"
                values = (shift_id, 1, "2026-09-01T09:00:00", "DEMO-MISSING")
        # Count SQLite work rather than depending on a machine's clock speed.
        con.set_progress_handler(lambda: 1, 1000)
        try:
            assert con.execute(query, values).fetchone() is None
        finally:
            con.set_progress_handler(None, 0)
        assert con.execute("SELECT COUNT(*) FROM shifts").fetchone()[0] == 60
