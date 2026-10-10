"""Base (OfficeDatabaseDocument) tools — read/query level.

Operates on open .odb documents (embedded HSQLDB, or external data
sources configured in the document). Row results are capped for safety.
"""

from __future__ import annotations

from ..bridge import OfficeBridge

BASE_SVC = "com.sun.star.sdb.OfficeDatabaseDocument"
_MAX_ROWS = 500


def _base_doc(bridge: OfficeBridge, index: int):
    doc = bridge.get_document(index)
    if not doc.supportsService(BASE_SVC):
        raise ValueError(f"document [{index}] is not a Base document")
    return doc


def _connection(doc):
    ds = doc.DataSource
    try:
        conn = ds.getConnection("", "")
    except Exception:
        # prompt-less retry via interaction handler is intentionally skipped
        conn = ds.getConnection("", "")
    return conn


def register(mcp, bridge: OfficeBridge) -> None:

    @mcp.tool()
    def base_list_tables(index: int) -> str:
        """List tables in an open Base (.odb) document's data source."""
        doc = _base_doc(bridge, index)
        conn = _connection(doc)
        try:
            tables = conn.Tables
            names = list(tables.ElementNames)
        finally:
            conn.close()
        return "\n".join(names) if names else "No tables."

    @mcp.tool()
    def base_list_queries(index: int) -> str:
        """List stored queries in an open Base document."""
        doc = _base_doc(bridge, index)
        queries = doc.DataSource.QueryDefinitions
        names = list(queries.ElementNames)
        return "\n".join(names) if names else "No stored queries."

    @mcp.tool()
    def base_list_columns(index: int, table: str) -> str:
        """List column names of a table in an open Base document."""
        doc = _base_doc(bridge, index)
        conn = _connection(doc)
        try:
            tbl = conn.Tables.getByName(table)
            return "\n".join(tbl.Columns.ElementNames)
        finally:
            conn.close()

    @mcp.tool()
    def base_query(index: int, sql: str, max_rows: int = 100) -> str:
        """Run a SQL query against an open Base document's data source.

        sql: full SQL text (SELECT recommended; DDL/DML also executed).
        max_rows: cap on returned rows (default 100, hard max 500).
        Returns tab-separated rows with a header line.
        """
        doc = _base_doc(bridge, index)
        conn = _connection(doc)
        try:
            stmt = conn.createStatement()
            rs = stmt.executeQuery(sql)
            meta = rs.MetaData
            ncols = meta.ColumnCount
            header = "\t".join(
                meta.getColumnName(i + 1) for i in range(ncols)
            )
            rows = [header]
            limit = min(max_rows, _MAX_ROWS)
            n = 0
            while rs.next() and n < limit:
                rows.append(
                    "\t".join(
                        str(rs.getString(i + 1)) for i in range(ncols)
                    )
                )
                n += 1
            suffix = "" if n < limit else f"\n… truncated at {limit} rows"
            return "\n".join(rows) + suffix
        finally:
            conn.close()

    @mcp.tool()
    def base_execute(index: int, sql: str) -> str:
        """Execute a non-query SQL statement (DDL/DML) against the data source."""
        doc = _base_doc(bridge, index)
        conn = _connection(doc)
        try:
            stmt = conn.createStatement()
            stmt.execute(sql)
            return f"Executed on document [{index}]: {sql[:80]}"
        finally:
            conn.close()

    @mcp.tool()
    def base_info(index: int) -> str:
        """Show the data source URL/type of an open Base document."""
        doc = _base_doc(bridge, index)
        ds = doc.DataSource
        url = getattr(ds, "URL", "") or getattr(ds, "DatabaseLocation", "")
        return f"document [{index}] datasource: {url or '(unknown)'}"
