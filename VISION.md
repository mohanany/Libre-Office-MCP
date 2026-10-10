# Libre-Office-MCP — Vision & Roadmap

## الرؤية / Vision

**Goal:** make LibreOffice the first office suite with a *native, per-application
MCP interface* — so any AI agent can drive Writer, Calc, Impress, Draw, Base and
Math with the same depth a human has through the GUI.

Not a script runner. Not a file converter. A **live, semantic interface** to the
running applications: documents, selections, styles, formulas, slides, shapes —
all as first-class MCP tools and resources.

## لماذا هذا المشروع / Why this exists

- MCP became the standard agent↔app protocol, but office suites are underserved:
  existing projects are either HTTP APIs mislabeled as MCP, or shallow
  Writer/Calc wrappers.
- LibreOffice is uniquely positioned: **UNO exposes ~everything** the GUI can
  do, in-process, with a mature Python bridge (PyUNO). No reverse engineering,
  no screen scraping.
- Nobody has shipped a *per-application* MCP surface for LO. That is the gap.

## قرار اللغة / The language decision

**Python stays the core.** Reasoning:

| Option | UNO access | MCP SDK | Packaging | Verdict |
|---|---|---|---|---|
| **Python (PyUNO)** | first-class, bundled in LO | official, mature | friction (system python) | ✅ core |
| C++ UNO | native | none real | hardest | ❌ dev cost |
| Java (juh) | full | weak ecosystem | JVM dep | ❌ |
| Go / Rust | **no UNO binding** — would need a Python sidecar anyway | good | single binary | ❌ as core |
| TypeScript | none | excellent | easy | ❌ no bridge |

Any "lighter" language still needs PyUNO underneath, so it only adds a layer.
The real problems are **packaging and distribution**, not the language — we
solve those at the packaging layer instead:

- `pipx install libreoffice-mcp` / `uv tool` for CLI users
- `.oxt` extension bundling its own interpreter path for GUI users
- later: a tiny launcher binary (Go/Rust) that just spawns the stdio server —
  UX improvement, not a rewrite

## البنية / Architecture (target)

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
                 │   auto-start + Tools▸MCP)    │   menus, status, settings
                 └──────────────────────────────┘
```

Principles:

1. **One bridge, many surfaces** — `OfficeBridge` owns the UNO connection;
   `apps/<app>.py` registers that app's tools; new apps = one file.
2. **Attach, don't own** — connect to a running LO when possible (user sees
   live edits); spawn headless only when nothing is running.
3. **Semantic tools, not macros** — tools map to concepts users think in
   (paragraphs, cells, slides), not raw UNO dumps.
4. **Per-app servers** — the same modules can be mounted as separate MCP
   server entries (`lo_mcp.writer`, `lo_mcp.calc`, …) so a client can enable
   only the apps it needs.

## المراحل / Roadmap

- **M1 — Core + two apps ✅ (done):** stdio server, UNO bridge with
  auto-spawn, common doc tools, Writer (6 tools), Calc (7 tools), tested with
  a real MCP client.
- **M2 — Full app coverage:** Impress (slides/layouts/shapes), Draw (shapes/
  layers/pages/export), Base (data sources/queries), Math (formula documents).
  Per-app server entry points + `pipx`-installable package.
- **M3 — `.oxt` extension:** installs inside LO; auto-opens the UNO socket;
  Tools ▸ MCP menu (enable/disable, port, status); zero manual flags. Publish
  on extensions.libreoffice.org.
- **M4 — Depth & resources:** MCP resources (`document://…`), selection/live
  cursor tools, event subscriptions (doc modified), richer style/template API,
  batch transactions.
- **M5 — Upstream path:** once adoption is real, propose to TDF — either
  bundled extension or a documented "AI integration" surface. Contribution via
  Gerrit only makes sense with a proven user base.
- **Always:** tests against real soffice (integration suite), docs, examples,
  a demo video.

## مكاننا من السوق / Position

- `patrup/mcp-libre`: embedded HTTP API (not true MCP), buggy on LO 26.x —
  we're upstream-compatible alternative.
- `krondor-corp/libre-mcp`: true stdio MCP, shallow coverage, external only —
  we go deeper + per-app + native extension.
- **Differentiator:** per-application surface + in-process extension + path to
  upstream. Nobody else is doing all three.

## القياس / Success looks like

- `pipx install libreoffice-mcp` + one config line → agent edits your open docs.
- Extension on the official LO extensions site.
- First external contributor / user report — then upstream conversation.
