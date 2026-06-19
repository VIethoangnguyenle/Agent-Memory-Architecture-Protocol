# MCP Portability + Subagent Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a cross-platform MCP doctor, controlled MCP bridge fallback, subagent evidence artifacts, and Antigravity `TargetFile` write-gate support for Codex, Claude Code, and Antigravity.

**Architecture:** Add a small `cli.mcp` package for platform adapters, config parsing, doctor status, report writing, and safe config fixes. Scaffold a standalone runtime bridge tool under `{framework_root}/tools/mcp-bridge/`, then wire AMAP rules/gates so MCP availability is evidence-based and subagent work is reviewed by the orchestrator before acceptance.

**Tech Stack:** Python 3 standard library, PyYAML, pytest, existing AMAP scaffold/manifest/Jinja pipeline, existing `gate-check` validators, Markdown runtime rules.

## Global Constraints

- Support the three primary AMAP runtimes: Codex, Claude Code, and Antigravity.
- Native MCP remains the preferred path; the bridge is diagnostic/fallback only.
- `amap init/update` may render bridge tooling but must not mutate user MCP config.
- Config edits require `amap doctor mcp --fix` plus `--yes` or explicit interactive confirmation.
- Reports must not print secrets, headers, tokens, or raw environment values.
- Subagents must not be the first actor to probe MCP.
- Orchestrator must review subagent output before accepting code.
- Existing unrelated worktree changes must not be reverted or staged.

---

## File Structure

Create:

- `cli/mcp/__init__.py` — package exports for MCP doctor internals.
- `cli/mcp/adapters.py` — platform adapter dataclasses and candidate config path logic.
- `cli/mcp/config.py` — JSON/TOML MCP config loading, selected-server matching, redaction helpers.
- `cli/mcp/doctor.py` — structured doctor status, native/bridge probe orchestration, report rendering, safe fix operations.
- `cli/commands/doctor.py` — CLI entrypoint for `amap doctor mcp`.
- `cli/tests/test_mcp_adapters.py` — adapter tests for Antigravity, Claude Code, Codex.
- `cli/tests/test_mcp_config.py` — config parser/redaction tests.
- `cli/tests/test_mcp_doctor.py` — report-only and fix-mode doctor tests.
- `cli/tests/test_mcp_bridge.py` — standalone bridge unit tests with fake transports.
- `.amap/tools/mcp-bridge/mcp_client.py` — standalone runtime bridge shipped into target projects.
- `.amap/tools/mcp-bridge/README.md` — bridge role and safety note.
- `.amap/knowledge/templates/TASK_HANDOFF.tpl.md` — subagent dispatch artifact template.
- `.amap/knowledge/templates/CONTEXT_REQUEST.tpl.md` — subagent context request template.
- `.amap/knowledge/templates/NODE_CHECKPOINT.tpl.md` — subagent output checkpoint template.

Modify:

- `cli/amap.py` — add `amap doctor mcp` subcommand.
- `cli/plugin-manifest.yaml` — add `mcp-bridge` tool plugin.
- `cli/tests/test_init.py` — assert `amap init` scaffolds bridge tooling and only prints doctor hint when MCPs are selected.
- `cli/tests/test_scaffold.py` — assert manifest declares bridge plugin.
- `cli/tests/test_snapshots.py` plus snapshot files — include `tools/mcp-bridge` files.
- `.amap/tools/gate-check/gates.py` — add context-request and node-checkpoint validators; optionally accept bridge fallback MCP evidence.
- `.amap/tools/gate-check/cli.py` — expose new validator names.
- `.amap/tools/gate-check/tests/test_gates.py` — tests for new validators and bridge MCP status.
- `.amap/procedures/bootstrap.md` — point MCP probe failure to `amap doctor mcp` and bridge fallback evidence.
- `.amap/rules/rules-tool.md` — encode bridge fallback and orchestrator-owned subagent evidence loop.
- `.amap/hooks/write-gate/write_gate.py` — parse `TargetFile`.
- `.amap/hooks/write-gate/tests/test_write_gate.py` — regression test for `TargetFile`.
- `README.md` — short MCP doctor usage note.

---

### Task 1: Platform MCP Adapter Contract

**Files:**
- Create: `cli/mcp/__init__.py`
- Create: `cli/mcp/adapters.py`
- Test: `cli/tests/test_mcp_adapters.py`

**Interfaces:**
- Produces: `McpConfigCandidate(path: Path, scope: str, format: str)`
- Produces: `McpPlatformAdapter(platform: str, framework_root: str, config_candidates(project_root: Path, home: Path) -> list[McpConfigCandidate])`
- Produces: `get_mcp_adapter(platform: str) -> McpPlatformAdapter`
- Consumes: platform keys from `resolved-config.yaml`: `antigravity`, `claude-code`, `codex`, `generic`

- [ ] **Step 1: Write failing adapter tests**

Create `cli/tests/test_mcp_adapters.py`:

```python
from pathlib import Path

import pytest

from cli.mcp.adapters import get_mcp_adapter


def test_antigravity_adapter_lists_workspace_cli_ide_and_shared_paths(tmp_path):
    project = tmp_path / "proj"
    home = tmp_path / "home"
    adapter = get_mcp_adapter("antigravity")

    candidates = adapter.config_candidates(project, home)
    paths = [item.path for item in candidates]

    assert adapter.framework_root == ".agents"
    assert project / ".agents" / "mcp_config.json" in paths
    assert home / ".gemini" / "antigravity-cli" / "mcp_config.json" in paths
    assert home / ".gemini" / "antigravity" / "mcp_config.json" in paths
    assert home / ".gemini" / "config" / "mcp_config.json" in paths


def test_claude_adapter_lists_project_mcp_json_first(tmp_path):
    project = tmp_path / "proj"
    home = tmp_path / "home"
    adapter = get_mcp_adapter("claude-code")

    candidates = adapter.config_candidates(project, home)

    assert adapter.framework_root == ".claude"
    assert candidates[0].path == project / ".mcp.json"
    assert candidates[0].format == "json"


def test_codex_adapter_lists_project_config_toml_first(tmp_path):
    project = tmp_path / "proj"
    home = tmp_path / "home"
    adapter = get_mcp_adapter("codex")

    candidates = adapter.config_candidates(project, home)

    assert adapter.framework_root == ".agents"
    assert candidates[0].path == project / ".codex" / "config.toml"
    assert candidates[0].format == "toml"


def test_generic_adapter_has_no_native_candidates(tmp_path):
    adapter = get_mcp_adapter("generic")
    assert adapter.framework_root == ".amap"
    assert adapter.config_candidates(tmp_path / "proj", tmp_path / "home") == []


def test_unknown_adapter_fails_clearly():
    with pytest.raises(ValueError) as exc:
        get_mcp_adapter("unknown")

    assert "Unknown MCP platform adapter" in str(exc.value)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest cli/tests/test_mcp_adapters.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'cli.mcp'`.

- [ ] **Step 3: Add adapter package**

Create `cli/mcp/__init__.py`:

```python
"""MCP diagnostics and bridge support for AMAP."""
```

Create `cli/mcp/adapters.py`:

```python
"""Platform-specific MCP config discovery for AMAP doctor."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class McpConfigCandidate:
    path: Path
    scope: str
    format: str


@dataclass(frozen=True)
class McpPlatformAdapter:
    platform: str
    framework_root: str
    candidates: tuple[tuple[str, str, str], ...]

    def config_candidates(self, project_root: Path, home: Path) -> list[McpConfigCandidate]:
        values: list[McpConfigCandidate] = []
        for scope, raw_path, fmt in self.candidates:
            if raw_path.startswith("~/"):
                path = home / raw_path.removeprefix("~/")
            else:
                path = project_root / raw_path
            values.append(McpConfigCandidate(path=path, scope=scope, format=fmt))
        return values


_ADAPTERS = {
    "antigravity": McpPlatformAdapter(
        platform="antigravity",
        framework_root=".agents",
        candidates=(
            ("workspace", ".agents/mcp_config.json", "json"),
            ("cli", "~/.gemini/antigravity-cli/mcp_config.json", "json"),
            ("ide", "~/.gemini/antigravity/mcp_config.json", "json"),
            ("shared", "~/.gemini/config/mcp_config.json", "json"),
        ),
    ),
    "claude-code": McpPlatformAdapter(
        platform="claude-code",
        framework_root=".claude",
        candidates=(
            ("workspace", ".mcp.json", "json"),
            ("user", "~/.claude/mcp_config.json", "json"),
        ),
    ),
    "codex": McpPlatformAdapter(
        platform="codex",
        framework_root=".agents",
        candidates=(
            ("workspace", ".codex/config.toml", "toml"),
            ("user", "~/.codex/config.toml", "toml"),
        ),
    ),
    "generic": McpPlatformAdapter(
        platform="generic",
        framework_root=".amap",
        candidates=(),
    ),
}


def get_mcp_adapter(platform: str) -> McpPlatformAdapter:
    try:
        return _ADAPTERS[platform]
    except KeyError as exc:
        raise ValueError(f"Unknown MCP platform adapter: {platform}") from exc
```

- [ ] **Step 4: Run tests to verify adapter contract passes**

Run: `pytest cli/tests/test_mcp_adapters.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cli/mcp/__init__.py cli/mcp/adapters.py cli/tests/test_mcp_adapters.py
git commit -m "feat: add platform mcp adapter contract"
```

---

### Task 2: MCP Config Parsing And Redaction

**Files:**
- Create: `cli/mcp/config.py`
- Test: `cli/tests/test_mcp_config.py`

**Interfaces:**
- Consumes: `McpConfigCandidate` from Task 1
- Produces: `LoadedMcpConfig(path: Path, format: str, exists: bool, valid: bool, servers: dict, error: str = "")`
- Produces: `load_mcp_config(candidate: McpConfigCandidate) -> LoadedMcpConfig`
- Produces: `server_names(config: LoadedMcpConfig) -> list[str]`
- Produces: `selected_server_matches(config: LoadedMcpConfig, selected: list[str]) -> tuple[list[str], list[str]]`
- Produces: `redact_mapping(value: dict) -> dict`

- [ ] **Step 1: Write failing config tests**

Create `cli/tests/test_mcp_config.py`:

```python
import json

from cli.mcp.adapters import McpConfigCandidate
from cli.mcp.config import load_mcp_config, redact_mapping, selected_server_matches, server_names


def test_load_json_mcp_servers(tmp_path):
    path = tmp_path / "mcp_config.json"
    path.write_text(
        json.dumps({"mcpServers": {"socraticode": {"command": "npx", "args": ["x"]}}}),
        encoding="utf-8",
    )
    config = load_mcp_config(McpConfigCandidate(path, "workspace", "json"))

    assert config.exists is True
    assert config.valid is True
    assert server_names(config) == ["socraticode"]


def test_load_codex_toml_mcp_servers(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        '[mcp_servers.socraticode]\ncommand = "npx"\nargs = ["socraticode"]\n',
        encoding="utf-8",
    )
    config = load_mcp_config(McpConfigCandidate(path, "workspace", "toml"))

    assert config.valid is True
    assert server_names(config) == ["socraticode"]


def test_missing_and_empty_configs_are_not_valid(tmp_path):
    missing = load_mcp_config(McpConfigCandidate(tmp_path / "missing.json", "x", "json"))
    assert missing.exists is False
    assert missing.valid is False

    empty_path = tmp_path / "empty.json"
    empty_path.write_text("", encoding="utf-8")
    empty = load_mcp_config(McpConfigCandidate(empty_path, "x", "json"))
    assert empty.exists is True
    assert empty.valid is False
    assert "empty" in empty.error


def test_selected_server_matches_returns_present_and_missing(tmp_path):
    path = tmp_path / "mcp_config.json"
    path.write_text(json.dumps({"mcpServers": {"db-remote": {}, "agent-memory": {}}}), encoding="utf-8")
    config = load_mcp_config(McpConfigCandidate(path, "workspace", "json"))

    present, missing = selected_server_matches(config, ["db-remote", "socraticode"])

    assert present == ["db-remote"]
    assert missing == ["socraticode"]


def test_redact_mapping_hides_secrets_recursively():
    value = {
        "headers": {"Authorization": "Bearer abc", "X-Plain": "ok"},
        "env": {"TOKEN": "secret", "NORMAL": "value"},
        "nested": [{"api_key": "123"}],
    }

    redacted = redact_mapping(value)

    assert redacted["headers"]["Authorization"] == "<redacted>"
    assert redacted["headers"]["X-Plain"] == "ok"
    assert redacted["env"]["TOKEN"] == "<redacted>"
    assert redacted["env"]["NORMAL"] == "value"
    assert redacted["nested"][0]["api_key"] == "<redacted>"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest cli/tests/test_mcp_config.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'cli.mcp.config'`.

- [ ] **Step 3: Implement config parsing**

Create `cli/mcp/config.py`:

```python
"""MCP config loading and redaction helpers."""

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cli.mcp.adapters import McpConfigCandidate


_SECRET_KEYS = ("authorization", "token", "secret", "password", "api_key", "apikey", "key")


@dataclass(frozen=True)
class LoadedMcpConfig:
    path: Path
    scope: str
    format: str
    exists: bool
    valid: bool
    servers: dict[str, dict[str, Any]]
    error: str = ""


def _extract_servers(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if "mcpServers" in data and isinstance(data["mcpServers"], dict):
        return data["mcpServers"]
    if "mcp_servers" in data and isinstance(data["mcp_servers"], dict):
        return data["mcp_servers"]
    return {}


def load_mcp_config(candidate: McpConfigCandidate) -> LoadedMcpConfig:
    if not candidate.path.exists():
        return LoadedMcpConfig(candidate.path, candidate.scope, candidate.format, False, False, {}, "missing")
    raw = candidate.path.read_text(encoding="utf-8")
    if not raw.strip():
        return LoadedMcpConfig(candidate.path, candidate.scope, candidate.format, True, False, {}, "empty config")
    try:
        if candidate.format == "json":
            data = json.loads(raw)
        elif candidate.format == "toml":
            data = tomllib.loads(raw)
        else:
            return LoadedMcpConfig(candidate.path, candidate.scope, candidate.format, True, False, {}, "unsupported format")
    except (json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        return LoadedMcpConfig(candidate.path, candidate.scope, candidate.format, True, False, {}, str(exc))
    if not isinstance(data, dict):
        return LoadedMcpConfig(candidate.path, candidate.scope, candidate.format, True, False, {}, "config root is not an object")
    servers = _extract_servers(data)
    if not servers:
        return LoadedMcpConfig(candidate.path, candidate.scope, candidate.format, True, False, {}, "missing mcpServers")
    return LoadedMcpConfig(candidate.path, candidate.scope, candidate.format, True, True, servers)


def server_names(config: LoadedMcpConfig) -> list[str]:
    return sorted(config.servers)


def selected_server_matches(config: LoadedMcpConfig, selected: list[str]) -> tuple[list[str], list[str]]:
    names = set(server_names(config))
    present = [name for name in selected if name in names]
    missing = [name for name in selected if name not in names]
    return present, missing


def redact_mapping(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(secret in key_text for secret in _SECRET_KEYS):
                redacted[key] = "<redacted>"
            else:
                redacted[key] = redact_mapping(item)
        return redacted
    if isinstance(value, list):
        return [redact_mapping(item) for item in value]
    return value
```

- [ ] **Step 4: Run config tests**

Run: `pytest cli/tests/test_mcp_config.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cli/mcp/config.py cli/tests/test_mcp_config.py
git commit -m "feat: load and redact mcp configs"
```

---

### Task 3: Standalone MCP Bridge Tool

**Files:**
- Create: `.amap/tools/mcp-bridge/mcp_client.py`
- Create: `.amap/tools/mcp-bridge/README.md`
- Test: `cli/tests/test_mcp_bridge.py`

**Interfaces:**
- Produces runtime command: `python3 {framework_root}/tools/mcp-bridge/mcp_client.py --config PATH --server SERVER tools-list`
- Produces runtime command: `python3 {framework_root}/tools/mcp-bridge/mcp_client.py --config PATH --server SERVER call TOOL --arguments JSON`
- Produces JSON fields: `ok`, `server`, `operation`, `result`, `error`

- [ ] **Step 1: Write failing bridge tests**

Create `cli/tests/test_mcp_bridge.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest cli/tests/test_mcp_bridge.py -v`

Expected: FAIL with `FileNotFoundError` for `.amap/tools/mcp-bridge/mcp_client.py`.

- [ ] **Step 3: Implement bridge tool**

Create `.amap/tools/mcp-bridge/mcp_client.py`:

```python
#!/usr/bin/env python3
"""Controlled MCP bridge for AMAP diagnostics and fallback use."""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


PROTOCOL_VERSION = "2024-11-05"


def parse_sse(response_text: str):
    for line in response_text.splitlines():
        if line.startswith("data: "):
            try:
                return json.loads(line[6:])
            except json.JSONDecodeError:
                return None
    return None


def emit(ok: bool, server: str, operation: str, result=None, error: str = "") -> int:
    print(json.dumps({
        "ok": ok,
        "server": server,
        "operation": operation,
        "result": result,
        "error": error,
    }, ensure_ascii=False))
    return 0 if ok else 1


def load_config(config_path: Path, server: str):
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    servers = data.get("mcpServers") or data.get("mcp_servers") or {}
    selected = servers.get(server)
    return selected if isinstance(selected, dict) else None


def request_payload(method: str, params: dict, req_id: int) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}) + "\n"


def initialize_params() -> dict:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {},
        "clientInfo": {"name": "amap-mcp-bridge", "version": "1.0.0"},
    }


def call_stdio(config: dict, operation: str, tool_name: str | None, arguments: dict):
    command = config.get("command")
    if not command:
        return None, "stdio server has no command"
    args = config.get("args") or []
    env = os.environ.copy()
    env.update(config.get("env") or {})
    proc = subprocess.Popen(
        [command, *args],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    def send(method: str, params: dict, req_id: int):
        proc.stdin.write(request_payload(method, params, req_id))
        proc.stdin.flush()
        while True:
            line = proc.stdout.readline()
            if not line:
                return None
            if "jsonrpc" not in line:
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue

    try:
        init = send("initialize", initialize_params(), 1)
        if not init:
            return None, "initialize failed"
        if operation == "tools-list":
            return send("tools/list", {}, 2), ""
        return send("tools/call", {"name": tool_name, "arguments": arguments}, 2), ""
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            proc.kill()


def call_http(config: dict, operation: str, tool_name: str | None, arguments: dict):
    url = config.get("serverUrl") or config.get("url")
    if not url:
        return None, "http server has no serverUrl"
    if not url.endswith("/mcp"):
        url = url.rstrip("/") + "/mcp"
    headers = dict(config.get("headers") or {})
    headers.update({"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})

    def post(method: str, params: dict, session_id: str | None = None):
        req_headers = dict(headers)
        if session_id:
            req_headers["mcp-session-id"] = session_id
        req = urllib.request.Request(
            url,
            data=request_payload(method, params, 1).encode("utf-8"),
            headers=req_headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return parse_sse(body) or json.loads(body), resp.headers.get("mcp-session-id")

    try:
        _, session = post("initialize", initialize_params())
        if operation == "tools-list":
            result, _ = post("tools/list", {}, session)
        else:
            result, _ = post("tools/call", {"name": tool_name, "arguments": arguments}, session)
        return result, ""
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, str(exc)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--server", required=True)
    sub = parser.add_subparsers(dest="operation", required=True)
    sub.add_parser("tools-list")
    call = sub.add_parser("call")
    call.add_argument("tool")
    call.add_argument("--arguments", default="{}")
    args = parser.parse_args(argv)

    config = load_config(Path(args.config), args.server)
    if config is None:
        return emit(False, args.server, args.operation, error="server not found or config invalid")
    try:
        arguments = json.loads(getattr(args, "arguments", "{}"))
    except json.JSONDecodeError as exc:
        return emit(False, args.server, args.operation, error=f"invalid arguments JSON: {exc}")

    if "command" in config:
        result, error = call_stdio(config, args.operation, getattr(args, "tool", None), arguments)
    else:
        result, error = call_http(config, args.operation, getattr(args, "tool", None), arguments)
    return emit(error == "", args.server, args.operation, result=result, error=error)


if __name__ == "__main__":
    sys.exit(main())
```

Create `.amap/tools/mcp-bridge/README.md`:

```markdown
# MCP Bridge

This tool is an AMAP diagnostic and fallback client for MCP servers.

Use native MCP tools when the runtime exposes them. Use this bridge only when
`amap doctor mcp` reports that native MCP is unavailable and records bridge
fallback evidence.

The bridge requires an explicit config path and server name. It does not scan
home-directory config locations by itself.
```

- [ ] **Step 4: Run bridge tests**

Run: `pytest cli/tests/test_mcp_bridge.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/tools/mcp-bridge cli/tests/test_mcp_bridge.py
git commit -m "feat: add controlled mcp bridge tool"
```

---

### Task 4: MCP Doctor Report-Only Mode

**Files:**
- Create: `cli/mcp/doctor.py`
- Create: `cli/commands/doctor.py`
- Modify: `cli/amap.py`
- Test: `cli/tests/test_mcp_doctor.py`

**Interfaces:**
- Consumes: `load_resolved_config(target: Path) -> dict | None`
- Produces: `run_doctor_mcp(target_dir: str, fix: bool = False, assume_yes: bool = False, home: Path | None = None) -> None`
- Produces: `build_doctor_status(target: Path, home: Path) -> DoctorStatus`
- Produces report path: `{framework_root}/knowledge/active/mcp-doctor-report.md`

- [ ] **Step 1: Write failing doctor tests**

Create `cli/tests/test_mcp_doctor.py`:

```python
import json

import yaml

from cli.commands.doctor import run_doctor_mcp


def write_resolved(target, platform="antigravity", mcps=None):
    root = ".agents" if platform in ("antigravity", "codex") else ".claude"
    path = target / root / "resolved-config.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(
        yaml.dump({"resolved": {
            "platform": platform,
            "framework_root": root,
            "mcps": mcps or ["socraticode"],
            "language": "python",
        }}),
        encoding="utf-8",
    )
    return path


def test_doctor_writes_report_for_missing_native_config(tmp_path):
    target = tmp_path / "proj"
    home = tmp_path / "home"
    write_resolved(target)

    run_doctor_mcp(str(target), fix=False, assume_yes=False, home=home)

    report = target / ".agents" / "knowledge" / "active" / "mcp-doctor-report.md"
    text = report.read_text(encoding="utf-8")
    assert "Platform: antigravity" in text
    assert "socraticode" in text
    assert "native: unavailable" in text


def test_doctor_matches_selected_server_in_existing_config(tmp_path):
    target = tmp_path / "proj"
    home = tmp_path / "home"
    write_resolved(target, mcps=["socraticode", "db-remote"])
    cfg = target / ".agents" / "mcp_config.json"
    cfg.write_text(json.dumps({"mcpServers": {"socraticode": {"command": "npx"}}}), encoding="utf-8")

    run_doctor_mcp(str(target), fix=False, assume_yes=False, home=home)

    text = (target / ".agents" / "knowledge" / "active" / "mcp-doctor-report.md").read_text(encoding="utf-8")
    assert "matched: socraticode" in text
    assert "missing: db-remote" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest cli/tests/test_mcp_doctor.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'cli.commands.doctor'`.

- [ ] **Step 3: Implement doctor internals**

Create `cli/mcp/doctor.py`:

```python
"""MCP doctor status and report generation."""

from dataclasses import dataclass
from pathlib import Path

from cli.mcp.adapters import get_mcp_adapter
from cli.mcp.config import load_mcp_config, selected_server_matches, server_names
from cli.scaffold import load_resolved_config


@dataclass(frozen=True)
class DoctorStatus:
    platform: str
    framework_root: str
    selected_mcps: list[str]
    config_path: Path | None
    native_state: str
    matched: list[str]
    missing: list[str]
    bridge_state: str
    recommendation: str


def build_doctor_status(target: Path, home: Path) -> DoctorStatus:
    resolved = load_resolved_config(target)
    if resolved is None:
        raise ValueError(f"No AMAP resolved-config.yaml found under {target}")
    platform = resolved.get("platform", "generic")
    framework_root = resolved.get("framework_root", get_mcp_adapter(platform).framework_root)
    selected = list(resolved.get("mcps") or [])
    adapter = get_mcp_adapter(platform)

    best_config = None
    for candidate in adapter.config_candidates(target, home):
        config = load_mcp_config(candidate)
        if config.valid:
            best_config = config
            break

    if best_config is None:
        return DoctorStatus(
            platform=platform,
            framework_root=framework_root,
            selected_mcps=selected,
            config_path=None,
            native_state="unavailable",
            matched=[],
            missing=selected,
            bridge_state="unavailable",
            recommendation="create or link a valid MCP config with amap doctor mcp --fix",
        )

    matched, missing = selected_server_matches(best_config, selected)
    native_state = "configured" if matched else "unavailable"
    bridge_state = "probe-not-run" if matched else "unavailable"
    return DoctorStatus(
        platform=platform,
        framework_root=framework_root,
        selected_mcps=selected,
        config_path=best_config.path,
        native_state=native_state,
        matched=matched,
        missing=missing,
        bridge_state=bridge_state,
        recommendation="run native MCP in the IDE/CLI and inspect tool availability",
    )


def render_report(status: DoctorStatus) -> str:
    config_path = status.config_path.as_posix() if status.config_path else "none"
    matched = ", ".join(status.matched) if status.matched else "none"
    missing = ", ".join(status.missing) if status.missing else "none"
    selected = ", ".join(status.selected_mcps) if status.selected_mcps else "none"
    return (
        "# MCP Doctor Report\n\n"
        f"- Platform: {status.platform}\n"
        f"- Framework root: {status.framework_root}\n"
        f"- Selected MCPs: {selected}\n"
        f"- Config path: {config_path}\n"
        f"- native: {status.native_state}\n"
        f"- bridge: {status.bridge_state}\n"
        f"- matched: {matched}\n"
        f"- missing: {missing}\n"
        f"- Recommendation: {status.recommendation}\n"
    )


def write_report(target: Path, status: DoctorStatus) -> Path:
    report = target / status.framework_root / "knowledge" / "active" / "mcp-doctor-report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(status), encoding="utf-8")
    return report
```

Create `cli/commands/doctor.py`:

```python
"""amap doctor — diagnostics for AMAP runtime dependencies."""

from pathlib import Path
from typing import Optional

from cli.mcp.doctor import build_doctor_status, write_report


def run_doctor_mcp(
    target_dir: str,
    fix: bool = False,
    assume_yes: bool = False,
    home: Optional[Path] = None,
) -> None:
    target = Path(target_dir).resolve()
    home_path = home or Path.home()
    status = build_doctor_status(target, home_path)
    report = write_report(target, status)
    print(f"\n  MCP doctor report: {report}")
    print(f"  native: {status.native_state} | bridge: {status.bridge_state}")
    if fix:
        print("  --fix requested, but fix operations are added in the next task.")
```

Modify `cli/amap.py`:

```python
    # ─── doctor ───
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Run AMAP diagnostics",
    )
    doctor_subparsers = doctor_parser.add_subparsers(dest="doctor_command")
    mcp_parser = doctor_subparsers.add_parser(
        "mcp",
        help="Diagnose MCP config and runtime availability",
    )
    mcp_parser.add_argument("--target", default=".")
    mcp_parser.add_argument("--fix", action="store_true")
    mcp_parser.add_argument("--yes", action="store_true")
```

Add dispatch before the final `else`:

```python
    elif args.command == "doctor" and args.doctor_command == "mcp":
        from cli.commands.doctor import run_doctor_mcp
        run_doctor_mcp(target_dir=args.target, fix=args.fix, assume_yes=args.yes)
```

- [ ] **Step 4: Run doctor tests**

Run: `pytest cli/tests/test_mcp_doctor.py -v`

Expected: PASS.

- [ ] **Step 5: Run CLI smoke help**

Run: `python -m cli.amap doctor mcp --help`

Expected: output includes `Diagnose MCP config and runtime availability`.

- [ ] **Step 6: Commit**

```bash
git add cli/mcp/doctor.py cli/commands/doctor.py cli/amap.py cli/tests/test_mcp_doctor.py
git commit -m "feat: add mcp doctor report mode"
```

---

### Task 5: Safe MCP Doctor Fix Mode

**Files:**
- Modify: `cli/mcp/doctor.py`
- Modify: `cli/commands/doctor.py`
- Test: `cli/tests/test_mcp_doctor.py`

**Interfaces:**
- Consumes: `DoctorStatus` from Task 4
- Produces: `apply_fix(target: Path, home: Path, assume_yes: bool) -> Path | None`
- Produces: backup file beside overwritten config with suffix `.bak`

- [ ] **Step 1: Add failing fix-mode tests**

Append to `cli/tests/test_mcp_doctor.py`:

```python
def test_doctor_fix_copies_known_good_antigravity_ide_config(tmp_path):
    target = tmp_path / "proj"
    home = tmp_path / "home"
    write_resolved(target, platform="antigravity", mcps=["socraticode"])
    source = home / ".gemini" / "antigravity" / "mcp_config.json"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps({"mcpServers": {"socraticode": {"command": "npx"}}}), encoding="utf-8")

    run_doctor_mcp(str(target), fix=True, assume_yes=True, home=home)

    dest = home / ".gemini" / "antigravity-cli" / "mcp_config.json"
    assert dest.exists()
    assert json.loads(dest.read_text(encoding="utf-8"))["mcpServers"]["socraticode"]["command"] == "npx"


def test_doctor_fix_backs_up_existing_non_empty_destination(tmp_path):
    target = tmp_path / "proj"
    home = tmp_path / "home"
    write_resolved(target, platform="antigravity", mcps=["socraticode"])
    source = home / ".gemini" / "antigravity" / "mcp_config.json"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps({"mcpServers": {"socraticode": {"command": "npx"}}}), encoding="utf-8")
    dest = home / ".gemini" / "antigravity-cli" / "mcp_config.json"
    dest.parent.mkdir(parents=True)
    dest.write_text(json.dumps({"mcpServers": {"old": {"command": "old"}}}), encoding="utf-8")

    run_doctor_mcp(str(target), fix=True, assume_yes=True, home=home)

    assert (dest.parent / "mcp_config.json.bak").exists()
    assert "old" in (dest.parent / "mcp_config.json.bak").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run fix tests to verify they fail**

Run: `pytest cli/tests/test_mcp_doctor.py::test_doctor_fix_copies_known_good_antigravity_ide_config cli/tests/test_mcp_doctor.py::test_doctor_fix_backs_up_existing_non_empty_destination -v`

Expected: FAIL because `--fix` only prints a message.

- [ ] **Step 3: Implement safe fix**

In `cli/mcp/doctor.py`, add:

```python
import shutil
```

Add this function:

```python
def apply_fix(target: Path, home: Path, assume_yes: bool) -> Path | None:
    resolved = load_resolved_config(target)
    if resolved is None:
        raise ValueError(f"No AMAP resolved-config.yaml found under {target}")
    platform = resolved.get("platform", "generic")
    if platform != "antigravity":
        return None
    adapter = get_mcp_adapter(platform)
    candidates = adapter.config_candidates(target, home)
    destination = next(item.path for item in candidates if item.scope == "cli")
    source = None
    for candidate in candidates:
        if candidate.scope == "cli":
            continue
        config = load_mcp_config(candidate)
        if config.valid:
            source = config.path
            break
    if source is None:
        return None
    if not assume_yes:
        answer = input(f"Copy {source} to {destination}? [y/N]: ").strip().lower()
        if answer != "y":
            return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.read_text(encoding="utf-8").strip():
        backup = destination.with_name(destination.name + ".bak")
        shutil.copy2(destination, backup)
    shutil.copy2(source, destination)
    return destination
```

Modify `cli/commands/doctor.py`:

```python
from cli.mcp.doctor import apply_fix, build_doctor_status, write_report
```

Inside `run_doctor_mcp`, replace the `--fix` message:

```python
    if fix:
        fixed = apply_fix(target, home_path, assume_yes)
        if fixed is None:
            print("  no safe automatic fix available")
        else:
            print(f"  fixed config: {fixed}")
            status = build_doctor_status(target, home_path)
            report = write_report(target, status)
            print(f"  refreshed report: {report}")
```

- [ ] **Step 4: Run doctor tests**

Run: `pytest cli/tests/test_mcp_doctor.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add cli/mcp/doctor.py cli/commands/doctor.py cli/tests/test_mcp_doctor.py
git commit -m "feat: add safe mcp doctor fix mode"
```

---

### Task 6: Scaffold MCP Bridge And Init Hint

**Files:**
- Modify: `cli/plugin-manifest.yaml`
- Modify: `cli/commands/init.py`
- Modify: `cli/tests/test_scaffold.py`
- Modify: `cli/tests/test_init.py`
- Modify: `cli/tests/test_snapshots.py`
- Modify: `cli/tests/snapshots/antigravity.txt`
- Modify: `cli/tests/snapshots/claude-code.txt`
- Modify: `cli/tests/snapshots/codex.txt`
- Modify: `cli/tests/snapshots/generic.txt`

**Interfaces:**
- Consumes: `.amap/tools/mcp-bridge/` from Task 3
- Produces scaffolded `{framework_root}/tools/mcp-bridge/mcp_client.py`
- Produces init output line: `Run MCP diagnostics: amap doctor mcp --target <target>`

- [ ] **Step 1: Add failing scaffold and init tests**

Append to `cli/tests/test_scaffold.py`:

```python
def test_manifest_declares_mcp_bridge_plugin(amap_root):
    manifest = load_manifest(amap_root)
    by_name = {p["name"]: p for p in manifest["plugins"]}
    assert by_name["mcp-bridge"]["type"] == "tool"
    assert by_name["mcp-bridge"]["source"] == "tools/mcp-bridge/"
    assert by_name["mcp-bridge"]["copy_dir"] is True
```

Append to `cli/tests/test_init.py`:

```python
def test_init_scaffolds_mcp_bridge_when_platform_supports_tools(tmp_path, amap_root):
    target = tmp_path / "proj"
    run_init(
        target_dir=str(target),
        amap_root=str(amap_root),
        platform_key="antigravity",
        selected_mcps=["socraticode"],
        language="python",
        assume_yes=True,
    )

    assert (target / ".agents" / "tools" / "mcp-bridge" / "mcp_client.py").exists()


def test_init_prints_mcp_doctor_hint_when_mcps_selected(tmp_path, amap_root, capsys):
    target = tmp_path / "proj"
    run_init(
        target_dir=str(target),
        amap_root=str(amap_root),
        platform_key="codex",
        selected_mcps=["socraticode"],
        language="python",
        assume_yes=True,
    )

    captured = capsys.readouterr()
    assert "amap doctor mcp --target" in captured.out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest cli/tests/test_scaffold.py::test_manifest_declares_mcp_bridge_plugin cli/tests/test_init.py::test_init_scaffolds_mcp_bridge_when_platform_supports_tools cli/tests/test_init.py::test_init_prints_mcp_doctor_hint_when_mcps_selected -v`

Expected: FAIL because the manifest lacks `mcp-bridge` and init lacks the hint.

- [ ] **Step 3: Add manifest plugin**

In `cli/plugin-manifest.yaml`, add after `gate-check` or near other tool plugins:

```yaml
  - name: mcp-bridge
    type: tool
    source: tools/mcp-bridge/
    template: false
    output: "{{ platform.framework_root }}/tools/mcp-bridge/"
    copy_dir: true
```

- [ ] **Step 4: Add init next-step hint**

In `cli/commands/init.py`, after the existing next steps, add:

```python
    if selected_mcps:
        print(f"  4. Run MCP diagnostics: amap doctor mcp --target {target}\n")
```

If the existing final print already includes a trailing newline, keep only one blank line in the output.

- [ ] **Step 5: Run focused tests**

Run: `pytest cli/tests/test_scaffold.py::test_manifest_declares_mcp_bridge_plugin cli/tests/test_init.py::test_init_scaffolds_mcp_bridge_when_platform_supports_tools cli/tests/test_init.py::test_init_prints_mcp_doctor_hint_when_mcps_selected -v`

Expected: PASS.

- [ ] **Step 6: Update snapshots**

Run: `pytest cli/tests/test_snapshots.py -v`

Expected: FAIL with snapshot diffs that include `tools/mcp-bridge/`.

Update each snapshot file to include:

```text
<root>/tools/mcp-bridge/
<root>/tools/mcp-bridge/README.md
<root>/tools/mcp-bridge/mcp_client.py
```

Use `.agents` for Antigravity and Codex, `.claude` for Claude Code, and `.amap` for Generic.

- [ ] **Step 7: Run snapshot tests**

Run: `pytest cli/tests/test_snapshots.py -v`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add cli/plugin-manifest.yaml cli/commands/init.py cli/tests/test_scaffold.py cli/tests/test_init.py cli/tests/snapshots
git commit -m "feat: scaffold mcp bridge diagnostics"
```

---

### Task 7: Subagent Evidence Artifacts And Gate Validators

**Files:**
- Create: `.amap/knowledge/templates/TASK_HANDOFF.tpl.md`
- Create: `.amap/knowledge/templates/CONTEXT_REQUEST.tpl.md`
- Create: `.amap/knowledge/templates/NODE_CHECKPOINT.tpl.md`
- Modify: `.amap/tools/gate-check/gates.py`
- Modify: `.amap/tools/gate-check/cli.py`
- Modify: `.amap/tools/gate-check/tests/test_gates.py`

**Interfaces:**
- Produces validator: `validate_context_request(text: str) -> Result`
- Produces validator: `validate_node_checkpoint(text: str) -> Result`
- Produces CLI gates: `context-request`, `node-checkpoint`

- [ ] **Step 1: Add failing validator tests**

Append to `.amap/tools/gate-check/tests/test_gates.py`:

```python
def test_context_request_requires_missing_evidence_and_requested_probe():
    empty = "# Context Request\n## Missing Evidence\n\n"
    filled = (
        "# Context Request\n"
        "## Missing Evidence\n- Missing DB column metadata\n"
        "## Why It Blocks\n- Cannot choose the correct repository method\n"
        "## Requested Probe\n- Run db metadata read for AD_USER\n"
    )
    assert g.validate_context_request(empty).ok is False
    assert g.validate_context_request(filled).ok is True


def test_node_checkpoint_requires_files_evidence_and_verification():
    empty = "# Node Checkpoint\n## Files Changed\n\n"
    filled = (
        "# Node Checkpoint\n"
        "## Files Changed\n- src/App.java\n"
        "## Requirement Satisfied\n- Implements TASK-1\n"
        "## Evidence Used\n- SP-6 from TASK_HANDOFF.node-1.md\n"
        "## Verification\n- pytest cli/tests/test_init.py -v: PASS\n"
    )
    assert g.validate_node_checkpoint(empty).ok is False
    assert g.validate_node_checkpoint(filled).ok is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest .amap/tools/gate-check/tests/test_gates.py::test_context_request_requires_missing_evidence_and_requested_probe .amap/tools/gate-check/tests/test_gates.py::test_node_checkpoint_requires_files_evidence_and_verification -v`

Expected: FAIL with `AttributeError` for missing validator functions.

- [ ] **Step 3: Implement validators**

In `.amap/tools/gate-check/gates.py`, add near the existing regex constants:

```python
_SECTION = r"##\s+{name}[ \t]*\n(.*?)(?=\n##\s|\Z)"
```

Add helper and validators:

```python
def _section_has_text(text: str, name: str) -> bool:
    pattern = re.compile(_SECTION.format(name=re.escape(name)), re.DOTALL | re.IGNORECASE)
    match = pattern.search(text)
    return bool(match and match.group(1).strip())


def validate_context_request(text: str) -> Result:
    required = ("Missing Evidence", "Why It Blocks", "Requested Probe")
    missing = [name for name in required if not _section_has_text(text, name)]
    if missing:
        return Result(False, f"context request missing sections: {', '.join(missing)}")
    return Result(True)


def validate_node_checkpoint(text: str) -> Result:
    required = ("Files Changed", "Requirement Satisfied", "Evidence Used", "Verification")
    missing = [name for name in required if not _section_has_text(text, name)]
    if missing:
        return Result(False, f"node checkpoint missing sections: {', '.join(missing)}")
    if not _RULE_ID.search(text):
        return Result(False, "node checkpoint missing rule-id evidence")
    return Result(True)
```

Modify `.amap/tools/gate-check/cli.py` gate map:

```python
    "context-request": "validate_context_request",
    "node-checkpoint": "validate_node_checkpoint",
```

- [ ] **Step 4: Add artifact templates**

Create `.amap/knowledge/templates/TASK_HANDOFF.tpl.md`:

```markdown
# TASK_HANDOFF.<node-id>

## Task Objective

## Scope

## Applicable DNA/Conventions

## Evidence

## Constraints

## Expected Output

## Verification
```

Create `.amap/knowledge/templates/CONTEXT_REQUEST.tpl.md`:

```markdown
# CONTEXT_REQUEST.<node-id>

## Missing Evidence

## Why It Blocks

## Requested Probe
```

Create `.amap/knowledge/templates/NODE_CHECKPOINT.tpl.md`:

```markdown
# NODE_CHECKPOINT.<node-id>

## Files Changed

## Requirement Satisfied

## Evidence Used

## Verification

## Known Risks
```

- [ ] **Step 5: Run gate tests**

Run: `pytest .amap/tools/gate-check/tests/test_gates.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add .amap/knowledge/templates/TASK_HANDOFF.tpl.md .amap/knowledge/templates/CONTEXT_REQUEST.tpl.md .amap/knowledge/templates/NODE_CHECKPOINT.tpl.md .amap/tools/gate-check/gates.py .amap/tools/gate-check/cli.py .amap/tools/gate-check/tests/test_gates.py
git commit -m "feat: add subagent evidence gates"
```

---

### Task 8: Runtime Rules For MCP Doctor, Bridge Fallback, And Subagent Review

**Files:**
- Modify: `.amap/procedures/bootstrap.md`
- Modify: `.amap/rules/rules-tool.md`
- Test: `.amap/tools/gate-check/tests/test_rule_collapse.py`

**Interfaces:**
- Consumes validators from Task 7
- Produces rule text requiring `amap doctor mcp` evidence/degrade and orchestrator review

- [ ] **Step 1: Add failing rule text tests**

Append to `.amap/tools/gate-check/tests/test_rule_collapse.py`:

```python
def test_rules_tool_mentions_bridge_fallback_and_node_checkpoint():
    text = (ROOT / "rules" / "rules-tool.md").read_text(encoding="utf-8")
    assert "mcp-bridge" in text
    assert "NODE_CHECKPOINT.<node-id>.md" in text
    assert "CONTEXT_REQUEST.<node-id>.md" in text
    assert "node-checkpoint" in text


def test_bootstrap_points_mcp_failures_to_doctor():
    text = (ROOT / "procedures" / "bootstrap.md").read_text(encoding="utf-8")
    assert "amap doctor mcp" in text
    assert "bridge fallback" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest .amap/tools/gate-check/tests/test_rule_collapse.py -v`

Expected: FAIL because the new strings are absent.

- [ ] **Step 3: Update bootstrap MCP probe text**

In `.amap/procedures/bootstrap.md`, within PHASE 5 MCP probe block, add this paragraph after the degrade sentence:

```markdown
>   Khi native MCP không khả dụng nhưng config hợp lệ, chạy `amap doctor mcp --target <repo>`
>   để tạo `mcp-doctor-report.md`. Nếu doctor chứng minh bridge fallback healthy, bootstrap
>   có thể ghi dòng `🔌 MCP: bridge fallback — <server> tools/list ok`; mọi reasoning dùng
>   bridge phải ghi vào `AGENT_TRANSPARENCY.md`. Không có native probe hoặc bridge evidence
>   thì vẫn phải degrade, không được ghi "Runtime Ready".
```

- [ ] **Step 4: Update tool rules**

In `.amap/rules/rules-tool.md`, under R-Tool-5, add:

```markdown
#### Bridge fallback

`{{ platform.framework_root }}/tools/mcp-bridge/mcp_client.py` chỉ được dùng khi:

- `resolved-config.yaml` có MCP tương ứng;
- native MCP probe fail hoặc runtime không inject tool;
- `amap doctor mcp` đã ghi bridge evidence vào `mcp-doctor-report.md`;
- agent ghi vào `AGENT_TRANSPARENCY.md` lý do dùng bridge thay native MCP.

Bridge không thay native MCP. Bridge không được dùng để gọi tool ghi dữ liệu/schema.
```

Under R-Tool-8, replace or extend the existing subagent paragraph with:

```markdown
#### Context request + orchestrator review

Nếu thiếu context trong khi chạy, subagent ghi `CONTEXT_REQUEST.<node-id>.md` và file này
phải pass:

`python3 {{ platform.framework_root }}/tools/gate-check/cli.py context-request <file>`

Orchestrator enrich context, cập nhật `TASK_HANDOFF.<node-id>.md`, rồi mới re-dispatch.
Khi subagent hoàn tất, output phải kèm `NODE_CHECKPOINT.<node-id>.md` và pass:

`python3 {{ platform.framework_root }}/tools/gate-check/cli.py node-checkpoint <file>`

Orchestrator review diff/proposal, evidence, scope, và test result trước khi accept/apply.
Subagent output không phải final chỉ vì subagent đã hoàn thành.
```

- [ ] **Step 5: Run rule tests**

Run: `pytest .amap/tools/gate-check/tests/test_rule_collapse.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add .amap/procedures/bootstrap.md .amap/rules/rules-tool.md .amap/tools/gate-check/tests/test_rule_collapse.py
git commit -m "docs: require mcp bridge evidence and subagent review"
```

---

### Task 9: Antigravity Write-Gate `TargetFile` Support

**Files:**
- Modify: `.amap/hooks/write-gate/write_gate.py`
- Modify: `.amap/hooks/write-gate/tests/test_write_gate.py`

**Interfaces:**
- Consumes: `extract_target_paths(payload: dict) -> list[Path]`
- Produces support for `toolCall.args.TargetFile` and `tool_input.TargetFile`

- [ ] **Step 1: Add failing write-gate tests**

Append to `.amap/hooks/write-gate/tests/test_write_gate.py`:

```python
def test_extracts_targetfile_from_antigravity_toolcall_payload():
    payload = {
        "toolCall": {
            "name": "replace_file_content",
            "args": {"TargetFile": "src/App.java"},
        }
    }
    assert wg.extract_target_paths(payload) == [Path("src/App.java")]


def test_extracts_targetfile_from_antigravity_tool_input_payload():
    payload = {
        "tool_name": "write_to_file",
        "tool_input": {"TargetFile": "src/App.java"},
    }
    assert wg.extract_target_paths(payload) == [Path("src/App.java")]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest .amap/hooks/write-gate/tests/test_write_gate.py::test_extracts_targetfile_from_antigravity_toolcall_payload .amap/hooks/write-gate/tests/test_write_gate.py::test_extracts_targetfile_from_antigravity_tool_input_payload -v`

Expected: FAIL because `extract_target_paths` returns `[]`.

- [ ] **Step 3: Patch extraction**

In `.amap/hooks/write-gate/write_gate.py`, update the `direct = (` expression:

```python
    direct = (
        _path_from_value(tool_input.get("file_path"))
        or _path_from_value(tool_input.get("path"))
        or _path_from_value(tool_input.get("TargetFile"))
        or _path_from_value(tool_args.get("file_path"))
        or _path_from_value(tool_args.get("path"))
        or _path_from_value(tool_args.get("FilePath"))
        or _path_from_value(tool_args.get("TargetFile"))
    )
```

- [ ] **Step 4: Run write-gate tests**

Run: `pytest .amap/hooks/write-gate/tests/test_write_gate.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .amap/hooks/write-gate/write_gate.py .amap/hooks/write-gate/tests/test_write_gate.py
git commit -m "fix: parse antigravity targetfile write payloads"
```

---

### Task 10: README And Full Verification

**Files:**
- Modify: `README.md`
- Modify: `cli/tests/snapshots/antigravity.txt`
- Modify: `cli/tests/snapshots/claude-code.txt`
- Modify: `cli/tests/snapshots/codex.txt`
- Modify: `cli/tests/snapshots/generic.txt`

**Interfaces:**
- Consumes all prior tasks
- Produces public user guidance for `amap doctor mcp`

- [ ] **Step 1: Add README MCP doctor section**

In `README.md`, in the MCP Integration section, add:

````markdown
### MCP Doctor

Sau khi chọn MCP lúc `amap init` hoặc `amap update --reconfigure`, chạy:

```bash
.venv/bin/python -m cli.amap doctor mcp --target /path/to/your-project
```

Doctor kiểm tra config MCP native của Codex, Claude Code, hoặc Antigravity, ghi
`mcp-doctor-report.md`, và thử bridge fallback khi native MCP không khả dụng.
Doctor không sửa config trừ khi bạn chạy:

```bash
.venv/bin/python -m cli.amap doctor mcp --target /path/to/your-project --fix
```
````

- [ ] **Step 2: Run full CLI and gate tests**

Run:

```bash
pytest cli/tests .amap/tools/gate-check/tests .amap/hooks/write-gate/tests -v
```

Expected: PASS.

- [ ] **Step 3: Run scaffold smoke commands**

Run:

```bash
tmpdir=$(mktemp -d)
python -m cli.amap init --target "$tmpdir/antigravity" --platform antigravity --mcp socraticode --language python --yes
python -m cli.amap doctor mcp --target "$tmpdir/antigravity"
test -f "$tmpdir/antigravity/.agents/tools/mcp-bridge/mcp_client.py"
test -f "$tmpdir/antigravity/.agents/knowledge/active/mcp-doctor-report.md"
```

Expected: all commands exit 0.

- [ ] **Step 4: Verify dirty worktree scope**

Run: `git status --short`

Expected: only files intentionally changed by this plan are listed, plus any pre-existing unrelated task-list deletions or proposal files. Do not stage unrelated changes unless the user explicitly asks.

- [ ] **Step 5: Commit docs and final verification changes**

```bash
git add README.md cli/tests/snapshots/antigravity.txt cli/tests/snapshots/claude-code.txt cli/tests/snapshots/codex.txt cli/tests/snapshots/generic.txt
git commit -m "docs: document mcp doctor workflow"
```

---

## Plan Self-Review

Spec coverage:

- Three runtimes: covered by Task 1 adapter tests and Task 4 doctor status.
- `amap doctor mcp`: covered by Tasks 4 and 5.
- Controlled bridge fallback: covered by Tasks 3, 6, and 8.
- Setup safety: covered by Task 6 init behavior and Task 5 explicit fix mode.
- Subagent context request and orchestrator review: covered by Tasks 7 and 8.
- Antigravity `TargetFile`: covered by Task 9.
- Security and redaction: covered by Task 2 redaction tests and Task 3 bridge constraints.
- Verification: covered by per-task tests and Task 10 full verification.

Placeholder scan:

- The plan contains no placeholder or deferred-work markers.
- Artifact names with `<node-id>` are literal template names from the approved spec.

Type consistency:

- `McpConfigCandidate`, `McpPlatformAdapter`, `LoadedMcpConfig`, and `DoctorStatus` names are introduced before use.
- `run_doctor_mcp`, `build_doctor_status`, `write_report`, and `apply_fix` signatures are stable across tasks.
- Gate names `context-request` and `node-checkpoint` match the validator names introduced in Task 7.
