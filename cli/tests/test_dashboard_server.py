"""Tests for the dashboard SSE server."""
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from cli.dashboard import registry, server
from cli.dashboard.reader import RunState


def test_serialize_includes_name_and_progress():
    s = RunState(
        project_path="/tmp/projX",
        phase_state="phase-3-in-progress",
        tasks_total=4,
        tasks_done=2,
        active_task="wire DI",
    )
    d = server.serialize(s)
    assert d["name"] == "projX"
    assert d["progress_pct"] == 50
    assert d["phase_state"] == "phase-3-in-progress"
    assert d["active_task"] == "wire DI"
    assert d["project_path"] == "/tmp/projX"


def test_sse_format_framing():
    assert server.sse_format('{"a":1}') == b'data: {"a":1}\n\n'


def test_snapshot_empty_registry(tmp_path):
    assert server.snapshot(tmp_path / "none.yaml") == []


def test_snapshot_non_amap_project_is_idle(tmp_path):
    reg = tmp_path / "projects.yaml"
    proj = tmp_path / "p"
    proj.mkdir()
    registry.register(reg, str(proj))
    runs = server.snapshot(reg)
    assert len(runs) == 1
    assert runs[0]["name"] == "p"
    assert runs[0]["phase_state"] is None
    assert runs[0]["tasks_total"] == 0


@pytest.fixture
def running_server(tmp_path):
    reg = tmp_path / "projects.yaml"
    proj = tmp_path / "p"
    proj.mkdir()
    registry.register(reg, str(proj))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.DashboardHandler)
    httpd.daemon_threads = True
    httpd.registry_file = reg
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()
    httpd.server_close()


def test_index_served(running_server):
    with urllib.request.urlopen(running_server + "/", timeout=5) as r:
        body = r.read().decode()
        assert r.status == 200
        assert r.headers["Cache-Control"] == "no-store"
        assert "AMAP" in body


def test_api_runs_json(running_server):
    with urllib.request.urlopen(running_server + "/api/runs", timeout=5) as r:
        assert r.status == 200
        data = json.loads(r.read())
        assert isinstance(data, list)
        assert data[0]["name"] == "p"


def test_unknown_path_404(running_server):
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(running_server + "/nope", timeout=5)
    assert exc.value.code == 404


def test_events_first_message_is_snapshot(running_server):
    req = urllib.request.urlopen(running_server + "/events", timeout=5)
    line = req.readline()  # b"data: [...]\n"
    req.close()
    assert line.startswith(b"data: ")
    payload = json.loads(line[len(b"data: "):].decode())
    assert isinstance(payload, list)
