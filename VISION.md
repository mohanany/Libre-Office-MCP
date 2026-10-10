# Libre-Office-MCP — Vision, Language Decision & Full Plan

## 1. Vision

**Goal:** make LibreOffice the first office suite with a *native,
per-application MCP interface* — so any AI agent can drive Writer, Calc,
Impress, Draw, Base and Math with the same depth a human has through the GUI.

Not a script runner. Not a file converter. A **live, semantic interface** to
the running applications: documents, selections, styles, formulas, slides,
shapes — all as first-class MCP tools and resources.

## 2. Why this project exists

- MCP is becoming the standard agent↔app protocol, but office suites are
  underserved: existing projects are either HTTP APIs mislabeled as MCP, or
  shallow Writer/Calc wrappers.
- LibreOffice is uniquely positioned: **UNO exposes nearly everything** the
  GUI can do, in-process, through a mature Python bridge (PyUNO). No reverse
  engineering, no screen scraping.
- Nobody has shipped a *per-application* MCP surface for LO. That is the gap.

## 3. Language decision

**Python remains the core.** Reasoning:

| Option | UNO access | MCP SDK | Packaging | Verdict |
|---|---|---|---|---|
| **Python (PyUNO)** | first-class, bundled with LO | official, mature | some friction (system python) | ✅ core |
| C++ UNO | native | none real | hardest | ❌ dev cost |
| Java (juh) | full | weak ecosystem | JVM dep | ❌ |
| Go / Rust | **no UNO binding** — would need a Python sidecar anyway | good | single binary | ❌ as core |
| TypeScript | none | excellent | easy | ❌ no bridge |

Any "lighter" language still needs PyUNO underneath, so it only adds a layer.
The real problems are **packaging and distribution**, not the language — we
solve those at the packaging layer instead:

- `pipx install libreoffice-mcp` / `uv tool install` for CLI users
- `.oxt` extension that locates the right interpreter for GUI users
- optionally later: a tiny launcher binary (Go/Rust) that just spawns the
  stdio server — a UX improvement, not a rewrite

**Revisit trigger:** if PyUNO blocks a requirement (e.g. threading limits,
performance at scale, embedded interpreter inside .oxt proves unworkable),
re-evaluate a Java UNO component or C++ extension then — with data.

## 4. Target architecture

```
                 ┌──────────────────────────────┐
   MCP clients   │  libreoffice-mcp (stdio)     │   one process per client
   (Claude, VS   │  FastMCP server              │
    Code, …)     │                              │
                 │   core: OfficeBridge         │   UNO socket ↔ soffice
                 │   apps/ writer|calc|impress  │   per-app tool modules
                 │         draw|base|math       │
                 └──────────────┬───────────────┘
                                │ UNO
                 ┌──────────────▼───────────────┐
                 │  LibreOffice                 │
                 │  (.oxt extension — optional  │   auto-opens the socket,
                 │   auto-start + Tools ▸ MCP)  │   menus, status, settings
                 └──────────────────────────────┘
```

Design principles:

1. **One bridge, many surfaces** — `OfficeBridge` owns the UNO connection;
   `apps/<app>.py` registers that app's tools; a new app is one new file.
2. **Attach, don't own** — connect to a running LO when possible (the user
   watches live edits); spawn headless only when nothing is running.
3. **Semantic tools, not macros** — tools map to concepts users think in
   (paragraphs, cells, slides), not raw UNO dumps.
4. **Per-app servers** — the same modules can be mounted as separate MCP
   server entries so a client can enable only the apps it needs.

## 5. Roadmap

### M1 — Core + first two apps ✅ done
- stdio MCP server (`python -m lo_mcp`), `OfficeBridge` with auto-spawn and
  attach modes, common document tools (6), Writer module (6 tools), Calc
  module (7 tools), verified end-to-end with a real MCP client.
- Repository published at github.com/mohanany/Libre-Office-MCP.

### M2 — Full application coverage *(current)*
- Impress module: slides, layouts, masters, shapes, notes.
- Draw module: pages, shapes, layers, connectors, export.
- Base module: data sources, tables, queries (read-level first).
- Math module: formula documents (basic create/edit/export).
- Per-app entry points: `lo_mcp.writer`, `lo_mcp.calc`, … mountable as
  separate MCP servers.
- Packaging: PyPI-ready `pyproject`, `pipx`/`uv` install path, console
  scripts `libreoffice-mcp` and `libreoffice-mcp-<app>`.

### M3 — `.oxt` extension
- Extension installs inside LibreOffice; opens the UNO acceptor on startup
  (no `--accept` flag needed).
- Tools ▸ MCP menu: enable/disable, port, status indicator.
- Bundled or detected interpreter strategy for the stdio server.
- Published on extensions.libreoffice.org.

### M4 — Depth
- MCP resources: `document://…` URIs for open documents.
- Selection/live-cursor tools; event subscriptions (document modified,
  selection changed).
- Style/template API, named ranges, comments/tracked changes.
- Batch transactions (group UNO ops to reduce round-trips).

### M5 — Upstream path
- With real adoption, approach TDF: bundled extension or a documented
  AI-integration surface. Gerrit contribution only once the user base
  justifies it.

### Continuous
- Integration test suite against a real soffice (CI where possible).
- Docs, examples, demo video, compatibility matrix across LO versions
  (24.x, 25.x, 26.x).

## 6. Competitive position

- `patrup/mcp-libre`: embedded HTTP API (not true MCP protocol), open bugs
  on LO 26.x — we are the protocol-correct alternative.
- `krondor-corp/libre-mcp`: true stdio MCP, but shallow coverage and
  external-only — we go deeper, per-app, and native.
- **Differentiator:** per-application surface + in-process extension +
  credible upstream path. Nobody else combines all three.

## 7. Definition of success

- `pipx install libreoffice-mcp` + one config line → an agent edits your
  open documents.
- Extension listed on the official LibreOffice extensions site.
- First external user/contributor — then the upstream conversation starts.
