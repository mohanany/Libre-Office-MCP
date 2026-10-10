from . import calc, impress, writer  # noqa: F401

# Per-application tool modules. Each exposes register(mcp, bridge).
# Add draw/base/math modules here as they are implemented.
MODULES = [writer, calc, impress]
