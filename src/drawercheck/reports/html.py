"""Render a self-contained, escaped cash review that works offline and in print."""

from html import escape

from drawercheck.money import format_cents
from drawercheck.reports import (
    REVIEW_NOTICE,
    STAGE_NOTICE,
    VARIANCE_NOTICE,
    ReportData,
    format_amount,
)

_CSS = """:root { color-scheme: light dark; --page:#edf3f5; --paper:#ffffff; --ink:#162b35;
  --muted:#48636f; --line:#cedce1; --accent:#076f78; --soft:#e8f4f3;
  --warn:#805000; --review:#963a32; --head:#143c4a; }
* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink);
  font:15px/1.55 "Avenir Next", "Segoe UI", sans-serif; }
main { max-width:1260px; margin:36px auto; background:var(--paper);
  border:1px solid var(--line); border-radius:12px; overflow:hidden; }
.demo { margin:0; padding:10px 36px; color:#fff; background:var(--head, #143c4a);
  font-size:12px; font-weight:700; letter-spacing:.08em; }
header { padding:30px 36px 24px; border-bottom:1px solid var(--line); }
.eyebrow { color:var(--accent); font:700 13px/1.4 "Avenir Next", "Segoe UI", sans-serif;
  letter-spacing:.08em; text-transform:uppercase; }
h1 { margin:8px 0; font:500 clamp(30px,4vw,44px)/1.16 "Iowan Old Style", Palatino, serif; }
h2 { margin:0; font-size:22px; line-height:1.3; letter-spacing:-.025em; }
p { margin:8px 0; } .muted, .help { color:var(--muted); }
.range { font-size:17px; } .generated { font-size:12px; color:var(--muted); }
nav { display:flex; gap:8px 24px; flex-wrap:wrap; padding:14px 36px; border-bottom:1px solid var(--line); }
a { color:var(--accent); text-underline-offset:4px; }
nav a { font-size:13px; font-weight:600; }
.overview { display:grid; grid-template-columns:repeat(3,1fr); gap:1px;
  background:var(--line); border-bottom:1px solid var(--line); }
.metric { background:var(--paper); padding:20px 36px; }
.metric strong { display:block; font-size:30px; font-weight:600; font-variant-numeric:tabular-nums; }
.metric span { font-size:13px; color:var(--muted); }
.stage { padding:16px 22px; margin:24px 36px 0; border-left:4px solid var(--accent); background:var(--soft); }
.stage p { margin:0; font-size:13px; }
section { padding:30px 36px; border-bottom:1px solid var(--line); scroll-margin-top:12px; }
.section-head { margin-bottom:16px; } .help { font-size:13px; max-width:88ch; }
.table-wrap { overflow-x:auto; scrollbar-gutter:stable; border:1px solid var(--line); border-radius:6px; }
table { width:100%; border-collapse:collapse; font-size:13px; }
caption { text-align:left; padding:12px 16px; color:var(--muted); font-size:12px; border-bottom:1px solid var(--line); }
th { text-align:left; color:var(--muted); background:var(--page); font-size:11px;
  letter-spacing:.025em; text-transform:uppercase; }
td,th { padding:12px 14px; border-bottom:1px solid var(--line); vertical-align:top; }
tbody tr:last-child td { border-bottom:0; }
td { font-variant-numeric:tabular-nums; } .daily { min-width:1030px; }
.daily td:not(:first-child), .daily th:not(:first-child) { text-align:right; }
.cashiers { min-width:900px; } .cashiers td:nth-child(n+3), .cashiers th:nth-child(n+3) { text-align:right; }
.shifts { min-width:830px; } .shifts td:nth-child(n+4), .shifts th:nth-child(n+4) { text-align:right; }
.flags { min-width:800px; } .flags td:last-child { min-width:300px; max-width:600px; overflow-wrap:anywhere; }
.severity { font-weight:700; text-transform:uppercase; font-size:11px; }
.severity.review { color:var(--review); } .severity.warn { color:var(--warn); } .severity.info { color:var(--accent); }
footer { padding:22px 36px; color:var(--muted); font-size:12px; }
:focus-visible { outline:3px solid var(--accent); outline-offset:3px; }
@media (max-width:650px) { main { margin:0; border-radius:0; border:0; }
  .demo, header, nav, section, footer { padding-left:18px; padding-right:18px; }
  .stage { margin-left:18px; margin-right:18px; } .metric { padding:16px 18px; }
  .metric strong { font-size:24px; } .metric span { font-size:11px; }
}
@media (prefers-color-scheme:dark) { :root { --page:#13262f; --paper:#1b333e; --ink:#eff5f7;
  --muted:#b4cbd4; --line:#3a5662; --accent:#80d8d3; --soft:#23454c; --warn:#ffd28a; --review:#ffb2a8; }
}
@media print { :root { color-scheme:light; --page:#fff; --paper:#fff; --ink:#162b35;
  --muted:#48636f; --line:#a8bbc3; --accent:#075b64; --soft:#fff; --warn:#805000; --review:#963a32; }
  body { background:#fff; } main { margin:0; border:0; overflow:visible; } nav { display:none; }
  .demo { color:#162b35; background:#fff; border-bottom:2px solid #162b35; }
  .table-wrap { overflow:visible; border:0; } table { min-width:0 !important; font-size:11px; }
  th,td { padding:6px 4px; overflow-wrap:anywhere; } .flags td:last-child { min-width:0; max-width:none; }
  thead { display:table-header-group; } tr { break-inside:avoid; }
  section,header,footer { padding:18px 0; } .metric { padding:12px; }
}
"""


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def _table(
    kind: str, caption: str, headers: tuple[str, ...], rows: list[tuple[object, ...]]
) -> str:
    head = "".join(f'<th scope="col">{_e(label)}</th>' for label in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{_e(value)}</td>" for value in row) + "</tr>"
        for row in rows
    )
    return f'<div class="table-wrap" role="region" aria-label="{_e(caption)}" tabindex="0"><table class="{_e(kind)}"><caption>{_e(caption)}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _flags(report: ReportData) -> str:
    if not report.flags:
        return '<p class="help">No review flags in this completed range.</p>'
    rows = []
    for flag in report.flags:
        rows.append(
            f'<tr><td class="severity {_e(flag.severity)}">{_e(flag.severity)}</td><td>{_e(flag.business_date)}</td><td>{_e(report.shift_code(flag) or "Daily review")}</td><td>{_e(flag.rule_code)}</td><td>{_e(flag.message)}</td></tr>'
        )
    headers = "".join(
        f'<th scope="col">{_e(label)}</th>'
        for label in ("Severity", "Date", "Shift", "Rule", "Review lead")
    )
    return (
        '<div class="table-wrap" role="region" aria-label="Saved review leads" tabindex="0"><table class="flags"><caption>All saved flags for the selected dates</caption><thead><tr>'
        + headers
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )


def render(report: ReportData) -> str:
    """Render an offline report with semantic tables, safe values, and light/dark styling."""
    incomplete_days = sum(
        day.shifts > 0 and day.expected_deposit_cents is None for day in report.days
    )
    daily = _table(
        "daily",
        "Completed dates; expected deposits are cash calculations, not bank matches",
        (
            "Date",
            "Shifts",
            "Balanced",
            "Over",
            "Short",
            "Incomplete",
            "Open",
            "Info",
            "Warn",
            "Review",
            "Expected deposit",
        ),
        [
            (
                day.business_date,
                day.shifts,
                day.balanced,
                day.over,
                day.short,
                day.incomplete,
                day.open,
                day.info,
                day.warn,
                day.review,
                format_amount(day.expected_deposit_cents),
            )
            for day in report.days
        ],
    )
    cashiers = _table(
        "cashiers",
        "Exact known cash differences by cashier",
        (
            "Cashier ID",
            "Name",
            "Shifts",
            "Known",
            "Incomplete",
            "Open",
            "Over",
            "Short",
            "Exact net",
        ),
        [
            (
                cashier.cashier_id,
                cashier.display_name,
                cashier.shifts,
                cashier.known,
                cashier.incomplete,
                cashier.open,
                format_amount(cashier.over_cents if cashier.known else None),
                format_amount(cashier.short_cents if cashier.known else None),
                format_amount(cashier.net_cents if cashier.known else None),
            )
            for cashier in report.cashiers
        ],
    )
    shifts = _table(
        "shifts",
        "Closing amounts retain exact differences; unknown cash is never shown as zero",
        ("Shift", "Cashier", "Status", "Expected", "Counted", "Exact difference"),
        [
            (
                result.shift.shift_code,
                result.shift.cashier_id,
                "Balanced within tolerance"
                if result.status == "balanced"
                else result.status,
                format_amount(result.expected_cents),
                format_amount(result.counted_cents),
                format_amount(result.variance_cents),
            )
            for result in report.shifts
        ],
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>DrawerCheck cash review: {_e(report.from_date)} to {_e(report.to_date)}</title><style>{_CSS}</style></head>
<body><main><p class="demo">DEMO DATA ONLY / FICTIONAL RECORDS</p>
<header><div class="eyebrow">DrawerCheck / Demo Store #001</div><h1>Cash drawer review</h1>
<p class="range">{_e(report.from_date)} through {_e(report.to_date)}</p><p class="muted">{_e(REVIEW_NOTICE)}</p>
<p class="generated">Generated on: {_e(report.generated_at)}</p></header>
<nav aria-label="Report sections"><a href="#daily">Daily summary</a><a href="#flags">Review leads</a><a href="#cashiers">Cashier log</a><a href="#shifts">Shift calculations</a></nav>
<div class="overview"><div class="metric"><strong>{_e(len(report.shifts))}</strong><span>Shifts reviewed</span></div><div class="metric"><strong>{_e(len(report.flags))}</strong><span>Review leads</span></div><div class="metric"><strong>{_e(incomplete_days)}</strong><span>Incomplete deposit days</span></div></div>
<aside class="stage"><p>{_e(STAGE_NOTICE)}</p></aside>
<section id="daily"><div class="section-head"><h2>Daily summary</h2><p class="help">Balanced means within {_e(format_cents(report.config.within_tolerance_cents))} tolerance. Open and incomplete drawers are counted separately. An unknown deposit needs complete data.</p></div>{daily}</section>
<section id="flags"><div class="section-head"><h2>Review leads</h2><p class="help">Recount and review the records behind each lead. Severity labels describe the configured review level.</p></div>{_flags(report)}</section>
<section id="cashiers"><div class="section-head"><h2>Cashier over/short log</h2><p class="help">{_e(VARIANCE_NOTICE)}</p></div>{cashiers}</section>
<section id="shifts"><div class="section-head"><h2>Shift calculations</h2><p class="help">Expected cash uses the opening float and recorded cash movements. Counted cash comes from the independent count sheet.</p></div>{shifts}</section>
<footer><p>Personal learning project using fictional data. Thresholds are example policies, not industry standards.</p><p>One expected closing shift per listed register and imported business date. This report is self-contained and works offline.</p></footer>
</main></body></html>"""
