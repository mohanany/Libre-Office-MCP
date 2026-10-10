"""Tools shared across every LibreOffice application."""

from __future__ import annotations

import os

import uno

from .bridge import FILTER_MAP, OfficeBridge, _prop


def register(mcp, bridge: OfficeBridge) -> None:

    @mcp.tool()
    def office_status() -> str:
        """Check whether LibreOffice is reachable over UNO."""
        try:
            bridge.ensure_started()
        except Exception as exc:  # noqa: BLE001
            return f"LibreOffice unavailable: {exc}"
        return f"LibreOffice connected on {bridge.host}:{bridge.port}"

    @mcp.tool()
    def document_list() -> str:
        """List all currently open LibreOffice documents with their index and type."""
        docs = bridge.list_documents()
        if not docs:
            return "No open documents."
        lines = [
            f"[{i}] {kind}\t{url or '(unsaved)'}" for i, _, url, kind in docs
        ]
        return "\n".join(lines)

    @mcp.tool()
    def document_open(path: str, kind: str | None = None) -> str:
        """Open a document file in LibreOffice.

        path: absolute path to the file.
        kind: optional hint — writer | calc | impress | draw (auto-detected otherwise).
        """
        doc = bridge.open_document(path)
        for i, _, url, k in bridge.list_documents():
            if url == doc.getURL():
                return f"Opened as document [{i}] ({k}): {url}"
        return f"Opened: {doc.getURL()}"

    @mcp.tool()
    def document_save(index: int) -> str:
        """Save an open document by its index (see document_list)."""
        doc = bridge.get_document(index)
        doc.store()
        return f"Saved document [{index}] ({doc.getURL()})"

    @mcp.tool()
    def document_export(index: int, path: str, format: str = "pdf") -> str:
        """Export an open document to another format.

        index: document index from document_list.
        path: output file path.
        format: pdf | docx | odt | txt | html | xlsx | ods | csv | pptx | odp | svg | png
        """
        doc = bridge.get_document(index)
        _, _, _, kind = next(
            d for d in bridge.list_documents() if d[1] == doc
        )
        filters = FILTER_MAP.get(kind, {})
        filt = filters.get(format.lower())
        if not filt:
            raise ValueError(
                f"format '{format}' not supported for {kind}; "
                f"try: {', '.join(filters) or 'none'}"
            )
        url = uno.systemPathToFileUrl(os.path.abspath(path))
        doc.storeToURL(url, [_prop("FilterName", filt)])
        return f"Exported document [{index}] to {path} ({format})"

    @mcp.tool()
    def document_close(index: int, save: bool = False) -> str:
        """Close an open document. Set save=true to save changes first."""
        doc = bridge.get_document(index)
        if save:
            doc.store()
        doc.close(False)
        return f"Closed document [{index}]"
