"""Math (formula document) tools.

Note: module file is math_.py to avoid shadowing Python's stdlib `math`.
"""

from __future__ import annotations

import os

import uno

from ..bridge import OfficeBridge, _prop


def _math_doc(bridge: OfficeBridge, index: int):
    doc = bridge.get_document(index)
    # Math documents expose XFormulaDocument / service FormulaProperties
    if not doc.supportsService("com.sun.star.formula.FormulaProperties"):
        raise ValueError(f"document [{index}] is not a Math document")
    return doc


def register(mcp, bridge: OfficeBridge) -> None:

    @mcp.tool()
    def math_create(hidden: bool = False) -> str:
        """Create a new Math (formula) document."""
        doc = bridge.create_document("math", hidden=hidden)
        for i, d, _, _ in bridge.list_documents():
            if d == doc:
                return f"Created Math document [{i}]"
        return "Created Math document"

    @mcp.tool()
    def math_set_formula(index: int, formula: str) -> str:
        """Set the formula content using StarMath syntax, e.g. 'a^2 + b^2 = c^2'."""
        doc = _math_doc(bridge, index)
        doc.Formula = formula
        return f"Set formula on document [{index}]"

    @mcp.tool()
    def math_get_formula(index: int) -> str:
        """Get the StarMath source of a Math document's formula."""
        doc = _math_doc(bridge, index)
        return doc.Formula or "(empty)"

    @mcp.tool()
    def math_export_mathml(index: int, path: str) -> str:
        """Export a Math document to MathML (.mml)."""
        doc = _math_doc(bridge, index)
        url = uno.systemPathToFileUrl(os.path.abspath(path))
        doc.storeToURL(url, [_prop("FilterName", "MathML XML (Math)")])
        return f"Exported Math document [{index}] to {path}"
