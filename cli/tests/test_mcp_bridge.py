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
