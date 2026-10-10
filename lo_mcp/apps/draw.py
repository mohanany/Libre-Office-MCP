"""Draw (DrawingDocument) tools."""

from __future__ import annotations

import uno
from com.sun.star.awt import Point, Size

from ..bridge import OfficeBridge

DRAW_SVC = "com.sun.star.drawing.DrawingDocument"

SHAPE_SERVICES = {
    "rectangle": "com.sun.star.drawing.RectangleShape",
    "ellipse": "com.sun.star.drawing.EllipseShape",
    "line": "com.sun.star.drawing.LineShape",
    "text": "com.sun.star.drawing.TextShape",
    "connector": "com.sun.star.drawing.ConnectorShape",
    "polygon": "com.sun.star.drawing.PolyPolygonShape",
}


def _draw_doc(bridge: OfficeBridge, index: int):
    doc = bridge.get_document(index)
    if not doc.supportsService(DRAW_SVC):
        raise ValueError(f"document [{index}] is not a Draw document")
    return doc


def _page(doc, page: int):
    pages = doc.DrawPages
    if page < 0 or page >= pages.Count:
        raise IndexError(
            f"page {page} out of range (document has {pages.Count} page(s))"
        )
    return pages.getByIndex(page)


def _pt(x_mm: float) -> int:
    return int(round(x_mm * 100))  # 1/100 mm


def register(mcp, bridge: OfficeBridge) -> None:

    @mcp.tool()
    def draw_create(hidden: bool = False) -> str:
        """Create a new Draw document with one page."""
        doc = bridge.create_document("draw", hidden=hidden)
        for i, d, _, _ in bridge.list_documents():
            if d == doc:
                return f"Created Draw document [{i}]"
        return "Created Draw document"

    @mcp.tool()
    def draw_page_count(index: int) -> str:
        """Return the number of pages in a Draw document."""
        doc = _draw_doc(bridge, index)
        return f"{doc.DrawPages.Count} page(s) in document [{index}]"

    @mcp.tool()
    def draw_add_page(index: int, position: int | None = None) -> str:
        """Add a page. position: 0-based index; omit to append at the end."""
        doc = _draw_doc(bridge, index)
        pages = doc.DrawPages
        pos = pages.Count if position is None else position
        pages.insertNewByIndex(pos)
        return f"Added page at {pos}; document [{index}] now has {pages.Count} page(s)"

    @mcp.tool()
    def draw_add_shape(
        index: int,
        shape: str,
        page: int = 0,
        x: float = 50,
        y: float = 50,
        width: float = 40,
        height: float = 40,
        text: str | None = None,
        fill_color: int | None = None,
    ) -> str:
        """Add a shape to a Draw page.

        shape: rectangle | ellipse | line | text | connector | polygon
        x, y, width, height: in millimetres.
        fill_color: RGB int (e.g. 16711680 for red); omit for default.
        text: text content for text-capable shapes.
        """
        doc = _draw_doc(bridge, index)
        svc = SHAPE_SERVICES.get(shape.lower())
        if not svc:
            raise ValueError(
                f"unknown shape '{shape}'; try: {', '.join(SHAPE_SERVICES)}"
            )
        sh = doc.createInstance(svc)
        sh.Position = Point(_pt(x), _pt(y))
        sh.Size = Size(_pt(width), _pt(height))
        if fill_color is not None:
            sh.FillColor = fill_color
        if text is not None and hasattr(sh, "setString"):
            sh.setString(text)
        _page(doc, page).add(sh)
        return f"Added {shape} to page {page} of document [{index}]"

    @mcp.tool()
    def draw_list_shapes(index: int, page: int = 0) -> str:
        """List shapes on a Draw page: index, type, name, position, size."""
        doc = _draw_doc(bridge, index)
        p = _page(doc, page)
        lines = []
        for i in range(p.Count):
            sh = p.getByIndex(i)
            pos, size = sh.Position, sh.Size
            lines.append(
                f"[{i}] {sh.ShapeType} name={getattr(sh, 'Name', '')!r} "
                f"at ({pos.X / 100:.0f},{pos.Y / 100:.0f})mm "
                f"{size.Width / 100:.0f}x{size.Height / 100:.0f}mm"
            )
        return "\n".join(lines) if lines else f"Page {page} has no shapes"

    @mcp.tool()
    def draw_set_shape_text(
        index: int, page: int, shape: int, text: str
    ) -> str:
        """Set the text of a shape by its index on the page."""
        doc = _draw_doc(bridge, index)
        p = _page(doc, page)
        sh = p.getByIndex(shape)
        sh.setString(text)
        return f"Set text on shape {shape}, page {page}, document [{index}]"

    @mcp.tool()
    def draw_list_layers(index: int, page: int = 0) -> str:
        """List layer names of a Draw page."""
        doc = _draw_doc(bridge, index)
        p = _page(doc, page)
        mgr = p.getPropertyValue("LayerManager") \
            if hasattr(p, "getPropertyValue") else doc.LayerManager
        return "\n".join(mgr.ElementNames)
