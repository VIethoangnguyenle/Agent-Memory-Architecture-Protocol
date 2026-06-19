"""MCP config loading and redaction helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # Python 3.9-3.10
    import tomli as tomllib  # type: ignore[no-redef]

from cli.mcp.adapters import McpConfigCandidate


_SECRET_KEYS = ("authorization", "token", "secret", "password", "api_key", "apikey", "key")


@dataclass(frozen=True)
class LoadedMcpConfig:
    path: Path
    format: str
    exists: bool
    valid: bool
    servers: dict[str, dict[str, Any]]
    error: str = ""


def _extract_servers(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    for key in ("mcpServers", "mcp_servers"):
        value = data.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _load_raw(candidate: McpConfigCandidate) -> tuple[bool, str]:
    if not candidate.path.exists():
        return False, ""
    return True, candidate.path.read_text(encoding="utf-8")


def load_mcp_config(candidate: McpConfigCandidate) -> LoadedMcpConfig:
    exists, raw = _load_raw(candidate)
    if not exists:
        return LoadedMcpConfig(candidate.path, candidate.format, False, False, {}, "missing")
    if not raw.strip():
        return LoadedMcpConfig(candidate.path, candidate.format, True, False, {}, "empty config")

    try:
        if candidate.format == "json":
            data = json.loads(raw)
        elif candidate.format == "toml":
            data = tomllib.loads(raw)
        else:
            return LoadedMcpConfig(
                candidate.path,
                candidate.format,
                True,
                False,
                {},
                "unsupported format",
            )
    except (json.JSONDecodeError, tomllib.TOMLDecodeError):
        return LoadedMcpConfig(
            candidate.path,
            candidate.format,
            True,
            False,
            {},
            f"invalid {candidate.format}",
        )

    if not isinstance(data, dict):
        return LoadedMcpConfig(candidate.path, candidate.format, True, False, {}, "config root is not an object")

    servers = _extract_servers(data)
    if not servers:
        return LoadedMcpConfig(candidate.path, candidate.format, True, False, {}, "missing mcpServers")

    return LoadedMcpConfig(candidate.path, candidate.format, True, True, servers)


def server_names(config: LoadedMcpConfig) -> list[str]:
    return list(config.servers)


def selected_server_matches(config: LoadedMcpConfig, selected: list[str]) -> tuple[list[str], list[str]]:
    names = set(server_names(config))
    present = [name for name in selected if name in names]
    missing = [name for name in selected if name not in names]
    return present, missing


def _looks_sensitive(key: Any) -> bool:
    key_text = str(key).lower()
    return any(secret in key_text for secret in _SECRET_KEYS)


def redact_mapping(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[Any, Any] = {}
        for key, item in value.items():
            if _looks_sensitive(key):
                redacted[key] = "<redacted>"
            else:
                redacted[key] = redact_mapping(item)
        return redacted
    if isinstance(value, list):
        return [redact_mapping(item) for item in value]
    return value
