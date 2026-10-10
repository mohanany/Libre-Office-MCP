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

## Tools (v0.1 — 45 tools)

| App | Tools |
|---|---|
| Common | `office_status` `document_list` `document_open` `document_save` `document_export` `document_close` |
| Writer | `writer_create` `writer_read_text` `writer_insert_text` `writer_format_selection` `writer_find_replace` `writer_paragraph_count` |
| Calc | `calc_create` `calc_set_cell` `calc_get_cell` `calc_get_range` `calc_set_values` `calc_list_sheets` `calc_recalculate` |
| Impress | `impress_create` `impress_slide_count` `impress_add_slide` `impress_delete_slide` `impress_set_slide_layout` `impress_set_slide_text` `impress_get_slide_text` `impress_set_slide_notes` `impress_list_shapes` |
| Draw | `draw_create` `draw_page_count` `draw_add_page` `draw_add_shape` `draw_list_shapes` `draw_set_shape_text` `draw_list_layers` |
| Base | `base_list_tables` `base_list_queries` `base_list_columns` `base_query` `base_execute` `base_info` |
| Math | `math_create` `math_set_formula` `math_get_formula` `math_export_mathml` |

## Per-app servers

Run only one application's toolset (+ common tools):

```bash
python -m lo_mcp calc        # or writer / impress / draw / base / math
```

or via installed console scripts: `libreoffice-mcp-calc`, etc.

## `.oxt` extension

`extension/` builds `libreoffice-mcp-bridge.oxt`
(`scripts/build_oxt.sh`, install with `unopkg add`). A Basic macro bound to
`OnStartApp` opens the UNO acceptor (`localhost:2002`) inside LibreOffice at
startup — no `--accept=` flag needed, so the stdio server can attach to the
running instance and its open documents.

## Roadmap

- [x] Writer, Calc, Impress, Draw modules
- [x] Base module (read/query via SDBC), Math module
- [x] Per-app MCP server entries
- [x] `.oxt` extension (auto-opens UNO socket at startup)
- [ ] Tools ▸ MCP menu (enable/disable, port, status)
- [ ] Publish on extensions.libreoffice.org
