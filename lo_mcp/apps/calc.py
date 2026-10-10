"""Calc (SpreadsheetDocument) tools."""

from __future__ import annotations

import re

from ..bridge import OfficeBridge

CALC_SVC = "com.sun.star.sheet.SpreadsheetDocument"

_A1 = re.compile(r"^([A-Za-z]+)([0-9]+)$")


def _a1_to_xy(ref: str) -> tuple[int, int]:
    """'B3' -> (col=1, row=2), 0-based."""
    m = _A1.match(ref.strip())
    if not m:
        raise ValueError(f"invalid cell reference '{ref}' (expected e.g. B3)")
    col = 0
    for ch in m.group(1).upper():
        col = col * 26 + (ord(ch) - ord("A") + 1)
    return col - 1, int(m.group(2)) - 1


def _calc_doc(bridge: OfficeBridge, index: int):
    doc = bridge.get_document(index)
    if not doc.supportsService(CALC_SVC):
        raise ValueError(f"document [{index}] is not a Calc document")
    return doc


def _sheet(doc, sheet: str | int | None):
    sheets = doc.Sheets
    if sheet is None:
        return sheets.getByIndex(0)
    if isinstance(sheet, int) or (isinstance(sheet, str) and sheet.isdigit()):
        return sheets.getByIndex(int(sheet))
    return sheets.getByName(sheet)


def register(mcp, bridge: OfficeBridge) -> None:

    @mcp.tool()
    def calc_create(hidden: bool = False) -> str:
        """Create a new Calc spreadsheet document."""
        doc = bridge.create_document("calc", hidden=hidden)
        for i, d, _, _ in bridge.list_documents():
            if d == doc:
                return f"Created Calc document [{i}]"
        return "Created Calc document"

    @mcp.tool()
    def calc_set_cell(
        index: int,
        cell: str,
        value: str,
        sheet: str | int | None = None,
    ) -> str:
        """Set a cell's content in a Calc document.

        cell: A1-style reference, e.g. 'B3'.
        value: number for numeric entry, '=SUM(A1:A5)' for a formula,
               anything else becomes text. Formula arguments use ';'
               (LibreOffice native grammar), e.g. '=SUM(B1:B2;C1:C2)'.
        sheet: sheet name or 0-based index (default: first sheet).
        """
        doc = _calc_doc(bridge, index)
        x, y = _a1_to_xy(cell)
        c = _sheet(doc, sheet).getCellByPosition(x, y)
        if value.startswith("="):
            c.setFormula(value)
        else:
            try:
                c.setValue(float(value))
            except ValueError:
                c.setString(value)
        return f"Set {cell} in document [{index}]"

    @mcp.tool()
    def calc_get_cell(
        index: int,
        cell: str,
        sheet: str | int | None = None,
    ) -> str:
        """Read a cell's displayed value and formula from a Calc document."""
        doc = _calc_doc(bridge, index)
        x, y = _a1_to_xy(cell)
        c = _sheet(doc, sheet).getCellByPosition(x, y)
        return (
            f"{cell}: value={c.getString()!r} formula={c.getFormula()!r} "
            f"number={c.getValue()}"
        )

    @mcp.tool()
    def calc_get_range(
        index: int,
        start: str,
        end: str,
        sheet: str | int | None = None,
    ) -> str:
        """Read a rectangular range as tab-separated rows.

        start/end: A1-style corners, e.g. 'A1' and 'C5'.
        """
        doc = _calc_doc(bridge, index)
        x1, y1 = _a1_to_xy(start)
        x2, y2 = _a1_to_xy(end)
        sh = _sheet(doc, sheet)
        rows = []
        for y in range(min(y1, y2), max(y1, y2) + 1):
            row = [
                sh.getCellByPosition(x, y).getString()
                for x in range(min(x1, x2), max(x1, x2) + 1)
            ]
            rows.append("\t".join(row))
        return "\n".join(rows)

    @mcp.tool()
    def calc_set_values(
        index: int,
        start: str,
        values: list[list[str]],
        sheet: str | int | None = None,
    ) -> str:
        """Bulk-fill a block of cells starting at `start`.

        values: rows of values; numbers are parsed numerically,
                strings starting with '=' become formulas, else text.
        """
        doc = _calc_doc(bridge, index)
        x0, y0 = _a1_to_xy(start)
        sh = _sheet(doc, sheet)
        n = 0
        for dy, row in enumerate(values):
            for dx, v in enumerate(row):
                c = sh.getCellByPosition(x0 + dx, y0 + dy)
                if isinstance(v, str) and v.startswith("="):
                    c.setFormula(v)
                else:
                    try:
                        c.setValue(float(v))
                    except (TypeError, ValueError):
                        c.setString(str(v))
                n += 1
        return f"Wrote {n} cell(s) starting at {start} in document [{index}]"

    @mcp.tool()
    def calc_list_sheets(index: int) -> str:
        """List sheet names in a Calc document."""
        doc = _calc_doc(bridge, index)
        return "\n".join(doc.Sheets.ElementNames)

    @mcp.tool()
    def calc_recalculate(index: int) -> str:
        """Force recalculation of all formulas in a Calc document."""
        doc = _calc_doc(bridge, index)
        doc.calculateAll()
        return f"Recalculated document [{index}]"
