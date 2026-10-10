"""UNO component loaded inside the LibreOffice process by the .oxt.

Phase 1 (stdio bridge) does not strictly need this file — the MCP server
connects over a UNO socket it can open itself. This component exists so the
extension can, in a later phase:

  * auto-open the UNO acceptor when LibreOffice starts,
  * expose a Tools ▸ MCP menu to enable/disable and pick a port,
  * eventually serve MCP from inside the process (no socket at all).

Kept intentionally minimal for v0.1.
"""

import uno  # noqa: F401  (provided by LibreOffice's python runtime)

ENABLED = False


def enable_uno_socket(port: int = 2002) -> None:
    """Placeholder: auto-open a UNO socket acceptor from inside LO."""
    # Implemented in the next milestone via the configuration/acceptor APIs.
    raise NotImplementedError("coming in the .oxt milestone")


g_ImplementationHelper = None  # no services exported yet
