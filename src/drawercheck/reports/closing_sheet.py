"""Render an offline closing sheet from the same formatted values as Review."""

from datetime import UTC, datetime
from html import escape

from drawercheck.config import Config
from drawercheck.money import format_cents
from drawercheck.reports.html import REPORT_CSS, render_table

_CSS = """
/* On screen, text sizes are in rem so the reader's text-size setting enlarges
   the sheet. They equal the shared report's pixel sizes at default settings. */
@media screen {
  body { font-size:0.9375rem; }
  h1 { font-size:clamp(1.875rem, 4vw, 2.75rem); }
  h2 { font-size:1.375rem; }
  .demo, .generated, caption, footer { font-size:0.75rem; }
  table, .help { font-size:0.8125rem; }
  .closing-table th { font-size:0.75rem; }
}
/* Long rule codes and IDs wrap instead of being cut off by the report frame. */
section p, section li, header p { overflow-wrap:anywhere; }
.closing-table { table-layout:fixed; }
.closing-table th, .closing-table td { overflow-wrap:anywhere; }
.closing-table th { text-transform:none; }
.closing-table td { white-space:pre-wrap; }
.count-lines td:nth-child(n+2) { text-align:right; }
.count-lines th:nth-child(n+2) { text-align:right; }
@page { size:auto; margin:15mm; }
@media print {
  body { font-size:11px; line-height:1.35; }
  h1 { font-size:25px; }
  h2 { font-size:17px; }
  h3 { font-size:12px; margin:8px 0 3px; }
  h2, h3 { break-after:avoid; }
  p { margin:5px 0; }
  section, header, footer { padding:12px 0; }
  .section-head { margin-bottom:8px; }
  .table-wrap { overflow:visible; break-inside:avoid; }
  li { break-inside:avoid; }
  th, td { padding:4px 3px; }
  .closing-table th, .closing-table td { font-size:10px; }
  .demo { letter-spacing:normal; }
}
"""


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def _section(title: str, content: str) -> str:
    return f'<section><div class="section-head"><h2>{_e(title)}</h2></div>{content}</section>'


def _table(caption: str, headers: tuple[str, ...], rows: list[tuple]) -> str:
    return render_table("closing-table", caption, headers, rows)


def _count_sheet(title: str, lines: list[dict], total: str) -> str:
    rows = [
        (line["denomination"], line["quantity"], line["line_total_amount"])
        for line in lines
    ]
    rows.append(("Counted cash", "", total))
    return _section(
        title,
        render_table(
            "closing-table count-lines",
            title,
            ("Bill or coin", "Quantity", "Line total"),
            rows,
        ),
    )


def _coverage(entries: list[dict]) -> str:
    states = {
        "ran_no_lead": "Ran, no lead",
        "ran_lead": "Ran, lead found",
        "not_run": "Not run",
    }
    parts = []
    for entry in entries:
        detail = f"<p>{_e(entry['detail'])}</p>"
        if entry["partial"]:
            for key, title in (
                ("checked", "Checked"),
                ("unavailable", "Could not be checked"),
            ):
                items = "".join(f"<li>{_e(value)}</li>" for value in entry[key])
                detail += f"<p><strong>{_e(title)}</strong></p><ul>{items}</ul>"
        parts.append(
            f"<li><h3>{_e(entry['label'])}: {_e(states[entry['state']])}</h3>"
            f'<p class="muted">{_e(entry["rule_code"])}</p>{detail}</li>'
        )
    return "<ul>" + "".join(parts) + "</ul>"


def _when(timestamp: str, labels: dict) -> str:
    # Read like Review: the date in words and a 24-hour clock time.
    return f"{labels['dates'][timestamp[:10]]}, {timestamp[11:16]}"


def _identity(shift: dict, labels: dict) -> str:
    return _table(
        "Shift slip",
        ("Field", "Supplied value"),
        [
            ("Business date", shift["business_date"]),
            ("Register", shift["register_id"]),
            ("Cashier ID", shift["cashier_id"]),
            ("Drawer code", shift["shift_code"]),
            ("Opened (local time)", _when(shift["opened_at"], labels)),
            ("Closed (local time)", _when(shift["closed_at"], labels)),
            ("Starting cash", shift["opening_float_amount"]),
        ],
    )


def _outcomes(drawer: dict, labels: dict, first: dict | None) -> str:
    comparison = [
        ("Expected cash", drawer["expected_amount"]),
        ("Counted cash", drawer["counted_amount"]),
        ("Difference", drawer["variance_amount"]),
        ("Status", labels["statuses"][drawer["status"]]),
        ("Count used for checks", "Recount" if first else "First count"),
    ]
    outcomes = _table("Checked outcome", ("Field", "Result"), comparison)
    if first:
        outcomes += "<p>Both counts are compared with the same expected cash from this check. Leads and coverage use the recount.</p>"
        outcomes += _table(
            "First count and recount",
            ("Field", "First count", "Recount, used for checks"),
            [
                ("Counted cash", first["counted_amount"], drawer["counted_amount"]),
                ("Difference", first["variance_amount"], drawer["variance_amount"]),
                (
                    "Status",
                    labels["statuses"][first["status"]],
                    labels["statuses"][drawer["status"]],
                ),
            ],
        )
    return outcomes


def _register_report(shift: dict) -> str:
    pos = shift["pos"]
    report = "<p>Register report: not available. Expected cash and difference are unknown.</p>"
    if pos:
        report = _table(
            "Register report",
            ("Cash movement", "Amount"),
            [
                ("Cash sales, before refunds", pos["cash_sales_amount"]),
                ("Cash refunds", pos["cash_refunds_amount"]),
                ("Paid in", pos["paid_ins_amount"]),
                ("Paid out, not safe drops", pos["paid_outs_amount"]),
            ],
        )
    report += "<p>Expected cash = starting cash + cash sales + paid in - cash refunds - paid out - safe drops. Difference = counted cash - expected cash.</p>"
    return report


def _drop_log(drops: dict) -> str:
    drop_rows = [
        (drop["amount"], drop["bag_number"] or "Not recorded")
        for drop in drops["drops"]
    ]
    drop_log = (
        _table("Safe drop log", ("Amount", "Bag number"), drop_rows)
        if drop_rows
        else "<p>No safe drops were recorded for this shift.</p>"
    )
    drop_log += f"<p><strong>Total safe drops: {_e(drops['total_amount'])}</strong></p>"
    return drop_log


def _counts(drawer: dict, first: dict | None) -> str:
    shift = drawer["shift"]
    counts = _count_sheet(
        "First count",
        first["counts"] if first else shift["counts"],
        first["counted_amount"] if first else drawer["counted_amount"],
    )
    if first:
        counts += _count_sheet(
            "Recount, used for checks", shift["counts"], drawer["counted_amount"]
        )
    return counts


def _leads(drawer: dict, labels: dict) -> str:
    leads = "<p>No leads from the checks that ran.</p>"
    if drawer["flags"]:
        leads = _table(
            "Leads for the checked count",
            ("Level", "Check", "Lead and applicable limit"),
            [
                (
                    labels["severities"][flag["severity"]],
                    f"{labels['rules'][flag['rule_code']]} ({flag['rule_code']})",
                    flag["message"]
                    + ("\n" + flag["limit_text"] if flag["limit_text"] else ""),
                )
                for flag in drawer["flags"]
            ],
        )
    return leads


def _signoff(shift: dict) -> str:
    signoff = _table(
        "Reviewer details: supplied, not verified",
        ("Field", "Supplied value"),
        [
            (
                "Verifier ID (supplied, not verified)",
                shift["verifier_id"] or "Not supplied",
            ),
            ("Note (supplied, not verified)", shift["variance_note"] or "Not supplied"),
        ],
    )
    signoff += "<p>A typed ID and note are not a login or signature. They do not prove who reviewed the drawer. Reviewed and balanced are separate concepts.</p>"
    return signoff


def _settings(drawer: dict, config: Config) -> str:
    return _table(
        "Example settings used for this check",
        ("Setting", "Value"),
        [
            ("Balanced within", format_cents(config.within_tolerance_cents)),
            ("Check at", format_cents(config.warn_cents)),
            ("Review cap", format_cents(config.review_cents)),
            ("Cash-sales review percentage", f"{config.review_percent_of_cash_sales}%"),
            ("Review threshold for this drawer", drawer["review_threshold_amount"]),
            (
                "Verifier and note required at",
                format_cents(config.require_verifier_and_note_at_or_above_cents),
            ),
        ],
    )


def render(data: dict, config: Config, *, generated_at: str | None = None) -> str:
    """Render one checked snapshot without recalculating cash or running rules."""
    drawer, labels = data["drawer"], data["labels"]
    shift, first = drawer["shift"], data["initial_count"]
    generated_at = generated_at or datetime.now(UTC).isoformat(timespec="seconds")
    sections = (
        _section(
            "Drawer and outcome",
            _identity(shift, labels) + _outcomes(drawer, labels, first),
        )
        + _section("Register report and calculation", _register_report(shift))
        + _section("Safe drops", _drop_log(data["safe_drops"]))
        + _counts(drawer, first)
        + _section("What to look at", _leads(drawer, labels))
        + _section(
            "Which checks ran",
            "<p>One drawer cannot establish patterns over time or a whole day's bank deposit. Missing information stays unknown.</p>"
            + _coverage(data["coverage"]),
        )
        + _section("Reviewer details", _signoff(shift))
        + _section("Example settings", _settings(drawer, config))
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Drawer closing sheet</title><style>{REPORT_CSS}{_CSS}</style></head>
<body><main><p class="demo">DEMO DATA ONLY. Fictional records. Not for real cash control.</p>
<header><h1>Drawer closing sheet</h1><p>{_e(labels["dates"][shift["business_date"]])}, register {_e(shift["register_id"])}</p>
<p class="generated">Generated {_e(generated_at)} (UTC). Open this file offline or use your browser's Print command.</p></header>
{sections}<footer><p>Flags are leads for review, not findings about a person. Settings are examples, not industry standards.</p>
<p>This file contains only the checked snapshot. Later edits are not included. The website keeps no saved history.</p></footer></main></body></html>"""
