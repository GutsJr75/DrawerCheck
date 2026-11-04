"""Verify a closing download preserves the checked snapshot and works safely offline."""

import importlib
from html.parser import HTMLParser
from pathlib import Path

import pytest
from drawer_cases import SIGN_OFF, drawer_payload

from drawercheck.config import Config
from drawercheck.reports.closing_sheet import render

pytest.importorskip("flask")
web = importlib.import_module("drawercheck.web")


class Sheet(HTMLParser):
    """Collect real markup and readable text separately from escaped user text."""

    def __init__(self, content: str) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict]] = []
        self.words: list[str] = []
        self.feed(content)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data: str) -> None:
        self.words.append(data)


def _check(case: str = "B", **changes: object) -> dict:
    with web.create_app().test_client() as client:
        response = client.post("/api/drawer", json=drawer_payload(case, **changes))
        assert response.status_code == 200
        return response.get_json()


@pytest.mark.parametrize("case", ["A", "B", "C"])
def test_sheet_uses_the_checked_amounts_leads_and_coverage(case: str) -> None:
    """Balanced, short, and unknown results keep their exact meaning in the sheet."""
    data = _check(case)
    download, drawer = data["closing_summary"], data["drawer"]
    content = download["content"]
    assert download["filename"] == "drawercheck-closing-2026-11-02.html"
    assert download["media_type"] == "text/html"
    for field in ("expected_amount", "counted_amount", "variance_amount"):
        assert drawer[field] in content
    for lead in drawer["flags"]:
        assert lead["rule_code"] in content
        assert lead["message"] in "".join(Sheet(content).words)
        assert lead["limit_text"] in content
    assert "First count" in content and "Recount, used for checks" not in content
    assert "Not run: no earlier shifts" in content
    assert "Not run: one drawer is not a whole day" in content
    assert "DEMO DATA ONLY" in content
    assert "supplied, not verified" in content
    assert "Settings are examples, not industry standards." in content
    if case == "A":
        assert "-$0.25" in content
    if case == "C":
        assert "Register report: not available" in content
        assert "Whether expected cash is negative: expected cash is unknown." in content


def test_recount_sheet_keeps_both_counts_against_the_same_expected_cash() -> None:
    """The balanced recount cannot erase the initial twenty-dollar shortage."""
    recount = dict(drawer_payload("B")["counts"], **{"20.00": "13"})
    content = _check(recount=recount)["closing_summary"]["content"]
    assert "First count and recount" in content
    assert "same expected cash" in content
    for amount in ("$665.65", "-$20.00", "$685.65", "$0.00", "$240.00", "$260.00"):
        assert amount in content
    assert "Recount, used for checks" in content
    assert "No leads from the checks that ran." in content
    assert "Could be two digits swapped" not in content


def test_unknown_report_and_zero_recount_stay_distinct() -> None:
    """A known empty recount remains $0.00 while its difference stays unknown."""
    zero = {key: "0" for key in drawer_payload("C")["counts"]}
    data = _check("C", recount=zero)
    content = data["closing_summary"]["content"]
    assert "$437.80" in content and "$0.00" in content
    assert data["initial_count"]["variance_amount"] == "unknown"
    assert data["drawer"]["variance_amount"] == "unknown"
    assert "Missing POS totals. Expected cash is unknown." in content


def test_reviewer_details_are_factual_and_do_not_change_the_difference() -> None:
    """A supplied note clears only missing sign-off and is explicitly unverified."""
    data = _check(**SIGN_OFF)
    content = data["closing_summary"]["content"]
    assert "manager_01" in content and SIGN_OFF["variance_note"] in content
    assert "Reviewer details: supplied, not verified" in content
    assert "-$20.00" in content
    assert "Missing verifier and variance note" not in content
    assert "not a login or signature" in content
    assert "Reviewed and balanced are separate" in content


def test_every_user_text_field_is_escaped_and_cannot_create_markup() -> None:
    """IDs, drop bags, and multiline notes cannot introduce executable HTML."""
    text = '<img src="https://example.invalid/probe" onerror="alert(1)"> & <script>x</script>'
    data = _check(
        register_id=text,
        cashier_id=text,
        verifier_id=text,
        variance_note=text + "\nSecond line.",
        safe_drops=[{"amount": "800.00", "bag_number": text}],
    )
    content = data["closing_summary"]["content"]
    sheet = Sheet(content)
    assert {tag for tag, _ in sheet.tags}.isdisjoint(
        {"script", "img", "iframe", "link"}
    )
    assert "&lt;img" in content and "&amp;" in content
    assert "Second line." in "".join(sheet.words)
    assert text in "".join(sheet.words)
    assert data["closing_summary"]["filename"] == "drawercheck-closing-2026-11-02.html"


def test_sheet_is_self_contained_printable_and_has_one_generation_time() -> None:
    """All styling is inline, the timestamp is explicit, and no outside file is needed."""
    data = _check()
    content = render(data, Config(), generated_at="2026-11-04T20:00:00+00:00")
    sheet = Sheet(content)
    assert "Generated 2026-11-04T20:00:00+00:00 (UTC)" in content
    # Times read like Review, never as raw timestamps.
    assert "Monday, November 2, 2026, 08:00" in content
    assert "Monday, November 2, 2026, 20:00" in content
    assert "T08:00" not in content
    assert "@media print" in content and "@page" in content
    assert "<style>:root" in content
    assert "print" in content and "offline" in content
    assert not any("src" in attrs or "href" in attrs for _, attrs in sheet.tags)
    assert {tag for tag, _ in sheet.tags}.isdisjoint({"script", "link", "form"})
    assert sum(tag == "h1" for tag, _ in sheet.tags) == 1
    assert "Cash-sales review percentage" in content and "$13.16" in content
    assert "Later edits are not included" in content


def test_a_later_check_cannot_change_an_earlier_download() -> None:
    """Each response embeds its own immutable snapshot rather than a server URL."""
    first = _check()["closing_summary"]["content"]
    signed = _check(**SIGN_OFF)["closing_summary"]["content"]
    assert "Not supplied" in first and SIGN_OFF["variance_note"] not in first
    assert SIGN_OFF["variance_note"] in signed
    assert "Missing verifier and variance note" in first


SAMPLE = Path(__file__).resolve().parents[1] / "examples/sample_closing_sheet.html"
SAMPLE_NOTE = "First count was short $20.00. Recount found one more $20 bill; the recount balances."


def _sample_sheet() -> str:
    recount = dict(drawer_payload("B")["counts"], **{"20.00": "13"})
    data = _check(
        "B", recount=recount, verifier_id="manager_01", variance_note=SAMPLE_NOTE
    )
    return render(data, Config(), generated_at="2026-11-04T20:44:12+00:00")


def test_the_committed_sample_matches_the_generator() -> None:
    """examples/sample_closing_sheet.html is case B recounted and signed off."""
    assert SAMPLE.read_text(encoding="utf-8") == _sample_sheet() + "\n"
