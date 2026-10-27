"""Check the page shell, its local assets, and the colour tokens without a browser."""

import importlib
import importlib.util
import re
import shlex
import subprocess
import sys
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
        "view-missing",
    ]
    views = {attrs["id"]: attrs for tag, attrs in page.tags if tag == "section"}
    assert "hidden" not in views["view-start"]
    assert all(
        "hidden" in views[name]
        for name in ("view-prepare", "view-results", "view-drawer", "view-missing")
    )
    # Drawer details builds its human title from the loaded result.
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
    assert "Not for real cash control." in text
    assert "Files are checked, then deleted. Nothing is saved." in text
    assert "Upload demo CSVs" in text
    assert (
        "Results disappear when you refresh or close this page. "
        "Download a report to keep a copy."
    ) in text


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
        # Screen readers announce the row header, so it carries the whole line's words.
        spoken = f"{line.spoken} {line.label}".strip()
        assert f'<th scope="row" aria-label="{spoken}">' in drawer
        assert (
            f"<dt>{line.label}</dt>" in html and f"<dd>{line.definition}</dd>" in html
        )
        if line.spoken:
            assert f'<span class="visually-hidden">{line.spoken} </span>' in drawer
    assert "<details" not in re.search(
        r'data-tape="example">(.*?)</table>', html, re.S
    ).group(1)


def test_results_reading_order_and_download_emphasis(client) -> None:
    """One set of filters precedes review; downloads follow it and stay secondary."""
    page, _ = _page(client)
    ids = [attrs.get("id") for tag, attrs in page.tags if "id" in attrs]
    expected = [
        "summary-headline",
        "filters",
        "leads-heading",
        "lead-list",
        "downloads-heading",
        "more-detail-heading",
        "day-details",
    ]
    assert [name for name in ids if name in expected] == expected
    assert ids.count("filter-date") == ids.count("filter-level") == 1
    assert not any(int(attrs.get("tabindex", "0")) > 0 for tag, attrs in page.tags)
    buttons = [attrs for tag, attrs in page.tags if "data-report" in attrs]
    assert all(
        "button-secondary" in attrs["class"] and "button-primary" not in attrs["class"]
        for attrs in buttons
    )


def test_results_detail_previews_and_group_units(client) -> None:
    """Optional tables keep plain previews; grouped headings distinguish drawers and dates."""
    page, text = _page(client)
    group = next(attrs for tag, attrs in page.tags if attrs.get("id") == "lead-list")
    assert group["role"] == "group"
    assert group["aria-labelledby"] == "leads-heading"
    assert group["data-drawers-one"] == "drawer"
    assert group["data-drawers-many"] == "drawers"
    assert group["data-dates-one"] == "date"
    assert group["data-dates-many"] == "dates"
    assert "Matching drawers" in group.values()
    previews = [
        attrs for tag, attrs in page.tags if attrs.get("class") == "help-preview"
    ]
    assert len(previews) == 6
    assert all("open" not in attrs for tag, attrs in page.tags if tag == "details")
    assert (
        "More detail" in text and "Every drawer, including those without leads." in text
    )


def test_drawer_outcomes_toggle_and_availability_ticks_have_semantics(client) -> None:
    """Drawer controls distinguish supplied zero rows and decorative input availability."""
    page, text = _page(client)
    slots = [
        attrs["data-outcome"] for tag, attrs in page.tags if "data-outcome" in attrs
    ]
    assert slots == ["expected", "counted", "difference"]
    toggle = next(
        attrs for tag, attrs in page.tags if attrs.get("id") == "count-toggle"
    )
    assert (
        toggle["aria-expanded"] == "false" and toggle["aria-controls"] == "count-rows"
    )
    assert "hidden" in toggle
    ticks = [attrs for tag, attrs in page.tags if attrs.get("class") == "input-tick"]
    assert len(ticks) == 6
    assert all(attrs["aria-hidden"] == "true" and "hidden" in attrs for attrs in ticks)
    assert "Ticked values are available for this calculation." in text
    assert "A zero for safe drops does not prove a source row was supplied." in text
    next_drawer = next(
        attrs for tag, attrs in page.tags if attrs.get("id") == "next-drawer"
    )
    assert "hidden" in next_drawer
    assert not any("Looked at" in word for word in page.text)


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
    plural_labels = [
        attrs for tag, attrs in page.tags if tag == "span" and "data-one" in attrs
    ]
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


def test_navigation_waiting_and_download_hooks(client) -> None:
    """Views are reached by #/ addresses, timings come from Python, and every report downloads."""
    page, text = _page(client)
    with client.post("/api/demo") as response:
        payload = response.get_json()
    body = next(attrs for tag, attrs in page.tags if tag == "body")
    assert body["data-slow-notice-ms"] == str(web.SLOW_NOTICE_MS) == "5000"
    assert body["data-give-up-ms"] == str(web.GIVE_UP_MS) == "90000"
    reports = [
        attrs["data-report"] for tag, attrs in page.tags if "data-report" in attrs
    ]
    assert sorted(reports) == sorted(payload["reports"])
    assert not any("data-go" in attrs for tag, attrs in page.tags)
    in_page = [
        attrs["href"]
        for tag, attrs in page.tags
        if tag == "a" and attrs["href"].startswith("#")
    ]
    # The skip link is the only in-page link that is not a view address.
    assert [href for href in in_page if not href.startswith("#/")] == ["#main"]
    assert {"#/", "#/prepare", "#/results"} <= set(in_page)
    for words in (
        "Results are not saved. Run the example again or upload your files.",
        "This drawer is not in the current results",
        "The demo server may be waking up. This usually takes about a minute.",
    ):
        assert words in text
    cancels = [
        attrs for tag, attrs in page.tags if attrs.get("id", "").endswith("-cancel")
    ]
    assert len(cancels) == 2 and all("hidden" in attrs for attrs in cancels)


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
    every_url = re.findall(r'url\("([^"]+)"\)', css)
    # Anything that is not a font file must be an inline image, never a remote address.
    urls = [url for url in every_url if not url.startswith("data:")]
    assert all(
        url.startswith("data:image/svg+xml,") for url in every_url if url not in urls
    )
    assert len(urls) == 2 and css.count("font-display: swap") == 2
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
    for family in ("next", "mono"):
        license_text = (STATIC / "fonts" / f"LICENSE-{family}.txt").read_text(
            encoding="utf-8"
        )
        assert "SIL Open Font License, Version 1.1" in license_text
        assert "Copyright" in license_text


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


def test_render_blueprint_matches_stateless_gunicorn_contract() -> None:
    """The Render Blueprint uses the free Python plan, 30s timeout, and no disk or DB."""
    blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")
    expected_start = (
        "gunicorn --bind 0.0.0.0:$PORT --workers 2 --worker-class sync "
        "--threads 1 --timeout 30 "
        '"drawercheck.web:create_app()"'
    )
    for line in (
        "type: web",
        "name: drawercheck",
        "runtime: python",
        "plan: free",
        'buildCommand: pip install ".[web]"',
        f"startCommand: {expected_start}",
        "healthCheckPath: /",
        "key: PYTHON_VERSION",
        "value: 3.13.5",
    ):
        assert line in blueprint, line
    for forbidden in ("disk:", "databases:", "keyvalue"):
        assert forbidden not in blueprint, forbidden
    if sys.platform != "win32" and importlib.util.find_spec("gunicorn") is not None:
        command = shlex.split(expected_start.replace("0.0.0.0:$PORT", "127.0.0.1:0"))
        assert command[0] == "gunicorn"
        completed = subprocess.run(
            [sys.executable, "-m", "gunicorn", "--check-config", *command[1:]],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr


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


def test_design_guide_matches_the_shared_colour_tokens() -> None:
    """Keep the maintained design guide in sync with both runtime themes."""
    guide = (ROOT / "DESIGN.md").read_text(encoding="utf-8")
    table = guide.split("### Colour", 1)[1].split("### Typography", 1)[0]
    documented: dict[str, dict[str, str]] = {"light": {}, "dark": {}}
    for line in table.splitlines():
        columns = [cell.strip() for cell in line.split("|")[1:-1]]
        if not columns or not (match := re.match(r"`([a-z-]+)`", columns[0])):
            continue
        name = match.group(1)
        for theme, column in (("light", 2), ("dark", 3)):
            colours = re.findall(r"#[0-9a-fA-F]{6}", columns[column])
            documented[theme][name] = colours[0].lower()
            if len(colours) == 2:
                documented[theme][name + "-bg"] = colours[1].lower()
    assert documented == _themes()


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
    ("ready", "surface", 3),  # Decorative logo tick, kept legible anyway.
    ("check", "surface", 4.5),
    ("note", "surface", 4.5),
]


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_colour_tokens_meet_wcag_contrast(theme: str) -> None:
    tokens = _themes()[theme]
    assert set(_themes()["light"]) == set(_themes()["dark"])
    for foreground, background, minimum in CONTRAST_PAIRS:
        ratio = _contrast(tokens[foreground], tokens[background])
        assert ratio >= minimum, (foreground, background, round(ratio, 2))
