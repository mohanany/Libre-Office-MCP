from . import writer  # noqa: F401

# Per-application tool modules. Each exposes register(mcp, bridge).
# Add calc/impress/draw modules here as they are implemented.
MODULES = [writer]
