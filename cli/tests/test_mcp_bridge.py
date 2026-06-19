import importlib.util
import json
from pathlib import Path


BRIDGE = Path(__file__).resolve().parents[2] / ".amap" / "tools" / "mcp-bridge" / "mcp_client.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location("mcp_client", BRIDGE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_sse_returns_first_json_data_event():
    bridge = load_bridge()
    text = "event: message\ndata: {\"jsonrpc\":\"2.0\",\"result\":{\"ok\":true}}\n\n"
    assert bridge.parse_sse(text)["result"]["ok"] is True


def test_load_config_requires_explicit_path(tmp_path):
    bridge = load_bridge()
    path = tmp_path / "mcp_config.json"
    path.write_text(json.dumps({"mcpServers": {"demo": {"command": "python"}}}), encoding="utf-8")

    config = bridge.load_config(path, "demo")

    assert config["command"] == "python"


def test_load_config_rejects_missing_server_without_printing_config(tmp_path):
    bridge = load_bridge()
    path = tmp_path / "mcp_config.json"
    path.write_text(json.dumps({"mcpServers": {"demo": {"headers": {"Authorization": "secret"}}}}), encoding="utf-8")

    result = bridge.load_config(path, "other")

    assert result is None


def test_call_stdio_sends_initialized_notification_before_tools_list(monkeypatch):
    bridge = load_bridge()
    writes = []
    responses = iter(
        [
            '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05"}}\n',
            '{"jsonrpc":"2.0","id":2,"result":{"tools":[]}}\n',
        ]
    )

    class FakeStdin:
        def write(self, text):
            writes.append(json.loads(text))

        def flush(self):
            return None

    class FakeStdout:
        def readline(self):
            return next(responses, "")

    class FakeProcess:
        def __init__(self):
            self.stdin = FakeStdin()
            self.stdout = FakeStdout()

        def terminate(self):
            return None

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(bridge.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())

    result, error = bridge.call_stdio({"command": "python"}, "tools-list", None, {})

    assert error == ""
    assert result["result"]["tools"] == []
    assert [entry["method"] for entry in writes] == [
        "initialize",
        "notifications/initialized",
        "tools/list",
    ]
    assert "id" not in writes[1]
    assert writes[1]["params"] == {}


def test_call_stdio_returns_error_when_tools_list_response_missing(monkeypatch):
    bridge = load_bridge()
    responses = iter(['{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05"}}\n'])

    class FakeStdin:
        def write(self, text):
            return None

        def flush(self):
            return None

    class FakeStdout:
        def readline(self):
            return next(responses, "")

    class FakeProcess:
        def __init__(self):
            self.stdin = FakeStdin()
            self.stdout = FakeStdout()

        def terminate(self):
            return None

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(bridge.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())

    result, error = bridge.call_stdio({"command": "python"}, "tools-list", None, {})

    assert result is None
    assert error == "tools/list failed: no valid JSON-RPC response"


def test_discover_sse_message_endpoint_reads_endpoint_event(monkeypatch):
    bridge = load_bridge()

    class FakeResponse:
        def __init__(self, body: str):
            self._body = body.encode("utf-8")

        def read(self):
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(request, timeout=15):
        assert request.get_method() == "GET"
        assert request.full_url == "http://example.test/sse"
        return FakeResponse("event: endpoint\ndata: /messages?session_id=abc\n\n")

    monkeypatch.setattr(bridge.urllib.request, "urlopen", fake_urlopen)

    message_url = bridge.discover_sse_message_endpoint("http://example.test/sse", {})

    assert message_url == "http://example.test/messages?session_id=abc"
