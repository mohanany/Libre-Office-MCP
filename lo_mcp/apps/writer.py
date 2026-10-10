"""Writer (TextDocument) tools."""

from __future__ import annotations

import uno

from ..bridge import OfficeBridge

WRITER_SVC = "com.sun.star.text.TextDocument"


def _writer_doc(bridge: OfficeBridge, index: int):
    doc = bridge.get_document(index)
    if not doc.supportsService(WRITER_SVC):
        raise ValueError(f"document [{index}] is not a Writer document")
    return doc


def register(mcp, bridge: OfficeBridge) -> None:

    @mcp.tool()
    def writer_create(text: str = "", hidden: bool = False) -> str:
        """Create a new Writer document, optionally with initial text."""
        doc = bridge.create_document("writer", hidden=hidden)
        if text:
            doc.Text.setString(text)
        for i, d, _, _ in bridge.list_documents():
            if d == doc:
                return f"Created Writer document [{i}]"
        return "Created Writer document"

    @mcp.tool()
    def writer_read_text(index: int) -> str:
        """Read the full plain-text content of a Writer document."""
        doc = _writer_doc(bridge, index)
        return doc.Text.getString()

    @mcp.tool()
    def writer_insert_text(
        index: int,
        text: str,
        position: str = "end",
        offset: int | None = None,
    ) -> str:
        """Insert text into a Writer document.

        position: 'start' | 'end' | 'cursor' | 'offset'
        offset: character offset, required when position='offset'.
        """
        doc = _writer_doc(bridge, index)
        txt = doc.Text
        cursor = txt.createTextCursor()
        if position == "start":
            cursor.gotoStart(False)
        elif position == "end":
            cursor.gotoEnd(False)
        elif position == "cursor":
            ctrl = doc.getCurrentController()
            cursor = ctrl.getViewCursor() if ctrl else cursor
        elif position == "offset":
            if offset is None:
                raise ValueError("offset is required when position='offset'")
            cursor.gotoStart(False)
            cursor.goRight(offset, False)
        else:
            raise ValueError(
                "position must be start|end|cursor|offset"
            )
        cursor.setString(text)
        return f"Inserted {len(text)} characters into document [{index}]"

    @mcp.tool()
    def writer_format_selection(
        index: int,
        bold: bool | None = None,
        italic: bool | None = None,
        font_name: str | None = None,
        font_size: float | None = None,
        start_offset: int | None = None,
        end_offset: int | None = None,
    ) -> str:
        """Apply formatting to a range (or the current selection) in a Writer document.

        start_offset/end_offset: character range; omit to format current selection.
        """
        doc = _writer_doc(bridge, index)
        cursor = doc.Text.createTextCursor()
        if start_offset is not None and end_offset is not None:
            cursor.gotoStart(False)
            cursor.goRight(start_offset, False)
            cursor.goRight(end_offset - start_offset, True)
        else:
            ctrl = doc.getCurrentController()
            if ctrl:
                vc = ctrl.getViewCursor()
                cursor.gotoRange(vc.getStart(), False)
                cursor.gotoRange(vc.getEnd(), True)
        if bold is not None:
            cursor.CharWeight = 150.0 if bold else 100.0  # BOLD / NORMAL
        if italic is not None:
            cursor.CharPosture = uno.Enum(  # type: ignore[name-defined]
                "com.sun.star.awt.FontSlant", "ITALIC" if italic else "NONE"
            )
        if font_name:
            cursor.CharFontName = font_name
        if font_size is not None:
            cursor.CharHeight = float(font_size)
        return f"Formatted selection in document [{index}]"

    @mcp.tool()
    def writer_find_replace(index: int, find: str, replace: str) -> str:
        """Replace all occurrences of `find` with `replace` in a Writer document."""
        doc = _writer_doc(bridge, index)
        rd = doc.createReplaceDescriptor()
        rd.SearchString = find
        rd.ReplaceString = replace
        count = doc.replaceAll(rd)
        return f"Replaced {count} occurrence(s) in document [{index}]"

    @mcp.tool()
    def writer_paragraph_count(index: int) -> str:
        """Return the number of paragraphs in a Writer document."""
        doc = _writer_doc(bridge, index)
        enum = doc.Text.createEnumeration()
        n = 0
        while enum.hasMoreElements():
            enum.nextElement()
            n += 1
        return f"{n} paragraph(s) in document [{index}]"
