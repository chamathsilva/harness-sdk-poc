"""A tiny MCP server over streamable HTTP, used to test the non-stdio transport.

Run standalone: `python mcp_http_server.py [port]`. Exposes two trivial tools so the
harness has something unmistakable to discover and call.
"""
import sys

from mcp.server.mcpserver import MCPServer

server = MCPServer("probe")


@server.tool()
def echo_upper(text: str) -> str:
    """Return the given text in upper case."""
    return text.upper()


@server.tool()
def magic_number() -> int:
    """Return the probe's magic number."""
    return 4242


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8931
    server.run(transport="streamable-http", host="127.0.0.1", port=port)
