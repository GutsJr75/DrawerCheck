"""Keep bank entries reportable even when no drawer records were supplied."""

from contextlib import closing
from pathlib import Path

from drawercheck import db
from drawercheck.config import Config
from drawercheck.reconcile import reconcile
from drawercheck.reports import html, load_report


def test_only_bank_entries_have_no_invented_cashier_or_business_day(
    tmp_path: Path,
) -> None:
    """A bank-only input still needs review, without claiming a missing closing drawer."""
    path = tmp_path / "bank-only.db"
    db.initialize(path)
    with closing(db.connect(path)) as con:
        with con:
            con.execute(
                "INSERT INTO bank_deposits (deposit_date, amount_cents) VALUES (?, ?)",
                ("2026-09-01", 10000),
            )
    run = reconcile(path, Config())
    assert not run.shifts
    assert len(run.flags) == 1 and run.flags[0].evidence["issue"] == "unexpected"
    report = load_report(path)
    assert not report.shifts and not report.cashiers
    assert report.days[0].shifts == 0 and report.days[0].review == 0
    output = html.render(report)
    assert "<strong>0</strong><span>Incomplete deposit days</span>" in output
    assert "not inferred business days" in output
