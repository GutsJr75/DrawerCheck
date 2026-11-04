"""Verify POST /api/drawer: bounded JSON in, the shared drawer shape out, nothing kept."""

import importlib
import json
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from drawer_cases import SIGN_OFF, drawer_payload, write_case_csvs

from drawercheck import errors
from drawercheck.csv_contract import CSV_HEADERS

pytest.importorskip("flask")
web = importlib.import_module("drawercheck.web")


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    """A test client that fails if the drawer check ever opens a workspace."""

    def no_workspace(**kwargs):
        raise AssertionError("the drawer check must not create a workspace")

    monkeypatch.setattr(web, "TemporaryDirectory", no_workspace)
    app = web.create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _post(client, payload: object, **kwargs):
    return client.post("/api/drawer", json=payload, **kwargs)


def _raw(client, body: bytes, content_type: str = "application/json"):
    return client.post("/api/drawer", data=body, content_type=content_type)


def test_case_b_returns_the_shared_drawer_shape(client) -> None:
    """Python formats every amount; the browser receives nothing to calculate."""
    response = _post(client, drawer_payload("B"))
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    data = response.get_json()
    assert set(data) == {
        "notice",
        "labels",
        "drawer",
        "initial_count",
        "safe_drops",
        "coverage",
        "closing_summary",
    }
    drawer = data["drawer"]
    assert drawer["expected_amount"] == "$685.65"
    assert drawer["counted_amount"] == "$665.65"
    assert drawer["variance_amount"] == "-$20.00"
    assert drawer["status"] == "short"
    assert drawer["count_basis"] == "first_count"
    assert drawer["review_threshold_amount"] == "$13.16"
    assert drawer["shift"]["shift_code"] == "2026-11-02-R2"
    assert drawer["shift"]["pos"]["card_sales_amount"] == "unknown"
    assert drawer["shift"]["counts"][2] == {
        "denomination": "$20.00",
        "quantity": 12,
        "line_total_amount": "$240.00",
    }
    assert [lead["rule_code"] for lead in drawer["flags"]] == [
        "R01_VARIANCE",
        "R02_SINGLE_DENOMINATION",
        "R05_MISSING_VERIFIER_OR_NOTE",
    ]
    assert drawer["flags"][0]["limit_text"] == (
        "Balanced up to $1.00; Check at $5.00; Needs review at $13.16."
    )
    assert not {key for key in drawer if "deposit" in key or "daily" in key}
    assert data["safe_drops"]["total_amount"] == "$800.00"
    assert data["labels"]["dates"] == {"2026-11-02": "Monday, November 2, 2026"}
    assert data["labels"]["statuses"]["balanced"] == "Balanced (within $1.00)"
    assert data["initial_count"] is None
    assert data["closing_summary"]["filename"] == "drawercheck-closing-2026-11-02.html"
    assert data["closing_summary"]["media_type"] == "text/html"
    assert "Drawer closing sheet" in data["closing_summary"]["content"]


def test_coverage_entries_carry_labels_and_states(client) -> None:
    """Every rule appears once, in the contract's order, with its public label."""
    coverage = _post(client, drawer_payload("C")).get_json()["coverage"]
    assert [entry["rule_code"] for entry in coverage] == [
        "R01_VARIANCE",
        "R02_SINGLE_DENOMINATION",
        "R03_TRANSPOSITION_HINT",
        "R05_MISSING_VERIFIER_OR_NOTE",
        "R09_DATA_INTEGRITY",
        "R04_REPEAT_SHORT",
        "R08_DEPOSIT",
    ]
    r09 = coverage[4]
    assert r09["label"] == "Missing or inconsistent records"
    assert r09["state"] == "ran_lead" and r09["partial"] is True
    assert r09["unavailable"][0].startswith("Whether expected cash is negative")
    assert {entry["state"] for entry in coverage[:4]} == {"not_run"}
    assert coverage[5]["state"] == coverage[6]["state"] == "not_run"


@pytest.mark.parametrize("signed", [False, True])
def test_manual_and_upload_requests_agree_for_every_case(
    client, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, signed: bool
) -> None:
    """The upload path and the drawer path show the same figures and leads."""
    monkeypatch.setattr(web, "TemporaryDirectory", TemporaryDirectory)
    write_case_csvs(tmp_path, signed=signed)
    upload = client.post(
        "/api/check",
        data={
            "files": [
                (BytesIO((tmp_path / name).read_bytes()), name) for name in CSV_HEADERS
            ]
        },
        content_type="multipart/form-data",
    ).get_json()
    by_code = {shift["shift"]["shift_code"]: shift for shift in upload["shifts"]}
    for case in ("A", "B", "C"):
        changes = SIGN_OFF if signed and case == "B" else {}
        drawer = _post(client, drawer_payload(case, **changes)).get_json()["drawer"]
        uploaded = by_code[drawer["shift"]["shift_code"]]
        for key in (
            "expected_amount",
            "counted_amount",
            "variance_amount",
            "status",
            "review_threshold_amount",
            "within_tolerance_amount",
        ):
            assert drawer[key] == uploaded[key]
        assert drawer["shift"]["counts"] == uploaded["shift"]["counts"]
        assert [
            {key: value for key, value in lead.items() if key != "shift_id"}
            for lead in drawer["flags"]
        ] == [
            {key: value for key, value in lead.items() if key != "shift_id"}
            for lead in uploaded["flags"]
        ]


def test_field_problems_are_listed_together(client) -> None:
    """A 400 names each field so the page can mark it and focus the first."""
    payload = drawer_payload("A", opened_at=None, safe_drops=None)
    payload["counts"]["1.00"] = ""
    response = _post(client, payload)
    assert response.status_code == 400
    error = response.get_json()["error"]
    assert error["message"] == errors.DRAWER_FIX
    assert error["fields"] == [
        {"field": "opened_at", "message": errors.DRAWER_TIMES_UNAVAILABLE},
        {
            "field": "counts.1.00",
            "message": "Enter how many $1 bills were counted, as a whole number. Write 0 if none.",
        },
        {"field": "safe_drops", "message": errors.DRAWER_DROPS_UNAVAILABLE},
    ]


@pytest.mark.parametrize(
    ("body", "content_type", "message"),
    [
        (b"{}", "text/plain", errors.DRAWER_REQUEST),
        (b"{not json", "application/json", errors.DRAWER_REQUEST),
        (b"\xff\xfe", "application/json", errors.DRAWER_REQUEST),
        (b"[" * 16_000 + b"]" * 16_000, "application/json", errors.DRAWER_REQUEST),
        (b'{"a": 1}', "application/json", errors.DRAWER_SHAPE),
        (b"[]", "application/json", errors.DRAWER_SHAPE),
    ],
)
def test_unreadable_requests_get_one_plain_message(
    client, body: bytes, content_type: str, message: str
) -> None:
    """Wrong type, broken JSON, deep nesting, and wrong shapes have no field list."""
    response = _raw(client, body, content_type)
    assert response.status_code == 400
    assert response.get_json() == {"error": {"message": message}}


def test_json_numbers_and_repeated_keys_are_refused(client) -> None:
    """Money never becomes a float, and a repeated key cannot hide a value."""
    payload = drawer_payload("A")
    numbered = json.dumps(payload).replace('"200.00"', "200.00").encode()
    repeated = json.dumps(payload).replace(
        '"verifier_id": ""', '"verifier_id": "", "verifier_id": "manager_01"'
    )
    for body in (numbered, repeated.encode()):
        response = _raw(client, body)
        assert response.status_code == 400
        assert response.get_json()["error"]["message"] == errors.DRAWER_SHAPE


def test_url_options_and_oversized_bodies_are_refused(client) -> None:
    """The body is at most 32 KiB and the address takes no options."""
    response = client.post("/api/drawer?debug=1", json=drawer_payload("A"))
    assert response.get_json()["error"]["message"] == errors.DRAWER_REQUEST
    payload = drawer_payload("A", variance_note="x" * (33 * 1024))
    response = _post(client, payload)
    assert response.status_code == 400
    assert response.get_json()["error"]["message"] == errors.DRAWER_TOO_LARGE


def test_a_recount_returns_both_counts_from_python(client) -> None:
    """The checked drawer uses the recount; the first count keeps its own figures."""
    recount = dict(drawer_payload("B")["counts"], **{"20.00": "13"})
    data = _post(client, drawer_payload("B", recount=recount)).get_json()
    drawer, first = data["drawer"], data["initial_count"]
    assert drawer["count_basis"] == "recount"
    assert (drawer["counted_amount"], drawer["variance_amount"], drawer["status"]) == (
        "$685.65",
        "$0.00",
        "balanced",
    )
    assert drawer["shift"]["counts"][2]["line_total_amount"] == "$260.00"
    assert first == {
        "basis": "first_count, compared with the same expected cash",
        "counted_amount": "$665.65",
        "variance_amount": "-$20.00",
        "status": "short",
        "counts": first["counts"],
    }
    assert first["counts"][2] == {
        "denomination": "$20.00",
        "quantity": 12,
        "line_total_amount": "$240.00",
    }
    assert drawer["flags"] == []


def test_only_post_is_accepted(client) -> None:
    """Reading the address does not run a check."""
    assert client.get("/api/drawer").status_code == 405


def test_concurrent_requests_stay_separate(client) -> None:
    """Nothing is shared between requests, so each reply matches its own drawer."""
    payloads = [drawer_payload("A"), drawer_payload("B")] * 10

    def check(payload: dict) -> tuple[str, str]:
        drawer = _post(client, payload).get_json()["drawer"]
        return drawer["shift"]["register_id"], drawer["variance_amount"]

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check, payloads))
    assert results == [("R1", "-$0.25"), ("R2", "-$20.00")] * 10


def test_submitted_values_are_never_logged(client, caplog) -> None:
    """Accepted and rejected drawers leave no trace of their entries in the log."""
    secret = "cashier_logcheck"
    with caplog.at_level("DEBUG"):
        _post(client, drawer_payload("B", cashier_id=secret))
        _post(client, drawer_payload("B", cashier_id=secret, opening_float="x"))
    assert secret not in caplog.text
