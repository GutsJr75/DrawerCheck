"""Export saved review leads as protected spreadsheet cells."""

import csv
from io import StringIO

from drawercheck.csv_safety import sanitize_cell
from drawercheck.reports import ReportData


def render(report: ReportData) -> str:
    """Render every header and value through the shared spreadsheet-cell protection."""
    stream = StringIO(newline="")
    writer = csv.writer(stream)
    rows = [("date", "shift_code", "rule_code", "severity", "message")]
    rows.extend(
        (
            flag.business_date,
            report.shift_code(flag),
            flag.rule_code,
            flag.severity,
            flag.message,
        )
        for flag in report.flags
    )
    for row in rows:
        writer.writerow([sanitize_cell(str(value)) for value in row])
    return stream.getvalue()
