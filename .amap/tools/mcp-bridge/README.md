# MCP Bridge

This tool is an AMAP diagnostic and fallback client for MCP servers.

Use native MCP tools when the runtime exposes them. Use this bridge only when
`amap doctor mcp` reports that native MCP is unavailable and records bridge
fallback evidence.

The bridge requires an explicit config path and server name. It does not scan
home-directory config locations by itself.
