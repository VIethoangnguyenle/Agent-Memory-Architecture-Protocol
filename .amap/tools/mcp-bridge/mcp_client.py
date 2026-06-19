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
    print(
        json.dumps(
            {
                "ok": ok,
                "server": server,
                "operation": operation,
                "result": result,
                "error": error,
            },
            ensure_ascii=False,
        )
    )
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
