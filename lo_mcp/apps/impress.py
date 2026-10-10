"""Impress (PresentationDocument) tools."""

from __future__ import annotations

from ..bridge import OfficeBridge

IMPRESS_SVC = "com.sun.star.presentation.PresentationDocument"


def _impress_doc(bridge: OfficeBridge, index: int):
    doc = bridge.get_document(index)
    if not doc.supportsService(IMPRESS_SVC):
        raise ValueError(f"document [{index}] is not an Impress document")
    return doc


def _slide(doc, slide: int):
    pages = doc.DrawPages
    if slide < 0 or slide >= pages.Count:
        raise IndexError(
            f"slide {slide} out of range (document has {pages.Count} slide(s))"
        )
    return pages.getByIndex(slide)


def register(mcp, bridge: OfficeBridge) -> None:

    @mcp.tool()
    def impress_create(hidden: bool = False) -> str:
        """Create a new Impress presentation with one blank slide."""
        doc = bridge.create_document("impress", hidden=hidden)
        for i, d, _, _ in bridge.list_documents():
            if d == doc:
                return f"Created Impress document [{i}] with {doc.DrawPages.Count} slide(s)"
        return "Created Impress document"

    @mcp.tool()
    def impress_slide_count(index: int) -> str:
        """Return the number of slides in an Impress document."""
        doc = _impress_doc(bridge, index)
        return f"{doc.DrawPages.Count} slide(s) in document [{index}]"

    @mcp.tool()
    def impress_add_slide(index: int, position: int | None = None) -> str:
        """Add a slide to an Impress document.

        position: 0-based insertion index; omit to append at the end.
        """
        doc = _impress_doc(bridge, index)
        pages = doc.DrawPages
        pos = pages.Count if position is None else position
        pages.insertNewByIndex(pos)
        return (
            f"Added slide at position {pos}; "
            f"document [{index}] now has {pages.Count} slide(s)"
        )

    @mcp.tool()
    def impress_delete_slide(index: int, slide: int) -> str:
        """Delete a slide by its 0-based index."""
        doc = _impress_doc(bridge, index)
        pages = doc.DrawPages
        pages.remove(_slide(doc, slide))
        return f"Deleted slide {slide}; document [{index}] now has {pages.Count} slide(s)"

    @mcp.tool()
    def impress_set_slide_layout(index: int, slide: int, layout: int) -> str:
        """Set a slide's layout number (0=title slide, 1=title+content, 20=blank, …)."""
        doc = _impress_doc(bridge, index)
        s = _slide(doc, slide)
        s.Layout = layout
        return f"Slide {slide} of document [{index}] set to layout {layout}"

    @mcp.tool()
    def impress_set_slide_text(
        index: int,
        slide: int,
        title: str | None = None,
        body: str | None = None,
    ) -> str:
        """Set the title and/or body text of a slide's placeholder shapes."""
        doc = _impress_doc(bridge, index)
        s = _slide(doc, slide)
        changed = []
        title_done = body_done = False
        for i in range(s.Count):
            shape = s.getByIndex(i)
            if not shape.supportsService("com.sun.star.presentation.TitleTextShape") \
                    and not shape.supportsService("com.sun.star.presentation.OutlinerShape"):
                continue
            svc = shape.getPresentation().getPropertyValue("PresentationClass") \
                if hasattr(shape, "getPresentation") else None
            try:
                pclass = shape.PresentationClass  # 'Title' | 'Outline' | …
            except Exception:
                pclass = svc or ""
            if title is not None and not title_done and str(pclass).lower() == "title":
                shape.setString(title)
                title_done = True
                changed.append("title")
            elif body is not None and not body_done and str(pclass).lower() in (
                "outline", "subtitle", "notes"
            ):
                shape.setString(body)
                body_done = True
                changed.append("body")
        # fallback: title → first text shape, body → second
        if title is not None and not title_done:
            for i in range(s.Count):
                shape = s.getByIndex(i)
                if hasattr(shape, "setString"):
                    shape.setString(title)
                    changed.append("title (fallback shape)")
                    break
        if not changed:
            return f"No matching placeholder found on slide {slide} of document [{index}]"
        return f"Set {', '.join(changed)} on slide {slide} of document [{index}]"

    @mcp.tool()
    def impress_get_slide_text(index: int, slide: int) -> str:
        """Read all text contained in a slide's shapes."""
        doc = _impress_doc(bridge, index)
        s = _slide(doc, slide)
        parts = []
        for i in range(s.Count):
            shape = s.getByIndex(i)
            if hasattr(shape, "getString") and shape.getString():
                parts.append(f"[shape {i}] {shape.getString()}")
        if not parts:
            return f"Slide {slide} of document [{index}] has no text"
        return "\n".join(parts)

    @mcp.tool()
    def impress_set_slide_notes(index: int, slide: int, notes: str) -> str:
        """Set the speaker notes of a slide."""
        doc = _impress_doc(bridge, index)
        s = _slide(doc, slide)
        notes_page = s.NotesPage
        for i in range(notes_page.Count):
            shape = notes_page.getByIndex(i)
            if hasattr(shape, "setString") and \
                    shape.supportsService("com.sun.star.presentation.NotesShape"):
                shape.setString(notes)
                return f"Set notes on slide {slide} of document [{index}]"
        # fallback: any text-capable shape
        for i in range(notes_page.Count):
            shape = notes_page.getByIndex(i)
            if hasattr(shape, "setString"):
                shape.setString(notes)
                return f"Set notes on slide {slide} of document [{index}] (fallback shape)"
        return f"No notes shape found on slide {slide} of document [{index}]"

    @mcp.tool()
    def impress_list_shapes(index: int, slide: int) -> str:
        """List shapes on a slide: index, service type, name, size."""
        doc = _impress_doc(bridge, index)
        s = _slide(doc, slide)
        lines = []
        for i in range(s.Count):
            shape = s.getByIndex(i)
            svc = shape.ShapeType if hasattr(shape, "ShapeType") else "shape"
            name = getattr(shape, "Name", "") or ""
            size = shape.Size
            lines.append(
                f"[{i}] {svc} name={name!r} {size.Width}x{size.Height}"
            )
        return "\n".join(lines) if lines else f"Slide {slide} has no shapes"
