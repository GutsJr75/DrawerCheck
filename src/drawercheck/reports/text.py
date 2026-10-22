"""Render a terminal-safe cash review with shared daily and cashier summaries."""

from drawercheck.money import format_cents
from drawercheck.reports import (
    REVIEW_NOTICE,
    STAGE_NOTICE,
    VARIANCE_NOTICE,
    ReportData,
    format_amount,
)
from drawercheck.text_safety import terminal_text


def _table(headers: tuple[str, ...], rows: list[tuple[object, ...]]) -> str:
    cells = [tuple(terminal_text(value) for value in row) for row in [headers, *rows]]
    widths = [max(len(row[index]) for row in cells) for index in range(len(headers))]
    lines = [
        " | ".join(value.ljust(widths[index]) for index, value in enumerate(row))
        for row in cells
    ]
    lines.insert(1, "-+-".join("-" * width for width in widths))
    return "\n".join(lines)


def render(report: ReportData) -> str:
    """Show status counts, all saved flags, exact cashier totals, and shift amounts."""
    sections = [
        "DEMO DATA ONLY: Demo Store #001",
        "DrawerCheck cash drawer review",
        f"Dates: {terminal_text(report.from_date)} through {terminal_text(report.to_date)}",
        f"Generated on: {terminal_text(report.generated_at)}",
        STAGE_NOTICE,
        REVIEW_NOTICE,
        "\nDAILY SUMMARY",
        _table(
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
        ),
        "\nREVIEW FLAGS",
    ]
    if not report.flags:
        sections.append("No review flags in this completed range.")
    for flag in report.flags:
        sections.append(
            terminal_text(
                f"[{flag.severity}] {flag.business_date} {report.shift_code(flag) or '(daily)'} {flag.rule_code}: {flag.message}"
            )
        )
    sections.extend(
        [
            "\nCASHIER OVER/SHORT LOG",
            VARIANCE_NOTICE,
            _table(
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
            ),
            "\nSHIFT CALCULATIONS",
            f"Balanced means within {format_cents(report.config.within_tolerance_cents)} tolerance; exact differences remain visible.",
            _table(
                (
                    "Shift",
                    "Cashier",
                    "Status",
                    "Expected",
                    "Counted",
                    "Exact difference",
                ),
                [
                    (
                        result.shift.shift_code,
                        result.shift.cashier_id,
                        result.status,
                        format_amount(result.expected_cents),
                        format_amount(result.counted_cents),
                        format_amount(result.variance_cents),
                    )
                    for result in report.shifts
                ],
            ),
        ]
    )
    return "\n".join(sections) + "\n"
