"""Entry point: stdio MCP server exposing per-app LibreOffice tools.

Run:
    python -m lo_mcp

MCP client config (Claude Desktop etc.):
    {"mcpServers": {"libreoffice": {"command": "python3", "args": ["-m", "lo_mcp"]}}}

Note: the interpreter must have the `uno` module — usually the system
python3 (apt install python3-uno) or LibreOffice's bundled python.
"""

from __future__ import annotations

import sys


def main() -> None:
    try:
        import uno  # noqa: F401
    except ModuleNotFoundError:
        sys.stderr.write(
            "lo_mcp: `import uno` failed — run with the system python3 "
            "(apt install python3-uno) or LibreOffice's bundled python.\n"
        )
        raise

    from mcp.server.fastmcp import FastMCP

    from . import common
    from .apps import MODULES
    from .bridge import OfficeBridge

    mcp = FastMCP("libreoffice")
    bridge = OfficeBridge()

    common.register(mcp, bridge)
    for module in MODULES:
        module.register(mcp, bridge)

    mcp.run()


if __name__ == "__main__":
    main()
