"""Exercise the deployment command over a local Unix socket, without the network."""

import json
import os
import shlex
import socket
import subprocess
import sys
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

pytest.importorskip("flask")
pytest.importorskip("gunicorn")
pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="Gunicorn needs Unix")
ROOT = Path(__file__).resolve().parents[1]


class _UnixConnection(HTTPConnection):
    def connect(self) -> None:
        """Connect through the test socket without using the network."""
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.host)


def _request(
    path: Path, method: str, url: str, *, slow: bool = False
) -> tuple[int, bytes]:
    connection = _UnixConnection(str(path), timeout=12)
    try:
        headers = {"X-Test-Slow": "yes"} if slow else {}
        connection.request(method, url, headers=headers)
        with connection.getresponse() as response:
            return response.status, response.read()
    finally:
        connection.close()


def _wait_until(check: Callable[[], bool], *, seconds: float = 6) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(0.05)
    pytest.fail("The local server did not reach the expected state in time")


def test_hosting_timeout_stops_work_cleans_up_and_recovers() -> None:
    """A stalled demo stops, leaves no workspace, and does not block another visitor."""
    # Keep the socket path short enough for both macOS and Linux.
    with TemporaryDirectory(prefix="dc-server-", dir="/tmp") as temporary:
        directory = Path(temporary)
        workspaces = directory / "workspaces"
        workspaces.mkdir()
        started = directory / "started"
        finished = directory / "finished"
        (directory / "timeout_app.py").write_text(
            "import os, time\n"
            "from pathlib import Path\n"
            "from flask import request\n"
            "from drawercheck import web\n"
            "original = web.generate_demo\n"
            "def generate(directory):\n"
            "    if request.headers.get('X-Test-Slow') == 'yes':\n"
            f"        Path({str(started)!r}).write_text(str(os.getpid()))\n"
            "        time.sleep(8)\n"
            f"        Path({str(finished)!r}).write_text('work continued')\n"
            "    return original(directory)\n"
            "web.generate_demo = generate\n"
            "app = web.create_app()\n",
            encoding="utf-8",
        )
        blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")
        start = next(
            line.split("startCommand:", 1)[1].strip()
            for line in blueprint.splitlines()
            if "startCommand:" in line
        )
        arguments = shlex.split(start)[1:-1]
        address = directory / "server.sock"
        arguments[arguments.index("--bind") + 1] = f"unix:{address}"
        # Same worker settings as deployment, with only the deadline shortened.
        arguments[arguments.index("--timeout") + 1] = "2"
        command = [
            sys.executable,
            "-m",
            "gunicorn",
            *arguments,
            "--chdir",
            temporary,
            "--graceful-timeout",
            "1",
            "--no-control-socket",
            "timeout_app:app",
        ]
        environment = dict(os.environ)
        environment.update(PYTHONPATH=str(ROOT / "src"), TMPDIR=str(workspaces))
        environment.pop("GUNICORN_CMD_ARGS", None)
        with (directory / "server.log").open("w+") as log:
            process = subprocess.Popen(command, stdout=log, stderr=log, env=environment)
            try:
                _wait_until(address.exists)

                def ready() -> bool:
                    try:
                        return _request(address, "GET", "/")[0] == 200
                    except OSError:
                        return False

                _wait_until(ready)
                with ThreadPoolExecutor(max_workers=1) as executor:
                    slow = executor.submit(
                        _request, address, "POST", "/api/demo", slow=True
                    )
                    _wait_until(started.exists)
                    status, content = _request(address, "POST", "/api/demo")
                    assert status == 200
                    assert json.loads(content)["summary"]["drawers_checked"] == 60
                    assert not slow.done(), "The other visitor must finish first"
                    status, _ = slow.result(timeout=10)
                assert status == 500, "A stalled request must not finish successfully"
                assert not finished.exists(), "The timed-out Python work must stop"
                _wait_until(lambda: not list(workspaces.iterdir()))
                assert "WORKER TIMEOUT" in (directory / "server.log").read_text()
                _wait_until(
                    lambda: (
                        (directory / "server.log")
                        .read_text()
                        .count("Booting worker with pid:")
                        >= 3
                    )
                )
                status, content = _request(address, "POST", "/api/demo")
                assert status == 200
                assert json.loads(content)["summary"]["leads_total"] == 16
                assert not list(workspaces.iterdir())
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
