from . import base, calc, draw, impress, math_, writer  # noqa: F401

# Per-application tool modules. Each exposes register(mcp, bridge).
MODULES = [writer, calc, impress, draw, base, math_]
