"""Entry point: stdio MCP server exposing per-app LibreOffice tools.

Run:
    python -m lo_mcp            # all apps + common tools
    python -m lo_mcp calc       # only the Calc toolset
    python -m lo_mcp writer calc

MCP client config (Claude Desktop etc.):
    {"mcpServers": {"libreoffice": {"command": "python3", "args": ["-m", "lo_mcp"]}}}
"""

from __future__ import annotations

import sys


def main() -> None:
    from .server import run

    apps = sys.argv[1:] or None
    run(apps)


if __name__ == "__main__":
    main()
