"""Check the page shell, its local assets, and the colour tokens without a browser."""

import importlib
import re
import tomllib
from fnmatch import fnmatch
from html.parser import HTMLParser
from pathlib import Path

import pytest

from drawercheck.csv_contract import CSV_HEADERS

pytest.importorskip("flask")
web = importlib.import_module("drawercheck.web")
PACKAGE = Path(web.__file__).parent
STATIC = PACKAGE / "static"
ROOT = PACKAGE.parent.parent
REPOSITORY = "https://github.com/GutsJr75/DrawerCheck"
# Copied from the security-header section of docs/WEB_PLAN.md.
PLANNED_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self'; "
    "font-src 'self'; img-src 'self' data: blob:; connect-src 'self'; "
    "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.text: list[str] = []
        self.open_views: list[str | None] = []
        self.heading_views: list[str | None] = []
        self.tape: str | None = None
        self.tape_line: str | None = None
        self.capturing: tuple[str, str] | None = None
        self.captured: dict[tuple[str, str], str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        self.tags.append((tag, attributes))
        if tag == "section":
            self.open_views.append(attributes.get("id"))
        elif tag == "h1":
            self.heading_views.append(self.open_views[-1] if self.open_views else None)
        elif tag == "table":
            self.tape = attributes.get("data-tape")
        elif tag == "tr":
            self.tape_line = attributes.get("data-line")
        elif tag == "td" and self.tape_line:
            # Captured per tape, so the empty Drawer details tape cannot mix in.
            self.capturing = (f"tape-{self.tape}", self.tape_line)
        if "data-message" in attributes:
            self.capturing = ("message", attributes["data-message"])

    def handle_endtag(self, tag: str) -> None:
        if tag == "section":
            self.open_views.pop()
        elif tag == "table":
            self.tape = self.tape_line = None
        elif tag in ("td", "p"):
            self.capturing = None

    def handle_data(self, data: str) -> None:
        self.text.append(data)
        if self.capturing:
            self.captured[self.capturing] = self.captured.get(self.capturing, "") + data

    def found(self, kind: str) -> dict[str, str]:
        """Return captured text of one kind, with whitespace collapsed."""
        return {
            key: " ".join(text.split())
            for (found_kind, key), text in self.captured.items()
            if found_kind == kind
        }


@pytest.fixture
def client():
    """Serve the app in-process; no browser or network is involved."""
    with web.create_app().test_client() as client:
        yield client


def _page(client) -> tuple[_Page, str]:
    response = client.get("/")
    assert response.status_code == 200 and response.mimetype == "text/html"
    parser = _Page()
    parser.feed(response.get_data(as_text=True))
    return parser, " ".join(" ".join(parser.text).split())


def test_page_shell_has_landmarks_notice_and_footer(client) -> None:
    page, text = _page(client)
    tags = [tag for tag, _ in page.tags]
    assert ("html", {"lang": "en"}) in page.tags
    # One h1 per view; only Start is visible before any script runs.
    assert page.heading_views == [
        "view-start",
        "view-prepare",
        "view-results",
        "view-drawer",
    ]
    views = {attrs["id"]: attrs for tag, attrs in page.tags if tag == "section"}
    assert "hidden" not in views["view-start"]
    assert all(
        "hidden" in views[name]
        for name in ("view-prepare", "view-results", "view-drawer")
    )
    # Drawer details builds its title from the shift code, so it has a template.
    assert all(
        (attrs.get("data-title") or attrs["data-title-template"]).endswith(
            " | DrawerCheck"
        )
        for attrs in views.values()
    )
    assert tags.count("main") == 1
    assert tags.count("header") == tags.count("footer") == 1
    first_link = next(attrs for tag, attrs in page.tags if tag == "a")
    assert first_link == {"class": "skip-link", "href": "#main"}
    assert ("main", {"id": "main", "class": "wrap", "tabindex": "-1"}) in page.tags
    assert any(
        tag == "meta" and attrs.get("name") == "viewport" for tag, attrs in page.tags
    )
    assert "| DrawerCheck" in text
    assert "Example data only. Do not upload real store records." in text
    assert "It is not for real cash control." in text
    assert "Uploaded files are checked and then deleted. Nothing is saved." in text


def test_page_has_no_inline_code_or_remote_assets(client) -> None:
    page, _ = _page(client)
    tags = [tag for tag, _ in page.tags]
    assert "style" not in tags
    for tag, attrs in page.tags:
        assert "style" not in attrs
        assert not any(name.startswith("on") for name in attrs)
        if tag == "script":
            assert attrs.get("src", "").startswith("/static/")
        if tag == "link":
            assert attrs["href"].startswith("/static/")
        if tag == "a" and not attrs["href"].startswith(("#", "/examples/")):
            # Outbound links are ordinary navigation, never loaded resources.
            assert attrs["href"].startswith(REPOSITORY)


def test_start_tape_matches_the_demo_calculation(client) -> None:
    """The Start view's example tape shows the server's own numbers for S1."""
    page, text = _page(client)
    with client.post("/api/demo") as response:
        payload = response.get_json()
    shift = next(
        item
        for item in payload["shifts"]
        if item["shift"]["shift_code"] == "2026-09-03-R1"
    )
    record, pos = shift["shift"], shift["shift"]["pos"]
    labels = payload["labels"]
    worst = max(
        (flag["severity"] for flag in shift["flags"]),
        key=["info", "warn", "review"].index,
    )
    assert page.found("tape-example") == {
        "opening_float": record["opening_float_amount"],
        "cash_sales": pos["cash_sales_amount"],
        "paid_ins": pos["paid_ins_amount"],
        "cash_refunds": pos["cash_refunds_amount"],
        "paid_outs": pos["paid_outs_amount"],
        "safe_drops": record["safe_drops_amount"],
        "expected": shift["expected_amount"],
        "counted": shift["counted_amount"],
        "difference": shift["variance_amount"],
        "result": f"{labels['statuses'][shift['status']]} "
        f"{labels['severities'][worst]}",
    }
    registers = {item["shift"]["register_id"] for item in payload["shifts"]}
    sentence = f"{payload['summary']['drawers_checked']} drawers on two registers"
    assert sentence in text and len(registers) == 2


def test_both_tapes_share_one_set_of_lines_and_meanings(client) -> None:
    """Start and Drawer details use the same labels, signs, and definitions."""
    page, _ = _page(client)
    html = client.get("/").get_data(as_text=True)
    keys = [line.key for line in web.TAPE_LINES]
    assert keys == list(web.EXAMPLE_TAPE)
    for tape in ("example", "drawer"):
        rows = re.search(
            rf'<table class="tape" data-tape="{tape}">(.*?)</table>', html, re.S
        )
        assert rows, tape
        assert re.findall(r'data-line="([a-z_]+)"', rows.group(1)) == [*keys, "result"]
    drawer = re.search(r'data-tape="drawer">(.*?)</table>', html, re.S).group(1)
    for line in web.TAPE_LINES:
        # Each Drawer details label opens its meaning; the Start tape lists them below.
        assert f"<summary>{line.label}</summary><p>{line.definition}</p>" in drawer
        assert (
            f"<dt>{line.label}</dt>" in html and f"<dd>{line.definition}</dd>" in html
        )
        if line.spoken:
            assert f'<span class="visually-hidden">{line.spoken} </span>' in drawer
    assert "<details" not in re.search(
        r'data-tape="example">(.*?)</table>', html, re.S
    ).group(1)


def test_results_hooks_match_the_response_fields(client) -> None:
    """Every number or word slot in Results points at a field Python sends."""
    page, _ = _page(client)
    with client.post("/api/demo") as response:
        payload = response.get_json()
    facts = [attrs["data-fact"] for tag, attrs in page.tags if "data-fact" in attrs]
    assert facts and set(facts) <= set(payload["summary"])
    statuses = [
        attrs["data-status"] for tag, attrs in page.tags if "data-status" in attrs
    ]
    assert set(statuses) == set(payload["labels"]["statuses"])
    plural_labels = [attrs for tag, attrs in page.tags if "data-one" in attrs]
    assert len(plural_labels) == len(facts)
    assert all(attrs["data-many"] for attrs in plural_labels)
    # One deposit sentence for each reason a drawer's share can be unknown.
    deposit = next(
        attrs for tag, attrs in page.tags if attrs.get("id") == "deposit-text"
    )
    for reason in (
        "data-template",
        "data-open",
        "data-no-count",
        "data-day-incomplete",
    ):
        assert deposit[reason], reason
    assert "counted cash is unknown" not in deposit["data-day-incomplete"]


def test_prepare_view_lists_the_seven_files_and_messages(client) -> None:
    page, text = _page(client)
    rows = [attrs for tag, attrs in page.tags if "data-file" in attrs]
    assert [row["data-file"] for row in rows] == list(CSV_HEADERS)
    assert [row["id"] for row in rows] == [
        f"file-{name.removesuffix('.csv')}" for name in CSV_HEADERS
    ]
    examples = [attrs for tag, attrs in page.tags if tag == "a" and "download" in attrs]
    assert [link["href"] for link in examples] == [
        f"/examples/{name}" for name in CSV_HEADERS
    ]
    assert page.found("message") == web.CLIENT_MESSAGES
    assert (
        "Use example data only. Files are checked and then deleted; nothing is saved."
        in text
    )
    assert "There is a problem with your files" in text
    assert "Up to 1,000 shifts, 2,000 safe drops, and 2,000 bank deposits." in text
    assert "up to 2 MiB (2,097,152 bytes)" in text


def test_script_never_inserts_markup_or_runs_strings() -> None:
    """Server text reaches the page only through textContent."""
    script = (STATIC / "app.js").read_text(encoding="utf-8")
    for forbidden in (
        "innerHTML",
        "outerHTML",
        "insertAdjacentHTML",
        "document.write",
        "eval(",
        "new Function",
        "parseFloat",
    ):
        assert forbidden not in script, forbidden
    assert "textContent" in script


@pytest.mark.parametrize(
    "method, path",
    [("get", "/"), ("get", "/static/app.css"), ("post", "/api/demo")],
)
def test_security_headers_on_every_response(client, method: str, path: str) -> None:
    # Closing the response also closes a served static file.
    with getattr(client, method)(path) as response:
        assert response.status_code == 200
    assert response.headers["Content-Security-Policy"] == PLANNED_POLICY
    assert web.CONTENT_SECURITY_POLICY == PLANNED_POLICY
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Cache-Control"] == "no-store"


def test_stylesheet_fonts_are_local_and_served(client) -> None:
    css = (STATIC / "app.css").read_text(encoding="utf-8")
    urls = re.findall(r'url\("([^"]+)"\)', css)
    assert len(urls) == 4 and css.count("font-display: swap") == 4
    page, _ = _page(client)
    preloads = {
        attrs["href"]
        for tag, attrs in page.tags
        if tag == "link" and attrs.get("rel") == "preload"
    }
    assert preloads <= {f"/static/{url}" for url in urls}
    for url in urls:
        assert url.startswith("fonts/") and "//" not in url
        with client.get(f"/static/{url}") as response:
            assert response.status_code == 200 and response.mimetype == "font/woff2"
            assert response.get_data()[:4] == b"wOF2"
    license_text = (STATIC / "fonts" / "LICENSE.txt").read_text(encoding="utf-8")
    assert "SIL Open Font License, Version 1.1" in license_text


def test_static_files_meet_the_performance_budget() -> None:
    """DESIGN.md: CSS and JavaScript under 60 KB together; fonts under 200 KB."""
    code = sum(
        path.stat().st_size
        for pattern in ("*.css", "*.js")
        for path in STATIC.glob(pattern)
    )
    fonts = sum(path.stat().st_size for path in (STATIC / "fonts").glob("*.woff2"))
    assert 0 < code < 60_000
    assert 0 < fonts < 200_000


def test_package_data_includes_every_template_and_static_file() -> None:
    """A wheel install must ship the same screens as an editable checkout."""
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    patterns = config["tool"]["setuptools"]["package-data"]["drawercheck"]
    files = [
        path.relative_to(PACKAGE).as_posix()
        for folder in ("templates", "static")
        for path in (PACKAGE / folder).rglob("*")
        if path.is_file()
    ]
    assert files
    for name in files:
        assert any(fnmatch(name, pattern) for pattern in patterns), name


def _luminance(colour: str) -> float:
    channels = [int(colour[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
        for value in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    lighter, darker = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def _themes() -> dict[str, dict[str, str]]:
    css = (STATIC / "app.css").read_text(encoding="utf-8")
    light = re.search(r"^:root \{(.*?)^\}", css, re.S | re.M)
    dark = re.search(
        r"@media \(prefers-color-scheme: dark\) \{\s*:root \{(.*?)\}", css, re.S
    )
    assert light and dark
    return {
        name: dict(re.findall(r"--([a-z-]+): (#[0-9a-f]{6});", block.group(1)))
        for name, block in (("light", light), ("dark", dark))
    }


# WCAG 2.2 AA: 4.5:1 for text, 3:1 for control borders.
CONTRAST_PAIRS = [
    ("text", "surface", 4.5),
    ("text", "page", 4.5),
    ("surface", "text", 4.5),  # The demo notice reverses these two colours.
    ("muted", "surface", 4.5),
    ("muted", "page", 4.5),
    ("control", "surface", 3),
    ("control", "page", 3),
    ("accent", "surface", 4.5),
    ("accent", "page", 4.5),
    ("on-accent", "accent", 4.5),
    ("note", "note-bg", 4.5),
    ("check", "check-bg", 4.5),
    ("review", "review-bg", 4.5),
    # Problem messages and error links use the review colour as plain text.
    ("review", "surface", 4.5),
    ("review", "page", 4.5),
    ("ready", "ready-bg", 4.5),
]


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_colour_tokens_meet_wcag_contrast(theme: str) -> None:
    tokens = _themes()[theme]
    assert set(_themes()["light"]) == set(_themes()["dark"])
    for foreground, background, minimum in CONTRAST_PAIRS:
        ratio = _contrast(tokens[foreground], tokens[background])
        assert ratio >= minimum, (foreground, background, round(ratio, 2))
