"""Verify bounded uploads, shared results, and cleanup without an external server."""

import csv
import importlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier

import pytest

from drawercheck import db, errors
from drawercheck.cli import main
from drawercheck.csv_contract import CSV_HEADERS
from drawercheck.demo import generate_demo
from drawercheck.reconcile import explain_shift
from drawercheck.reports import csv_out, html, load_report, text

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
    assert len(payload["shifts"]) == 60 and len(payload["flags"]) == 16
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


def test_upload_preserves_bom_crlf_and_raw_bytes(
    app, csv_directory: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Web saves original bytes; the importer owns CSV and encoding handling."""
    source = csv_directory / "cashiers.csv"
    source.write_bytes(b"\xef\xbb\xbf" + source.read_bytes().replace(b"\n", b"\r\n"))
    expected = {name: (csv_directory / name).read_bytes() for name in CSV_HEADERS}
    original = web.import_directory

    def inspect(directory, database):
        assert {
            name: (directory / name).read_bytes() for name in CSV_HEADERS
        } == expected
        return original(directory, database)

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
def test_shift_limit_before_calculation(
    app, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, extra_shift: bool
) -> None:
    directory = tmp_path / "large-demo"
    generate_demo(directory, days=500)
    if extra_shift:
        with (directory / "shifts.csv").open("a") as stream:
            stream.write(
                "DEMO-EXTRA,2028-01-14,R1,cashier_01,2028-01-14T08:00:00,2028-01-14T16:00:00,200.00,,\n"
            )

        def forbidden(*args):
            pytest.fail("Oversized shift set reached reconciliation")

        monkeypatch.setattr(web, "reconcile", forbidden)
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

    def fail(*args):
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

    def together(directory, database):
        paths.append(database)
        barrier.wait()
        return original(directory, database)

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
    def fail(*args):
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
    assert len(response.get_json()["flags"]) == 16


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
