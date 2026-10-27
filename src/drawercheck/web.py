"""Optional stateless web requests using the same offline reconciliation core."""

import json
import sqlite3
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import IO

from flask import Flask, Request, Response, jsonify, render_template, request
from werkzeug.exceptions import HTTPException, NotFound

from drawercheck import errors
from drawercheck.config import Config
from drawercheck.csv_contract import CSV_HEADERS, DENOMINATIONS_CENTS
from drawercheck.demo import generate_demo
from drawercheck.importer import import_directory
from drawercheck.models import Flag, ShiftResult, group_flags_by_date
from drawercheck.money import format_cents
from drawercheck.reconcile import build_explanation, reconcile
from drawercheck.reports import (
    DailySummary,
    ReportData,
    csv_out,
    format_amount,
    html,
    load_report,
    text,
)

MAX_REQUEST_BYTES = 2 * 1024 * 1024
MAX_SHIFTS = 1000
MAX_FIELD_CHARACTERS = 256
MAX_RELATED_SHIFT_CODES = 1000
MAX_RESPONSE_BYTES = 10_000_000
ROW_LIMITS = {
    "registers.csv": 5,
    "cashiers.csv": 100,
    "shifts.csv": MAX_SHIFTS,
    "pos_totals.csv": MAX_SHIFTS,
    "cash_counts.csv": MAX_SHIFTS * len(DENOMINATIONS_CENTS),
    "bank_deposits.csv": 2000,
    "safe_drops.csv": 2000,
}
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; "
    "img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; "
    "base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)
# Public words for each code, sent once per response so every screen agrees.
RULE_LABELS = {
    "R01_VARIANCE": "Cash difference to check",
    "R02_SINGLE_DENOMINATION": "Possible single bill",
    "R03_TRANSPOSITION_HINT": "Possible swapped digits",
    "R04_REPEAT_SHORT": "Repeated shortages",
    "R05_MISSING_VERIFIER_OR_NOTE": "Missing sign-off",
    "R08_DEPOSIT": "Bank deposit to check",
    "R09_DATA_INTEGRITY": "Missing or inconsistent records",
}
SEVERITY_LABELS = {"info": "Note", "warn": "Check", "review": "Needs review"}
STATUS_LABELS = {
    "balanced": "Balanced (within {tolerance})",
    "over": "Over",
    "short": "Short",
    "incomplete": "Missing records",
    "open": "Still open",
}


@dataclass(frozen=True)
class TapeLine:
    """One drawer-tape line: its key, sign, spoken sign, label, and plain meaning."""

    key: str
    sign: str
    spoken: str
    label: str
    definition: str


# Both tapes (the Start example and Drawer details) use these words and signs.
TAPE_LINES = (
    TapeLine(
        "opening_float",
        "",
        "",
        "Opening float",
        "Cash put in the drawer at the start of the shift, so the cashier can give change.",
    ),
    TapeLine(
        "cash_sales",
        "+",
        "Plus",
        "Cash sales",
        "Sales paid in cash, as recorded by the register.",
    ),
    TapeLine(
        "paid_ins",
        "+",
        "Plus",
        "Paid-ins",
        "Cash added to the drawer that did not come from a sale.",
    ),
    TapeLine(
        "cash_refunds",
        "-",
        "Minus",
        "Cash refunds",
        "Cash given back to customers for returns.",
    ),
    TapeLine(
        "paid_outs",
        "-",
        "Minus",
        "Paid-outs",
        "Cash taken from the drawer to pay for something, such as supplies.",
    ),
    TapeLine(
        "safe_drops",
        "-",
        "Minus",
        "Safe drops",
        "Cash moved from the drawer to the safe during the shift.",
    ),
    TapeLine(
        "expected",
        "=",
        "Equals",
        "Expected cash",
        "What the drawer should hold, worked out from the lines above.",
    ),
    TapeLine(
        "counted",
        "",
        "",
        "Counted cash",
        "What was actually counted in the drawer at closing.",
    ),
    TapeLine(
        "difference",
        "",
        "",
        "Difference",
        "Counted cash minus expected cash. Below zero means the drawer is short.",
    ),
)
# The Start view's example is drawer 2026-09-03-R1; a test compares it with /api/demo.
EXAMPLE_TAPE = {
    "opening_float": "$200.00",
    "cash_sales": "$1,250.75",
    "paid_ins": "$0.00",
    "cash_refunds": "$12.00",
    "paid_outs": "$20.00",
    "safe_drops": "$900.00",
    "expected": "$518.75",
    "counted": "$498.75",
    "difference": "-$20.00",
}
FILE_DESCRIPTIONS = {
    "cashiers.csv": "Cashiers and managers, each with an ID and a name",
    "registers.csv": "The registers in the store",
    "shifts.csv": "Who worked each register, when, and the cash it started with",
    "pos_totals.csv": "Sales and other totals recorded by each register",
    "safe_drops.csv": "Cash moved from a drawer to the safe during a shift",
    "cash_counts.csv": "The closing count of each bill and coin",
    "bank_deposits.csv": "Cash deposits recorded by the bank",
}
# The page reads these from the template, so browser messages stay in errors.py.
CLIENT_MESSAGES = {
    "missing": errors.WEB_CLIENT_MISSING,
    "unknown_name": errors.WEB_CLIENT_UNKNOWN_NAME,
    "rename": errors.WEB_CLIENT_RENAME,
    "too_large": errors.WEB_CLIENT_TOO_LARGE,
    "network": errors.WEB_CLIENT_NETWORK,
    "timeout": errors.WEB_CLIENT_TIMEOUT,
    "unavailable": errors.WEB_UNAVAILABLE,
}
# The browser adds a waking-server notice after 5 seconds and stops waiting at 90.
SLOW_NOTICE_MS = 5_000
GIVE_UP_MS = 90_000


def _json_response(payload: dict) -> Response:
    # Stop encoding at the full-response budget instead of building a huge JSON string.
    encoder = json.JSONEncoder(ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    content = bytearray()
    for chunk in encoder.iterencode(payload):
        encoded = chunk.encode("utf-8")
        if len(content) + len(encoded) + 1 > MAX_RESPONSE_BYTES:
            raise errors.WebInputError(errors.WEB_RESPONSE_LIMIT)
        content.extend(encoded)
    content.extend(b"\n")
    return Response(bytes(content), mimetype="application/json")


class _UploadRequest(Request):
    # A failed multipart parse can open streams before request.files is assigned.
    def _get_file_stream(
        self,
        total_content_length: int | None,
        content_type: str | None,
        filename: str | None = None,
        content_length: int | None = None,
    ) -> IO[bytes]:
        stream = super()._get_file_stream(
            total_content_length, content_type, filename, content_length
        )
        self.__dict__.setdefault("_upload_streams", []).append(stream)
        return stream

    def close(self) -> None:
        """Close uploads even when parsing stopped before a files collection existed."""
        try:
            super().close()
        finally:
            for stream in self.__dict__.pop("_upload_streams", []):
                stream.close()


def _display_values(value: object) -> object:
    # JSON is data, not HTML. M8 must render strings as text, never as innerHTML.
    if isinstance(value, dict):
        formatted = {}
        for key, item in value.items():
            if key.endswith("_cents"):
                formatted[key.removesuffix("_cents") + "_amount"] = format_amount(item)
            else:
                formatted[key] = _display_values(item)
        return formatted
    if isinstance(value, (tuple, list)):
        return [_display_values(item) for item in value]
    return value


def _shift_data(
    result: ShiftResult,
    config: Config,
    day: DailySummary,
    daily_flags: tuple[Flag, ...],
) -> dict:
    explanation = build_explanation(
        result, config, day.expected_deposit_cents, daily_flags
    )
    values = asdict(result)
    values["shift"]["counts"] = [
        {
            "denomination": format_cents(denomination),
            "quantity": quantity,
            "line_total_amount": format_cents(denomination * quantity),
        }
        for denomination, quantity in result.shift.counts
    ]
    values.update(
        deposit_contribution_cents=explanation.deposit_contribution_cents,
        daily_deposit_cents=explanation.daily_deposit_cents,
        daily_flags=[asdict(flag) for flag in explanation.daily_flags],
        retained_float_cents=config.retained_float_per_register_cents,
        within_tolerance_cents=config.within_tolerance_cents,
        review_threshold_cents=config.review_threshold(
            result.shift.pos.cash_sales_cents
        )
        if result.shift.pos
        else None,
    )
    return _display_values(values)


def _labels(config: Config) -> dict:
    tolerance = format_cents(config.within_tolerance_cents)
    return {
        "rules": RULE_LABELS,
        "severities": SEVERITY_LABELS,
        "statuses": {
            status: label.format(tolerance=tolerance)
            for status, label in STATUS_LABELS.items()
        },
    }


def _summary(report: ReportData) -> dict:
    # Leads and drawers are counted separately; one drawer can have several leads.
    severities = Counter(flag.severity for flag in report.flags)
    return {
        "drawers_checked": len(report.shifts),
        "drawers_needing_review": sum(
            any(flag.severity == "review" for flag in result.flags)
            for result in report.shifts
        ),
        "leads_total": len(report.flags),
        "leads_by_severity": {
            severity: severities[severity] for severity in SEVERITY_LABELS
        },
        "deposit_lead_days": len(
            {
                flag.business_date
                for flag in report.flags
                if flag.rule_code == "R08_DEPOSIT"
            }
        ),
    }


def _response_data(report: ReportData) -> dict:
    days_by_date = {day.business_date: day for day in report.days}
    daily_flags_by_date = group_flags_by_date(
        tuple(flag for flag in report.flags if flag.shift_id is None)
    )
    days = []
    for day in report.days:
        values = _display_values(asdict(day))
        values["expected_deposit_amount"] = day.expected_deposit_text
        days.append(values)
    cashiers = []
    for cashier in report.cashiers:
        values = _display_values(asdict(cashier))
        if not cashier.known:
            for key in ("over_amount", "short_amount", "net_amount"):
                values[key] = "unknown"
        cashiers.append(values)
    return {
        "notice": errors.WEB_NOTICE,
        "from_date": report.from_date,
        "to_date": report.to_date,
        "generated_at": report.generated_at,
        "labels": _labels(report.config),
        "summary": _summary(report),
        "days": days,
        "cashiers": cashiers,
        "flags": [
            _display_values({**asdict(flag), "shift_code": report.shift_code(flag)})
            for flag in report.flags
        ],
        "shifts": [
            _shift_data(
                result,
                report.config,
                days_by_date[result.shift.business_date],
                daily_flags_by_date.get(result.shift.business_date, ()),
            )
            for result in report.shifts
        ],
        "reports": {
            "text": {
                "filename": "drawercheck.txt",
                "media_type": "text/plain",
                "content": text.render(report),
            },
            "html": {
                "filename": "drawercheck.html",
                "media_type": "text/html",
                "content": html.render(report),
            },
            "csv": {
                "filename": "drawercheck.csv",
                "media_type": "text/csv",
                "content": csv_out.render(report),
            },
        },
    }


def _save_uploads(directory: Path) -> None:
    if request.mimetype != "multipart/form-data":
        raise errors.WebInputError(errors.WEB_MULTIPART)
    if request.args or request.form or set(request.files) - {"files"}:
        raise errors.WebInputError(errors.WEB_FIELDS)
    uploads = request.files.getlist("files")
    selected = {}
    for upload in uploads:
        name = upload.filename
        if name not in CSV_HEADERS:
            raise errors.WebInputError(errors.WEB_FILENAME.format(name=name))
        if name in selected:
            raise errors.WebInputError(errors.WEB_DUPLICATE.format(name=name))
        selected[name] = upload
    missing = [name for name in CSV_HEADERS if name not in selected]
    if missing:
        raise errors.WebInputError(errors.WEB_MISSING.format(names=", ".join(missing)))
    # Iterate fixed server-owned names; client filenames never become paths.
    for name in CSV_HEADERS:
        selected[name].save(directory / name)


def _run_request(*, demo: bool) -> Response:
    with TemporaryDirectory(prefix="drawercheck-web-") as temporary:
        directory = Path(temporary)
        if demo:
            if request.args or request.get_data(cache=False):
                raise errors.WebInputError(errors.WEB_DEMO_BODY)
            generate_demo(directory)
        else:
            _save_uploads(directory)
        database = directory / "run.db"
        import_directory(
            directory,
            database,
            row_limits=ROW_LIMITS,
            max_field_characters=MAX_FIELD_CHARACTERS,
        )
        reconcile(database, Config(), max_related_shift_codes=MAX_RELATED_SHIFT_CODES)
        response = _json_response(_response_data(load_report(database)))
    # The response is fully buffered; no download depends on the deleted workspace.
    return response


def create_app() -> Flask:
    """Create an isolated-request app without a global database, run cache, or debug UI."""
    app = Flask(__name__)
    app.request_class = _UploadRequest
    app.config.update(
        DEBUG=False,
        MAX_CONTENT_LENGTH=MAX_REQUEST_BYTES,
        MAX_FORM_PARTS=8,
        MAX_FORM_MEMORY_SIZE=128 * 1024,
    )

    @app.get("/")
    def page() -> str:
        return render_template(
            "index.html",
            tape_lines=TAPE_LINES,
            example_tape=EXAMPLE_TAPE,
            files=FILE_DESCRIPTIONS,
            messages=CLIENT_MESSAGES,
            row_limits=ROW_LIMITS,
            max_field_characters=MAX_FIELD_CHARACTERS,
            max_upload_bytes=MAX_REQUEST_BYTES,
            slow_notice_ms=SLOW_NOTICE_MS,
            give_up_ms=GIVE_UP_MS,
        )

    @app.get("/examples/<file_name>")
    def example_file(file_name: str) -> Response:
        # The same generator as "Try the example", so downloads cannot drift from it.
        if file_name not in CSV_HEADERS:
            raise NotFound()
        with TemporaryDirectory(prefix="drawercheck-example-") as temporary:
            generate_demo(temporary)
            content = (Path(temporary) / file_name).read_bytes()
        return Response(
            content,
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
        )

    @app.post("/api/demo")
    def demo() -> Response:
        return _run_request(demo=True)

    @app.post("/api/check")
    def check() -> Response:
        return _run_request(demo=False)

    @app.after_request
    def private_response(response: Response) -> Response:
        if (
            response.content_length is not None
            and response.content_length > MAX_RESPONSE_BYTES
        ):
            response = jsonify(error={"message": errors.WEB_RESPONSE_LIMIT})
            response.status_code = 400
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.errorhandler(errors.WebInputError)
    def invalid_input(error: errors.WebInputError) -> tuple[Response, int]:
        return jsonify(error={"message": str(error)}), 400

    @app.errorhandler(errors.ImportValidationError)
    def invalid_csv(error: errors.ImportValidationError) -> tuple[Response, int]:
        return jsonify(
            error={
                "message": errors.web_import_message(error),
                "file_name": error.file_name,
                "line_number": error.line_number,
                "column": error.column,
            }
        ), 400

    @app.errorhandler(errors.ImportRowLimitError)
    def row_limit(error: errors.ImportRowLimitError) -> tuple[Response, int]:
        message = (
            errors.WEB_SHIFT_LIMIT
            if error.file_name == "shifts.csv"
            else errors.WEB_ROW_LIMIT.format(
                file_name=error.file_name, limit=error.limit
            )
        )
        return jsonify(
            error={
                "message": message,
                "file_name": error.file_name,
                "limit": error.limit,
            }
        ), 400

    @app.errorhandler(errors.CalculationLimitError)
    def detail_limit(error: errors.CalculationLimitError) -> tuple[Response, int]:
        return jsonify(error={"message": errors.WEB_DETAIL_LIMIT}), 400

    @app.errorhandler(errors.DrawerCheckError)
    def core_error(error: errors.DrawerCheckError) -> tuple[Response, int]:
        if str(error) == errors.NO_SHIFTS:
            return jsonify(error={"message": errors.WEB_EMPTY}), 400
        return jsonify(error={"message": errors.WEB_UNAVAILABLE}), 503

    @app.errorhandler(HTTPException)
    def http_error(error: HTTPException) -> Response:
        messages = {
            400: errors.WEB_BAD_REQUEST,
            404: errors.WEB_NOT_FOUND,
            405: errors.WEB_METHOD,
            413: errors.WEB_TOO_LARGE,
        }
        response = error.get_response()
        response.set_data(
            app.json.dumps(
                {"error": {"message": messages.get(error.code, errors.WEB_HTTP_ERROR)}}
            )
        )
        response.mimetype = "application/json"
        return response

    @app.errorhandler(Exception)
    def server_error(error: Exception) -> tuple[Response, int]:
        # Never log exception text, paths, or submitted records.
        if not isinstance(error, (OSError, sqlite3.DatabaseError)):
            app.logger.error("Web check failed (%s)", type(error).__name__)
        return jsonify(error={"message": errors.WEB_UNAVAILABLE}), 503

    return app
