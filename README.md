# libreoffice-mcp

Native [Model Context Protocol](https://modelcontextprotocol.io) servers for
LibreOffice — one toolset per application (Writer, Calc, Impress, Draw, Base,
Math) on a shared UNO core, exposed to any MCP client over **stdio**.

## Architecture

```
MCP client (Claude, VS Code, …)
        │ stdio
        ▼
   python -m lo_mcp            ← FastMCP server, one process
        │ UNO socket (localhost:2002)
        ▼
   LibreOffice (soffice)       ← spawned automatically if not running
        │
        ├─ Writer  ── writer_* tools
        ├─ Calc    ── calc_* tools    (planned)
        ├─ Impress ── impress_* tools (planned)
        ├─ Draw    ── draw_* tools    (planned)
        └─ common  ── document_* / office_* tools
```

A single `OfficeBridge` owns the UNO connection; each `lo_mcp/apps/<app>.py`
module registers that application's tools. Adding a new app = one module.

## Requirements

- LibreOffice (`apt install libreoffice-writer libreoffice-calc …`)
- `python3-uno` (the UNO Python bridge — must import in the interpreter that runs the server)
- `pip install mcp>=1.10,<2.0` in that same interpreter

## Usage

```bash
cd libreoffice-mcp
PYTHONPATH=. /usr/bin/python3 -m lo_mcp     # stdio MCP server
```

MCP client config:

```json
{
  "mcpServers": {
    "libreoffice": {
      "command": "/usr/bin/python3",
      "args": ["-m", "lo_mcp"],
      "env": {"PYTHONPATH": "/path/to/libreoffice-mcp"}
    }
  }
}
```

Environment variables:

| Var | Default | Meaning |
|---|---|---|
| `LO_MCP_HOST` | `localhost` | UNO socket host |
| `LO_MCP_PORT` | `2002` | UNO socket port |
| `LO_MCP_GUI` | `0` | `1` = run soffice with visible GUI |
| `SOFFICE_BIN` | PATH lookup | explicit soffice binary path |

If LibreOffice is already running with
`--accept=socket,host=localhost,port=2002;urp;` the server attaches to it
(including your open documents); otherwise it spawns a headless instance.

## Tools (v0.1 — common + Writer)

Common: `office_status`, `document_list`, `document_open`, `document_save`,
`document_export`, `document_close`
Writer: `writer_create`, `writer_read_text`, `writer_insert_text`,
`writer_format_selection`, `writer_find_replace`, `writer_paragraph_count`

## Roadmap

- [ ] Calc module (cells, formulas, charts)
- [ ] Impress module (slides, masters, shapes)
- [ ] Draw module (shapes, layers, export)
- [ ] `.oxt` extension packaging (auto-start UNO socket inside LibreOffice,
      Tools ▸ MCP menu) — see `extension/`
- [ ] Publish on extensions.libreoffice.org
