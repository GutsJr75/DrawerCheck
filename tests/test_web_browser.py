"""Opt-in real-browser regression checks; the Python core needs no Node tools."""

import importlib
import os
import shutil
import subprocess
from pathlib import Path
from threading import Event, Lock, Thread

import pytest

from drawercheck.demo import generate_demo

pytest.importorskip("flask")
from flask import jsonify, request
from werkzeug.serving import make_server

web = importlib.import_module("drawercheck.web")
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("browser", ["chrome", "webkit"])
def test_file_replacement_ignores_the_old_response(
    browser: str, tmp_path: Path
) -> None:
    """Replace pending uploads through both controls, then deliver the old answer."""
    if not os.environ.get("DRAWERCHECK_PLAYWRIGHT_MODULE"):
        pytest.skip("Set DRAWERCHECK_PLAYWRIGHT_MODULE to opt in to browser checks")
    node = shutil.which("node")
    assert node, "The optional browser checks need Node.js"
    inputs = tmp_path / "inputs"
    generate_demo(inputs, days=3)
    app = web.create_app()
    gates: dict[str, dict] = {}
    lock = Lock()

    @app.after_request
    def hold_upload_response(response):
        token = request.headers.get("X-Test-Upload-Gate")
        if request.path == "/api/check" and token:
            gate = {
                "release": Event(),
                "finished": Event(),
                "status": response.status_code,
            }
            with lock:
                gates[token] = gate
            gate["release"].wait(15)
            gate["finished"].set()
        return response

    @app.route("/__test__/gate/<token>", methods=["GET", "DELETE"])
    def upload_gate(token):
        with lock:
            gate = gates.get(token)
        if gate is None:
            return jsonify(waiting=False)
        if request.method == "DELETE":
            gate["release"].set()
        return jsonify(
            waiting=True, status=gate["status"], finished=gate["finished"].is_set()
        )

    # Port zero lets the OS choose a free local port. Gate routes exist only here.
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = Thread(target=server.serve_forever)
    thread.start()
    try:
        result = subprocess.run(
            [
                node,
                str(ROOT / "tests/browser/upload_replacement.cjs"),
                f"http://127.0.0.1:{server.server_port}",
                browser,
                str(inputs),
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        print(result.stdout, end="")
    finally:
        with lock:
            for gate in gates.values():
                gate["release"].set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        assert not thread.is_alive(), "The browser test server did not stop"
