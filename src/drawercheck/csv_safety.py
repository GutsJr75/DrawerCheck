"""Protect exported spreadsheet cells without changing ordinary text."""


def sanitize_cell(value: str) -> str:
    """Prefix a quote when a cell could be interpreted as a spreadsheet formula."""
    return "'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r")) else value
