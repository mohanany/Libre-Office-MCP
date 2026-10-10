from . import calc, writer  # noqa: F401

# Per-application tool modules. Each exposes register(mcp, bridge).
# Add impress/draw modules here as they are implemented.
MODULES = [writer, calc]
