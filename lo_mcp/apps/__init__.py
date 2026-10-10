from . import calc, draw, impress, writer  # noqa: F401

# Per-application tool modules. Each exposes register(mcp, bridge).
# Add base/math modules here as they are implemented.
MODULES = [writer, calc, impress, draw]
