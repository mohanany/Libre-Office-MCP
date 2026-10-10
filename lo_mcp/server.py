"""Server construction shared by the main entry point and per-app entries."""

from __future__ import annotations

import sys


def build_server(apps: list[str] | None = None):
    """Create the FastMCP server for the given app names.

    apps: subset of module names in lo_mcp.apps (None = all, plus common tools).
    """
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
    from . import apps as apps_pkg
    from .bridge import OfficeBridge

    bridge = OfficeBridge()
    selected = apps_pkg.MODULES if apps is None else [
        m for m in apps_pkg.MODULES if m.__name__.rsplit(".", 1)[-1].rstrip("_") in apps
    ]
    name = "libreoffice" if apps is None else f"libreoffice-{apps[0]}"
    mcp = FastMCP(name)

    common.register(mcp, bridge)
    for module in selected:
        module.register(mcp, bridge)
    return mcp


def run(apps: list[str] | None = None) -> None:
    build_server(apps).run()


def run_app(app: str) -> None:
    """Console-script entry for a single-app server."""
    run([app])
