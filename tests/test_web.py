"""Verify bounded uploads, shared results, and cleanup without an external server."""

import csv
import importlib
import re
import sqlite3
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier
from typing import get_args, get_type_hints

import pytest

from drawercheck import db, errors, rules
from drawercheck.cli import main
from drawercheck.config import Config
from drawercheck.csv_contract import CSV_HEADERS
from drawercheck.demo import generate_demo
from drawercheck.models import Flag, ShiftResult
from drawercheck.money import format_cents, parse_dollars
from drawercheck.reconcile import explain_shift
from drawercheck.reports import ReportData, csv_out, html, load_report, text

pytest.importorskip("flask")
web = importlib.import_module("drawercheck.web")
GENERATED_AT = datetime(2026, 10, 23, 12, tzinfo=UTC)


@pytest.fixture
def app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Track temporary workspaces and use a fixed report timestamp."""
    workspaces = []

    def temporary(**kwargs):
        workspace = TemporaryDirectory(dir=tmp_path, **kwargs)
        workspaces.append(Path(workspace.name))
        return workspace

    monkeypatch.setattr(web, "TemporaryDirectory", temporary)
    monkeypatch.setattr(
        web, "load_report", lambda path: load_report(path, generated_at=GENERATED_AT)
    )
    app = web.create_app()
    app.config["TESTING"] = True
    yield app
    assert workspaces and all(not path.exists() for path in workspaces)


def _upload(client, directory: Path, **kwargs):
    response = client.post(
        "/api/check",
        data={
            "files": [
                (BytesIO((directory / name).read_bytes()), name) for name in CSV_HEADERS
            ]
        },
        **kwargs,
    )
    response.get_data()
    # The test client owns its separate multipart-encoding input file.
    response.request.input_stream.close()
    response.close()
    return response


def test_demo_upload_and_cli_match(app, tmp_path: Path) -> None:
    """The full month has identical reports, flags, and all shift explanations."""
    directory, database = tmp_path / "cli-inputs", tmp_path / "cli.db"
    assert main(["demo-data", "--out", str(directory)]) == 0
    assert main(["import", "--dir", str(directory), "--db", str(database)]) == 0
    assert main(["reconcile", "--db", str(database)]) == 0
    report = load_report(database, generated_at=GENERATED_AT)
    with app.test_client() as client:
        demo = client.post("/api/demo")
        upload = _upload(client, directory)
    assert demo.status_code == upload.status_code == 200
    payload = demo.get_json()
    assert payload == upload.get_json()
    assert len(payload["shifts"]) == 60 and len(payload["flags"]) == 18
    assert len(payload["days"]) == 30
    for name, render in (
        ("text", text.render),
        ("html", html.render),
        ("csv", csv_out.render),
    ):
        assert payload["reports"][name]["content"] == render(report)
    for item in payload["shifts"]:
        explanation = explain_shift(database, item["shift"]["shift_code"])
        assert item["expected_amount"] == web.format_amount(
            explanation.result.expected_cents
        )
        assert item["counted_amount"] == web.format_amount(
            explanation.result.counted_cents
        )
        assert item["variance_amount"] == web.format_amount(
            explanation.result.variance_cents
        )
        assert item["deposit_contribution_amount"] == web.format_amount(
            explanation.deposit_contribution_cents
        )
        assert item["daily_deposit_amount"] == web.format_amount(
            explanation.daily_deposit_cents
        )
        assert [flag["message"] for flag in item["flags"]] == [
            flag.message for flag in explanation.result.flags
        ]
        assert [flag["message"] for flag in item["daily_flags"]] == [
            flag.message for flag in explanation.daily_flags
        ]
    assert demo.headers["Cache-Control"] == "no-store"
    assert demo.headers["X-Content-Type-Options"] == "nosniff"
    assert "Set-Cookie" not in demo.headers


def _dollars_to_cents(amount: str) -> int:
    return parse_dollars(amount.replace("$", "").replace(",", ""))


def test_screen_fields_match_cli_results(app, tmp_path: Path) -> None:
    """The summary, count line totals, and labels agree with the CLI's saved results."""
    directory, database = tmp_path / "cli-inputs", tmp_path / "cli.db"
    assert main(["demo-data", "--out", str(directory)]) == 0
    assert main(["import", "--dir", str(directory), "--db", str(database)]) == 0
    assert main(["reconcile", "--db", str(database)]) == 0
    report = load_report(database, generated_at=GENERATED_AT)
    with app.test_client() as client:
        payload = client.post("/api/demo").get_json()
    severities = Counter(flag.severity for flag in report.flags)
    assert payload["summary"] == {
        "drawers_with_leads": 9,
        "drawers_without_leads": 51,
        "drawers_by_highest_severity": {"info": 0, "warn": 5, "review": 4},
        "drawer_leads_total": 16,
        "whole_day_leads_total": 2,
        "whole_day_lead_days": 2,
        "drawers_checked": len(report.shifts),
        "drawers_needing_review": len(
            {
                flag.shift_id
                for flag in report.flags
                if flag.shift_id is not None and flag.severity == "review"
            }
        ),
        "leads_total": len(report.flags),
        "leads_by_severity": {
            "info": severities["info"],
            "warn": severities["warn"],
            "review": severities["review"],
        },
        "deposit_lead_days": len(
            {
                flag.business_date
                for flag in report.flags
                if flag.rule_code == "R08_DEPOSIT"
            }
        ),
    }
    # Full-run counts include the two R03 heuristic notes, without double-counting drawers.
    assert payload["summary"] == {
        "drawers_with_leads": 9,
        "drawers_without_leads": 51,
        "drawers_by_highest_severity": {"info": 0, "warn": 5, "review": 4},
        "drawer_leads_total": 16,
        "whole_day_leads_total": 2,
        "whole_day_lead_days": 2,
        "drawers_checked": 60,
        "drawers_needing_review": 4,
        "leads_total": 18,
        "leads_by_severity": {"info": 4, "warn": 7, "review": 7},
        "deposit_lead_days": 2,
    }
    hints = [
        flag
        for flag in payload["flags"]
        if flag["rule_code"] == "R03_TRANSPOSITION_HINT"
    ]
    assert len(hints) == 2
    assert (
        payload["labels"]["rules"]["R03_TRANSPOSITION_HINT"]
        == "Possible swapped digits"
    )
    assert all(flag["severity"] == "info" for flag in hints)
    for item in payload["shifts"]:
        result = explain_shift(database, item["shift"]["shift_code"]).result
        rows = item["shift"]["counts"]
        assert [(row["denomination"], row["quantity"]) for row in rows] == [
            (format_cents(denomination), quantity)
            for denomination, quantity in result.shift.counts
        ]
        line_totals = [_dollars_to_cents(row["line_total_amount"]) for row in rows]
        if result.counted_cents is None:
            assert line_totals == []
        else:
            assert sum(line_totals) == result.counted_cents
    worked = next(
        item
        for item in payload["shifts"]
        if item["shift"]["shift_code"] == "2026-09-03-R1"
    )
    assert [row["line_total_amount"] for row in worked["shift"]["counts"][:3]] == [
        "$400.00",
        "$50.00",
        "$40.00",
    ]
    labels = payload["labels"]
    assert {flag["rule_code"] for flag in payload["flags"]} == set(labels["rules"])
    assert labels["severities"] == {
        "info": "Note",
        "warn": "Check",
        "review": "Needs review",
    }
    assert labels["statuses"]["balanced"] == "Balanced (within $1.00)"
    assert {item["status"] for item in payload["shifts"]} <= set(labels["statuses"])
    # Labels are sent once, never repeated on each flag.
    assert all("label" not in key for flag in payload["flags"] for key in flag)


@pytest.mark.parametrize("case", ["empty", "clean", "notes", "mixed", "day-only"])
def test_summary_counts_keep_drawers_leads_and_days_separate(
    worked_shift, case: str
) -> None:
    """Mixed-level drawers count once; any rule can produce a whole-day lead."""
    note = Flag(1, "2026-09-03", "R03_TRANSPOSITION_HINT", "info", "Hint only.", {})
    review = replace(note, rule_code="R01_VARIANCE", severity="review")
    day = replace(note, shift_id=None, rule_code="R09_DATA_QUALITY", severity="warn")
    deposit = replace(day, rule_code="R08_DEPOSIT", business_date="2026-09-04")
    own = {"notes": (note,), "mixed": (note, review)}.get(case, ())
    shifts = (
        ()
        if case in ("empty", "day-only")
        else (ShiftResult(worked_shift, 0, 0, 0, "balanced", flags=own),)
    )
    flags = own + (
        (day, replace(day, severity="info"), deposit)
        if case in ("mixed", "day-only")
        else ()
    )
    report = ReportData("2026-09-03", "2026-09-04", "", Config(), shifts, flags, (), ())
    summary = web._summary(report)
    affected = int(bool(own))
    assert summary["drawers_with_leads"] == affected
    assert summary["drawers_without_leads"] == len(shifts) - affected
    assert summary["drawers_by_highest_severity"] == {
        "info": int(case == "notes"),
        "warn": 0,
        "review": int(case == "mixed"),
    }
    assert (
        summary["drawers_with_leads"] + summary["drawers_without_leads"]
        == summary["drawers_checked"]
    )
    assert sum(summary["drawers_by_highest_severity"].values()) == affected
    assert (
        summary["drawers_needing_review"]
        == summary["drawers_by_highest_severity"]["review"]
    )
    assert summary["drawer_leads_total"] == len(own)
    assert (
        summary["drawer_leads_total"] + summary["whole_day_leads_total"]
        == summary["leads_total"]
    )
    assert summary["whole_day_leads_total"] == (
        3 if case in ("mixed", "day-only") else 0
    )
    assert summary["whole_day_lead_days"] == (2 if case in ("mixed", "day-only") else 0)
    assert summary["deposit_lead_days"] == int(case in ("mixed", "day-only"))


@pytest.mark.parametrize(
    ("rule", "evidence", "expected"),
    [
        (
            "R01_VARIANCE",
            {
                "within_tolerance_cents": 100,
                "warn_cents": 500,
                "review_threshold_cents": 1250,
            },
            "Balanced up to $1.00; Check at $5.00; Needs review at $12.50.",
        ),
        (
            "R04_REPEAT_SHORT",
            {"min_shifts": 3, "warn_cents": 500, "window": 10},
            "Pattern limit: at least 3 shortages of $5.00 or more in the last 10 shifts.",
        ),
        (
            "R05_MISSING_VERIFIER_OR_NOTE",
            {"required_at_cents": 2000},
            "Sign-off required for differences of $20.00 or more.",
        ),
        (
            "R08_DEPOSIT",
            {"issue": "mismatch", "max_lag_days": 1},
            "Matching window: 1 day after the business date. Differences of $77.00 or more need review.",
        ),
        (
            "R08_DEPOSIT",
            {"issue": "missing", "max_lag_days": 0},
            "Matching window: 0 days after the business date.",
        ),
        ("R08_DEPOSIT", {"issue": "unexpected"}, ""),
        ("R02_SINGLE_DENOMINATION", {"denomination_cents": 100}, ""),
        ("R03_TRANSPOSITION_HINT", {"heuristic": True}, ""),
        ("R09_DATA_INTEGRITY", {"issue": "missing_pos"}, ""),
    ],
)
def test_drawer_lead_limits_use_the_saved_evidence(rule, evidence, expected) -> None:
    """Money limits come from Python; heuristics and record problems get no invented limit."""
    flag = Flag(1, "2026-09-03", rule, "review", "Demo message.", evidence)
    values = web._lead_data(flag, replace(Config(), review_cents=7700))
    assert values["limit_text"] == expected
    assert values["message"] == flag.message and values["evidence"] == evidence


def test_date_labels_cover_range_and_overnight_clock_dates(worked_shift) -> None:
    """Python provides English calendar dates across midnight, months, and years."""
    shift = replace(
        worked_shift, opened_at="2026-09-02T23:00:00", closed_at="2026-09-04T01:00:00"
    )
    result = ShiftResult(shift, None, None, None, "incomplete")
    flag = Flag(None, "2027-02-01", "R09_DATA_QUALITY", "info", "Demo note.", {})
    report = ReportData(
        "2026-12-31", "2027-01-01", "", Config(), (result,), (flag,), (), ()
    )
    assert web._date_labels(report) == {
        "2026-09-02": "Wednesday, September 2, 2026",
        "2026-09-03": "Thursday, September 3, 2026",
        "2026-09-04": "Friday, September 4, 2026",
        "2026-12-31": "Thursday, December 31, 2026",
        "2027-01-01": "Friday, January 1, 2027",
        "2027-02-01": "Monday, February 1, 2027",
    }


def test_labels_cover_every_rule_severity_and_status() -> None:
    """A new rule code or status cannot reach the screens without public words."""
    source = Path(rules.__file__).read_text(encoding="utf-8")
    assert set(re.findall(r'"(R\d\d_[A-Z_]+)"', source)) == set(web.RULE_LABELS)
    assert set(get_args(get_type_hints(Flag)["severity"])) == set(web.SEVERITY_LABELS)
    assert set(get_args(get_type_hints(ShiftResult)["status"])) == set(
        web.STATUS_LABELS
    )


def test_example_files_match_the_built_in_demo(app) -> None:
    """Each download is the committed demo CSV, so it uploads as the example."""
    demo_inputs = Path(__file__).parent.parent / "data" / "demo"
    with app.test_client() as client:
        for name in CSV_HEADERS:
            response = client.get(f"/examples/{name}")
            assert response.status_code == 200
            assert response.mimetype == "text/csv"
            assert response.headers["Content-Disposition"] == (
                f'attachment; filename="{name}"'
            )
            assert response.get_data() == (demo_inputs / name).read_bytes()


@pytest.mark.parametrize(
    "path", ["/examples/other.csv", "/examples/SHIFTS.csv", "/examples/..%2Frun.db"]
)
def test_example_files_reject_other_names(path: str) -> None:
    with web.create_app().test_client() as client:
        response = client.get(path)
    assert response.status_code == 404
    assert response.get_json()["error"]["message"] == errors.WEB_NOT_FOUND


def test_upload_preserves_bom_crlf_and_raw_bytes(
    app, csv_directory: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Web saves original bytes; the importer owns CSV and encoding handling."""
    source = csv_directory / "cashiers.csv"
    source.write_bytes(b"\xef\xbb\xbf" + source.read_bytes().replace(b"\n", b"\r\n"))
    expected = {name: (csv_directory / name).read_bytes() for name in CSV_HEADERS}
    original = web.import_directory

    def inspect(directory, database, **kwargs):
        assert {
            name: (directory / name).read_bytes() for name in CSV_HEADERS
        } == expected
        return original(directory, database, **kwargs)

    monkeypatch.setattr(web, "import_directory", inspect)
    with app.test_client() as client:
        assert _upload(client, csv_directory).status_code == 200


@pytest.mark.parametrize(
    "name",
    [
        "../shifts.csv",
        "/tmp/shifts.csv",
        "folder\\shifts.csv",
        "data.zip",
        "SHIFTs.csv",
        "",
        "<script>.csv",
    ],
)
def test_rejects_unexpected_filenames(app, name: str) -> None:
    with app.test_client() as client:
        response = client.post(
            "/api/check", data={"files": (BytesIO(b"data"), name.replace("\\", "\\\\"))}
        )
    assert response.status_code == 400
    assert response.get_json()["error"]["message"] == errors.WEB_FILENAME.format(
        name=name
    )


@pytest.mark.parametrize(
    "case",
    [
        "missing",
        "duplicate",
        "field",
        "wrong-key",
        "query",
        "not-multipart",
        "no-files",
    ],
)
def test_rejects_wrong_upload_shape(app, csv_directory: Path, case: str) -> None:
    files = [
        (BytesIO((csv_directory / name).read_bytes()), name) for name in CSV_HEADERS
    ]
    data, url = {"files": files}, "/api/check"
    expected = errors.WEB_FIELDS
    if case == "missing":
        data["files"] = files[:-1]
        expected = errors.WEB_MISSING.format(names="bank_deposits.csv")
    elif case == "duplicate":
        data["files"].append((BytesIO(b"x"), "shifts.csv"))
        expected = errors.WEB_DUPLICATE.format(name="shifts.csv")
    elif case == "field":
        data["settings"] = "ignored?"
    elif case == "wrong-key":
        data = {"other": files}
    elif case == "query":
        url += "?db=local.db"
    elif case == "not-multipart":
        data = "not a form"
        expected = errors.WEB_MULTIPART
    elif case == "no-files":
        data = {}
        expected = errors.WEB_MISSING.format(names=", ".join(CSV_HEADERS))
    with app.test_client() as client:
        response = client.post(
            url,
            data=data,
            content_type="multipart/form-data" if case == "no-files" else None,
        )
    assert response.status_code == 400
    assert response.get_json()["error"]["message"] == expected


@pytest.mark.parametrize("case", ["body", "query", "file"])
def test_demo_rejects_options_and_uploads(app, case: str) -> None:
    with app.test_client() as client:
        response = client.post(
            "/api/demo?days=500" if case == "query" else "/api/demo",
            data={"files": (BytesIO(b"x"), "shifts.csv")}
            if case == "file"
            else b"x"
            if case == "body"
            else None,
        )
    assert response.status_code == 400
    assert response.get_json()["error"]["message"] == errors.WEB_DEMO_BODY


@pytest.mark.parametrize(
    "case", ["money", "encoding", "header", "empty", "multiline", "reference"]
)
def test_readable_source_errors(app, csv_directory: Path, case: str) -> None:
    name, line, column = "bank_deposits.csv", 2, "amount"
    content = b"deposit_date,amount,reference\n2026-09-01,1.234,DEMO\n"
    if case == "encoding":
        name, line, column, content = (
            "cashiers.csv",
            2,
            "<encoding>",
            b"cashier_id,display_name\n\xff\n",
        )
    elif case == "header":
        name, line, column, content = "cashiers.csv", 1, "<header>", b"cashier_id\n"
    elif case == "empty":
        name, line, column, content = "cashiers.csv", 1, "<header>", b""
    elif case == "multiline":
        name, line, column, content = (
            "cashiers.csv",
            4,
            "display_name",
            b'cashier_id,display_name\ncashier_01,"Demo\nName"\ncashier_02,\n',
        )
    elif case == "reference":
        name, line, column = "shifts.csv", 5, "cashier_id"
        content = (
            (csv_directory / name).read_bytes().replace(b"cashier_01", b"DEMO-UNKNOWN")
        )
    (csv_directory / name).write_bytes(content)
    with app.test_client() as client:
        response = _upload(client, csv_directory)
    assert response.status_code == 400
    error = response.get_json()["error"]
    assert (error["file_name"], error["line_number"], error["column"]) == (
        name,
        line,
        column,
    )
    assert f"source line {line}" in error["message"]
    assert (
        "drawercheck " not in error["message"] and "Traceback" not in error["message"]
    )
    if case == "reference":
        assert "DEMO-UNKNOWN" in error["message"] and "cashier_id" in error["message"]


def _multipart(directory: Path, extra: bytes = b"") -> bytes:
    parts = []
    for name in CSV_HEADERS:
        data = (directory / name).read_bytes()
        if name == "cashiers.csv":
            data += extra
        parts.append(
            f'--demo-boundary\r\nContent-Disposition: form-data; name="files"; filename="{name}"\r\nContent-Type: text/csv\r\n\r\n'.encode()
            + data
            + b"\r\n"
        )
    return b"".join(parts) + b"--demo-boundary--\r\n"


@pytest.mark.parametrize("difference", [-1, 0, 1])
def test_total_request_limit_boundary(
    app, csv_directory: Path, difference: int
) -> None:
    padding = web.MAX_REQUEST_BYTES + difference - len(_multipart(csv_directory))
    # Whitespace-only CSV lines stay valid and below the CSV field-size limit.
    extra = (b" " * 1024 + b"\n") * (padding // 1025) + b" " * (padding % 1025)
    body = _multipart(csv_directory, extra)
    assert len(body) == web.MAX_REQUEST_BYTES + difference
    with app.test_client() as client:
        response = client.post(
            "/api/check",
            data=body,
            content_type="multipart/form-data; boundary=demo-boundary",
        )
    assert response.status_code == (413 if difference > 0 else 200)
    if difference > 0:
        assert response.get_json()["error"]["message"] == errors.WEB_TOO_LARGE


@pytest.mark.parametrize("extra_shift", [False, True])
def test_shift_limit_before_database(
    app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, extra_shift: bool
) -> None:
    directory = tmp_path / "large-demo"
    generate_demo(directory, days=500)
    if extra_shift:
        with (directory / "shifts.csv").open("a") as stream:
            stream.write(
                "DEMO-EXTRA,2028-01-14,R1,cashier_01,2028-01-14T08:00:00,2028-01-14T16:00:00,200.00,,\n"
            )

        def forbidden(*args, **kwargs):
            pytest.fail("Oversized shift set opened a database")

        monkeypatch.setattr(db, "connect", forbidden)
    with app.test_client() as client:
        response = _upload(client, directory)
    assert response.status_code == (400 if extra_shift else 200)
    if extra_shift:
        assert response.get_json()["error"]["message"] == errors.WEB_SHIFT_LIMIT
    else:
        assert len(response.get_json()["shifts"]) == 1000


def test_html_escape_csv_protection_and_unknown_amounts(
    app, csv_directory: Path
) -> None:
    source = csv_directory / "cashiers.csv"
    source.write_text(
        source.read_text().replace("Demo Cashier 01", "<script>alert('demo')</script>")
    )
    for name in CSV_HEADERS:
        source = csv_directory / name
        source.write_text(source.read_text().replace("2026-09-03-R1", "=DEMO-SHIFT"))
    # Missing counts are unknown, not a counted zero.
    source = csv_directory / "cash_counts.csv"
    lines = source.read_text().splitlines(keepends=True)
    source.write_text(
        "".join(line for line in lines if not line.startswith("2026-09-01-R1,"))
    )
    with app.test_client() as client:
        response = _upload(client, csv_directory)
    assert response.status_code == 200
    payload = response.get_json()
    rendered = payload["reports"]["html"]["content"]
    assert "<script>" not in rendered and "&lt;script&gt;" in rendered
    assert "<script src" not in rendered and "<script>" not in rendered
    rows = list(csv.DictReader(StringIO(payload["reports"]["csv"]["content"])))
    assert any(row["shift_code"] == "'=DEMO-SHIFT" for row in rows)
    missing = next(
        item
        for item in payload["shifts"]
        if item["shift"]["shift_code"] == "2026-09-01-R1"
    )
    assert missing["counted_amount"] == missing["variance_amount"] == "unknown"


@pytest.mark.parametrize(
    "stage", ["import", "reconcile", "report", "serialize", "save"]
)
def test_failures_close_connections_and_remove_workspaces(
    app, monkeypatch: pytest.MonkeyPatch, stage: str, caplog
) -> None:
    connections = []
    original = db.connect

    def connect(path):
        connection = original(path)
        connections.append(connection)
        return connection

    def fail(*args, **kwargs):
        raise RuntimeError("SECRET UPLOADED CONTENT AND PRIVATE PATH")

    monkeypatch.setattr(db, "connect", connect)
    targets = {
        "import": "import_directory",
        "reconcile": "reconcile",
        "report": "load_report",
        "serialize": "_response_data",
    }
    if stage == "save":
        monkeypatch.setattr(db, "save_reconciliation", fail)
    else:
        monkeypatch.setattr(web, targets[stage], fail)
    with app.test_client() as client:
        response = client.post("/api/demo")
    assert response.status_code == 503
    assert response.get_json()["error"]["message"] == errors.WEB_UNAVAILABLE
    assert "SECRET" not in response.get_data(as_text=True) + caplog.text
    for connection in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("SELECT 1")


def test_success_closes_connections(app, monkeypatch: pytest.MonkeyPatch) -> None:
    connections = []
    original = db.connect

    def connect(path):
        connection = original(path)
        connections.append(connection)
        return connection

    monkeypatch.setattr(db, "connect", connect)
    with app.test_client() as client:
        assert client.post("/api/demo").status_code == 200
    assert len(connections) == 3
    for connection in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("SELECT 1")


def test_concurrent_runs_do_not_mix_data_or_touch_local_database(
    app, csv_directory: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    local = Path("drawercheck.db")
    local.write_bytes(b"LOCAL DATABASE MUST STAY UNCHANGED")
    barrier = Barrier(2, timeout=15)
    original = web.import_directory
    paths = []

    def together(directory, database, **kwargs):
        paths.append(database)
        barrier.wait()
        return original(directory, database, **kwargs)

    monkeypatch.setattr(web, "import_directory", together)
    source = csv_directory / "cashiers.csv"
    source.write_text(
        source.read_text().replace("Demo Cashier 01", "UNIQUE UPLOAD NAME")
    )

    def run(demo):
        with app.test_client() as client:
            response = (
                client.post("/api/demo") if demo else _upload(client, csv_directory)
            )
            assert response.status_code == 200
            return response.get_json()

    with ThreadPoolExecutor(max_workers=2) as pool:
        demo_future, upload_future = pool.submit(run, True), pool.submit(run, False)
        demo, upload = demo_future.result(), upload_future.result()
    assert len(paths) == len(set(paths)) == 2
    assert all(not path.parent.exists() for path in paths)
    assert len(demo["shifts"]) == 60 and len(upload["shifts"]) == 6
    assert "UNIQUE UPLOAD NAME" not in demo["reports"]["html"]["content"]
    assert "UNIQUE UPLOAD NAME" in upload["reports"]["html"]["content"]
    assert local.read_bytes() == b"LOCAL DATABASE MUST STAY UNCHANGED"


def test_empty_records_have_web_guidance(app, csv_directory: Path) -> None:
    for name, headers in CSV_HEADERS.items():
        (csv_directory / name).write_text(",".join(headers) + "\n")
    with app.test_client() as client:
        response = _upload(client, csv_directory)
    assert response.status_code == 400
    assert response.get_json()["error"]["message"] == errors.WEB_EMPTY


def test_bank_only_dates_do_not_invent_shifts(app, csv_directory: Path) -> None:
    for name, headers in CSV_HEADERS.items():
        if name != "bank_deposits.csv":
            (csv_directory / name).write_text(",".join(headers) + "\n")
    with app.test_client() as client:
        response = _upload(client, csv_directory)
    assert response.status_code == 200
    payload = response.get_json()
    assert not payload["shifts"] and not payload["cashiers"]
    assert (
        payload["summary"]["drawers_checked"]
        == payload["summary"]["drawers_with_leads"]
        == 0
    )
    dates = {payload["from_date"], payload["to_date"]}
    dates.update(day["business_date"] for day in payload["days"])
    dates.update(flag["business_date"] for flag in payload["flags"])
    assert dates == set(payload["labels"]["dates"])
    assert all(
        "undefined" not in value and ", " in value
        for value in payload["labels"]["dates"].values()
    )
    assert all(
        day["expected_deposit_amount"] == "Not calculated (no shifts)"
        for day in payload["days"]
    )


@pytest.mark.parametrize(
    "exception",
    [
        OSError("PRIVATE PATH"),
        sqlite3.OperationalError("PRIVATE DATABASE"),
        errors.DatabaseVersionError("PRIVATE VERSION"),
    ],
)
def test_internal_errors_hide_paths_and_cli_instructions(
    app, monkeypatch: pytest.MonkeyPatch, exception: Exception
) -> None:
    def fail(*args, **kwargs):
        raise exception

    monkeypatch.setattr(web, "import_directory", fail)
    with app.test_client() as client:
        response = client.post("/api/demo")
    assert response.status_code == 503
    assert response.get_json()["error"]["message"] == errors.WEB_UNAVAILABLE


def test_http_errors_are_json_and_debug_is_off() -> None:
    app = web.create_app()
    assert app.debug is False
    with app.test_client() as client:
        response = client.get("/api/demo")
        assert response.get_json()["error"]["message"] == errors.WEB_METHOD
        assert "POST" in response.headers["Allow"]
        assert (
            client.get("/missing").get_json()["error"]["message"]
            == errors.WEB_NOT_FOUND
        )


def test_zero_counts_stay_zero_and_unknown_cashier_totals_stay_unknown(
    app, csv_directory: Path
) -> None:
    counts = csv_directory / "cash_counts.csv"
    with counts.open(newline="") as stream:
        rows = list(csv.reader(stream))
    with counts.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(rows[0])
        for code, denomination, quantity in rows[1:]:
            if code == "2026-09-01-R1":
                writer.writerow((code, denomination, "0"))
    with app.test_client() as client:
        response = _upload(client, csv_directory)
    assert response.status_code == 200
    payload = response.get_json()
    zero = next(
        item
        for item in payload["shifts"]
        if item["shift"]["shift_code"] == "2026-09-01-R1"
    )
    assert zero["counted_amount"] == "$0.00"
    assert zero["variance_amount"] != "unknown"
    unknown_cashiers = [item for item in payload["cashiers"] if not item["known"]]
    assert unknown_cashiers
    assert all(item["net_amount"] == "unknown" for item in unknown_cashiers)


@pytest.mark.parametrize("case", ["many-parts", "large-field", "malformed"])
def test_multipart_parser_limits_and_bad_body(app, case: str) -> None:
    if case == "many-parts":
        data = {f"field{index}": "value" for index in range(9)}
    elif case == "large-field":
        data = {"extra": "x" * (128 * 1024 + 1)}
    else:
        data = b"--broken-header\r\nnot a multipart form"
    with app.test_client() as client:
        response = client.post(
            "/api/check", data=data, content_type="multipart/form-data"
        )
    assert response.status_code == (400 if case == "malformed" else 413)
    assert response.is_json and "Traceback" not in response.get_data(as_text=True)


@pytest.mark.parametrize("too_large", [False, True])
def test_wsgi_stream_limit_without_content_length(
    app, csv_directory: Path, too_large: bool
) -> None:
    body = _multipart(csv_directory, b" " * web.MAX_REQUEST_BYTES if too_large else b"")
    with app.test_client() as client:
        response = client.post(
            "/api/check",
            data=body,
            content_type="multipart/form-data; boundary=demo-boundary",
            environ_overrides={"CONTENT_LENGTH": "", "wsgi.input_terminated": True},
        )
    assert response.status_code == (413 if too_large else 200)


def test_upload_streams_close_even_on_rejection(
    app, csv_directory: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    streams = []
    original = app.request_class._get_file_stream

    def track(self, *args, **kwargs):
        stream = original(self, *args, **kwargs)
        streams.append(stream)
        return stream

    monkeypatch.setattr(app.request_class, "_get_file_stream", track)
    with app.test_client() as client:
        assert _upload(client, csv_directory).status_code == 200
        with client.post(
            "/api/check", data={"files": (BytesIO(b"x" * 600_000), "bad.csv")}
        ) as response:
            assert response.status_code == 400
            response.request.input_stream.close()
    assert len(streams) == 8 and all(stream.closed for stream in streams)


def test_local_config_cannot_change_web_policies(
    app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    Path("config.toml").write_text("deliberately invalid local settings")
    with app.test_client() as client:
        response = client.post("/api/demo")
    assert response.status_code == 200
    assert len(response.get_json()["flags"]) == 18


def test_partial_upload_save_failure_removes_files(
    app, csv_directory: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from werkzeug.datastructures import FileStorage

    original = FileStorage.save
    saved = []

    def fail_second(storage, destination):
        if saved:
            raise OSError("PRIVATE UPLOAD PATH")
        original(storage, destination)
        saved.append(Path(destination))

    monkeypatch.setattr(FileStorage, "save", fail_second)
    with app.test_client() as client:
        response = _upload(client, csv_directory)
    assert response.status_code == 503
    assert len(saved) == 1 and not saved[0].exists()
    assert response.get_json()["error"]["message"] == errors.WEB_UNAVAILABLE


def _replace_many_records(directory: Path, file_name: str, count: int) -> None:
    with (directory / file_name).open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(CSV_HEADERS[file_name])
        for index in range(count):
            if file_name == "bank_deposits.csv":
                writer.writerow(("2026-10-01", "0.01", f"DEMO-{index}"))
            else:
                writer.writerow(
                    ("2026-09-01-R1", "0.01", "2026-09-01T09:00:00", f"DEMO-{index}")
                )


@pytest.mark.parametrize("file_name", ["bank_deposits.csv", "safe_drops.csv"])
@pytest.mark.parametrize("count", [1999, 2000, 2001, 20000])
def test_record_caps_before_opening_database(
    app,
    csv_directory: Path,
    monkeypatch: pytest.MonkeyPatch,
    file_name: str,
    count: int,
) -> None:
    """A small upload with too many records is rejected before any database work."""
    _replace_many_records(csv_directory, file_name, count)
    assert (
        sum((csv_directory / name).stat().st_size for name in CSV_HEADERS)
        < web.MAX_REQUEST_BYTES
    )
    opened = []
    if count > 2000:

        def forbidden(path):
            opened.append(path)
            raise RuntimeError("Database must not open for an oversized record set")

        monkeypatch.setattr(db, "connect", forbidden)
    with app.test_client() as client:
        response = _upload(client, csv_directory)
    if count <= 2000:
        assert response.status_code == 200
    else:
        assert response.status_code == 400
        assert (
            response.get_json()["error"]["message"]
            == f"{file_name} contains more than 2,000 records. Choose a smaller set of synthetic records."
        )
        assert opened == []


@pytest.mark.parametrize(
    "content, location, explanation",
    [
        (
            b"cashier_id\n",
            "the first row (column names)",
            "Missing required columns: display_name.",
        ),
        (
            b'cashier_id,display_name\ncashier_01,"Demo\n',
            "source line 2",
            "A quoted value is never closed.",
        ),
        (
            b'cashier_id,display_name\ncashier_01,"Demo"oops\n',
            "source line 2",
            "Check the quotes and commas around each value.",
        ),
        (b"cashier_id,display_name\n\xff\n", "source line 2", "Use UTF-8 encoding"),
        (
            b"cashier_id,display_name\ncashier_01," + b"x" * 131073 + b"\n",
            "source line 2",
            "A value is too long. Shorten it",
        ),
    ],
)
def test_web_csv_errors_use_plain_locations_and_explanations(
    app, csv_directory: Path, content: bytes, location: str, explanation: str
) -> None:
    (csv_directory / "cashiers.csv").write_bytes(content)
    with app.test_client() as client:
        response = _upload(client, csv_directory)
    assert response.status_code == 400
    message = response.get_json()["error"]["message"]
    assert location in message and explanation in message
    assert all(
        label not in message
        for label in (
            "<header>",
            "<row>",
            "<encoding>",
            "unexpected end of data",
            "Malformed CSV:",
        )
    )


def test_record_cap_counts_csv_records_not_physical_lines(
    app, csv_directory: Path
) -> None:
    source = csv_directory / "bank_deposits.csv"
    with source.open("w", newline="") as stream:
        stream.write("\ufeffdeposit_date,amount,reference\r\n\r\n")
        writer = csv.writer(stream, lineterminator="\r\n")
        for index in range(2000):
            writer.writerow(("2026-10-01", "0.01", f"DEMO-{index}\nsecond line"))
            stream.write("\r\n")
    with app.test_client() as client:
        assert _upload(client, csv_directory).status_code == 200


@pytest.mark.parametrize(
    "file_name,limit", [("registers.csv", 5), ("cashiers.csv", 100)]
)
@pytest.mark.parametrize("extra", [-1, 0, 1, 1000])
def test_roster_caps_before_database(
    app,
    csv_directory: Path,
    monkeypatch: pytest.MonkeyPatch,
    file_name: str,
    limit: int,
    extra: int,
) -> None:
    source = csv_directory / file_name
    with source.open(newline="") as stream:
        rows = list(csv.reader(stream))
    count = limit + extra
    rows.extend(
        [
            [f"EXTRA-{index}", f"Demo entry {index}"]
            for index in range(count - len(rows) + 1)
        ]
    )
    if count < len(rows) - 1:
        rows = rows[: count + 1]
    with source.open("w", newline="") as stream:
        csv.writer(stream, lineterminator="\n").writerows(rows)
    if count > limit:

        def forbidden(*args):
            pytest.fail("Excess roster reached the database")

        monkeypatch.setattr(db, "connect", forbidden)
    with app.test_client() as client:
        response = _upload(client, csv_directory)
    assert response.status_code == (400 if count > limit else 200)
    if count > limit:
        assert (
            response.get_json()["error"]["message"]
            == f"{file_name} contains more than {limit:,} records. Choose a smaller set of synthetic records."
        )


def _combined_workload(directory: Path, *, long_identifiers: bool = False) -> None:
    generate_demo(directory, days=500)

    def read(name):
        with (directory / name).open(newline="") as stream:
            return list(csv.reader(stream))

    def write(name, rows):
        with (directory / name).open("w", newline="") as stream:
            csv.writer(stream, lineterminator="\n").writerows(rows)

    register_ids = [
        f"R{index}" + ("-" + "&" * 253 if long_identifiers else "")
        for index in range(1, 6)
    ]
    write(
        "registers.csv",
        [CSV_HEADERS["registers.csv"]]
        + [
            [identifier, f"Demo register {index}"]
            for index, identifier in enumerate(register_ids)
        ],
    )
    rows = read("cashiers.csv")
    rows.extend(
        [
            [f"EXTRA-PERSON-{index}", f"Demo person {index}"]
            for index in range(100 - len(rows) + 1)
        ]
    )
    write("cashiers.csv", rows)
    rows = read("shifts.csv")
    columns = {name: index for index, name in enumerate(rows[0])}
    dates = {}
    for index, row in enumerate(rows[1:]):
        day = (date(2026, 9, 1) + timedelta(days=index)).isoformat()
        dates[row[columns["shift_code"]]] = day
        row[columns["business_date"]] = day
        row[columns["register_id"]] = register_ids[0]
        for field in ("opened_at", "closed_at"):
            if row[columns[field]]:
                row[columns[field]] = day + row[columns[field]][10:]
    write("shifts.csv", rows)
    rows = read("safe_drops.csv")
    for row in rows[1:]:
        row[2] = dates[row[0]] + row[2][10:]
    originals = rows[1:]
    for index in range(2000 - len(originals)):
        row = originals[index % len(originals)].copy()
        row[1], row[3] = "0.01", f"DEMO-EXTRA-{index}"
        rows.append(row)
    write("safe_drops.csv", rows)
    rows = read("cash_counts.csv")
    counted_codes = {row[0] for row in rows[1:]}
    for code in dates:
        if code not in counted_codes:
            for denomination in (
                "100.00",
                "50.00",
                "20.00",
                "10.00",
                "5.00",
                "2.00",
                "1.00",
                "0.50",
                "0.25",
                "0.10",
                "0.05",
                "0.01",
            ):
                rows.append([code, denomination, "0"])
    write("cash_counts.csv", rows)
    write(
        "bank_deposits.csv",
        [CSV_HEADERS["bank_deposits.csv"]]
        + [
            [
                (date(2026, 9, 1) + timedelta(days=index)).isoformat(),
                "0.01",
                f"DEMO-{index}",
            ]
            for index in range(2000)
        ],
    )


@pytest.mark.parametrize("long_identifiers", [False, True])
def test_combined_caps_keep_the_full_response_within_budget(
    app, tmp_path: Path, long_identifiers: bool
) -> None:
    """Budget every JSON field and embedded report together, including escaping."""
    directory = tmp_path / "combined"
    _combined_workload(directory, long_identifiers=long_identifiers)
    assert (
        sum((directory / name).stat().st_size for name in CSV_HEADERS)
        < web.MAX_REQUEST_BYTES
    )
    with app.test_client() as client:
        response = _upload(client, directory)
    assert len(response.get_data()) <= 10_000_000
    if long_identifiers:
        assert response.status_code == 400
        assert "too much detail" in response.get_json()["error"]["message"]
    else:
        assert response.status_code == 200
        payload = response.get_json()
        assert len(payload["shifts"]) == 1000
        assert len(payload["days"]) == 2000
        assert set(payload["reports"]) == {"text", "html", "csv"}


def test_overlong_values_are_rejected_before_database(
    app, csv_directory: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = csv_directory / "cashiers.csv"
    source.write_text("cashier_id,display_name\nDEMO-PERSON," + "x" * 257 + "\n")

    def forbidden(*args):
        pytest.fail("Overlong value reached the database")

    monkeypatch.setattr(db, "connect", forbidden)
    with app.test_client() as client:
        response = _upload(client, csv_directory)
    assert response.status_code == 400
    assert "256 characters" in response.get_json()["error"]["message"]


@pytest.mark.parametrize("same_day", [True, False])
def test_excessive_shift_relationships_stop_before_rule_evaluation(
    app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, same_day: bool
) -> None:
    directory = tmp_path / "overlap"
    _combined_workload(directory)
    with (directory / "shifts.csv").open(newline="") as stream:
        rows = list(csv.reader(stream))
    columns = {name: index for index, name in enumerate(rows[0])}
    for row in rows[1:]:
        row[columns["closed_at"]] = "2035-01-01T16:00:00"
        if same_day:
            row[columns["business_date"]] = "2026-09-01"
            row[columns["opened_at"]] = "2026-09-01T08:00:00"
    with (directory / "shifts.csv").open("w", newline="") as stream:
        csv.writer(stream, lineterminator="\n").writerows(rows)

    def forbidden(*args):
        raise RuntimeError("Unbounded shift relationships reached rules")

    monkeypatch.setattr("drawercheck.reconcile.evaluate_rules", forbidden)
    with app.test_client() as client:
        response = _upload(client, directory)
    assert response.status_code == 400
    assert "overlapping" in response.get_json()["error"]["message"]


@pytest.mark.parametrize("difference", [-1, 0, 1])
def test_complete_response_budget_boundary(
    app, monkeypatch: pytest.MonkeyPatch, difference: int
) -> None:
    with app.test_client() as client:
        baseline = client.post("/api/demo")
        size = len(baseline.get_data())
        monkeypatch.setattr(web, "MAX_RESPONSE_BYTES", size + difference, raising=False)
        response = client.post("/api/demo")
    assert response.status_code == (400 if difference < 0 else 200)
    if difference >= 0:
        assert len(response.get_data()) == size
    else:
        assert "too much detail" in response.get_json()["error"]["message"]


def test_large_error_also_respects_response_budget(
    app, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(web, "MAX_RESPONSE_BYTES", 1000)
    with app.test_client() as client:
        response = client.post(
            "/api/check", data={"files": (BytesIO(b"x"), "x" * 1500)}
        )
    assert response.status_code == 400
    assert len(response.get_data()) <= 1000
    assert "too much detail" in response.get_json()["error"]["message"]
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize(
    "file_name,limit", [("pos_totals.csv", 1000), ("cash_counts.csv", 12000)]
)
@pytest.mark.parametrize("extra", [1, 1000])
def test_remaining_csv_caps_before_database(
    app,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    file_name: str,
    limit: int,
    extra: int,
) -> None:
    directory = tmp_path / "natural-limits"
    _combined_workload(directory)
    source = directory / file_name
    with source.open(newline="") as stream:
        rows = list(csv.reader(stream))
    assert len(rows) - 1 == limit
    with source.open("a", newline="") as stream:
        csv.writer(stream, lineterminator="\n").writerows([rows[1]] * extra)

    def forbidden(*args):
        pytest.fail("Excess POS/count rows reached the database")

    monkeypatch.setattr(db, "connect", forbidden)
    with app.test_client() as client:
        response = _upload(client, directory)
    assert response.status_code == 400
    assert response.get_json()["error"]["limit"] == limit
