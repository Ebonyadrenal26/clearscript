# Changelog

All notable changes to clearscript will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.3] - 2026-04-25

### Added — the library is alive

- **Library tab in the web UI** with three sub-tabs (Terms / Speakers / Edit patterns), each with a sortable table, search, type/status/domain filters, an inline add form, and per-row delete. Status rendered with Bauhaus-colored dots.
- **Library stats strip** at the top of the Library tab: 8 metric cards (terms / verified / confirmed / proposed / speakers / patterns / negatives / sessions).
- **Mode A (project-start activation)**: the briefing field is scanned for entity tokens (CamelCase, acronyms, CJK names) and each is looked up in the library; matches inject "Term mappings from your library" and "Briefing speakers" sections into the LLM system prompt. `lookup_alias` now also matches by canonical, not just aliases.
- **Mode B (end-of-session harvest)**: the layered-edit prompt now produces a `---SUGGESTIONS---` block alongside `---CHANGELOG---`. Pipeline parses it into `EditResult.suggestions`. The web UI displays a yellow panel after each run with checkboxes; "Accept selected → library" bulk-writes to terms / speakers / patterns.

### Added — Library class API

- `list_terms(type_, domain, status, search, limit)` — filtered listing including all aliases per row
- `update_term(id, ...)` and `delete_term(id)`
- `list_speakers(search, limit)`, `update_speaker`, `delete_speaker`
- `list_edit_patterns(domain)`, `add_edit_pattern(...)`, `delete_edit_pattern(id)`
- `add_negative(text, do_not_change_to, domain, reason)` (NULL-safe dedupe), `list_negatives()`
- Expanded `stats()`: now includes `verified_terms`, `confirmed_terms`, `proposed_terms`, `edit_patterns`, `negative_rules`

### Added — Server API

- `GET /api/library/stats`
- `GET /api/library/terms` (with `type`, `domain`, `status`, `search`, `limit` query params)
- `POST /api/library/terms`, `PATCH /api/library/terms/{id}`, `DELETE /api/library/terms/{id}`
- `GET /api/library/speakers`, `POST`, `PATCH`, `DELETE`
- `GET /api/library/patterns`, `POST`, `DELETE`
- `POST /api/library/accept-suggestions` — bulk write Mode B suggestions

### Changed

- All Pydantic request models lifted to module level so FastAPI can introspect them as request bodies (was: nested in `create_app`, dropped to query params)
- `TxtAdapter.parse_string()` already public from v0.0.2 — no change here; documenting that web UI uses it for in-memory input
- Bumped version to `0.0.3`

### Tests

- 17 new unit tests covering: term filtering by type/status/search, term update/delete, speaker listing/search, edit-pattern lifecycle, negative-list NULL-safe dedupe, expanded stats schema, suggestions parsing, briefing entity extraction (CJK + CamelCase + acronyms), Mode A end-to-end, fenced-JSON parsing
- Total: 44 tests, all passing

## [0.0.2] - 2026-04-25

### Added

- **Local web UI** at `http://127.0.0.1:7681`, launched via `clearscript serve`
  - Bauhaus-styled single-page app (Tailwind via CDN, Outfit font, hard offset shadows, primary color blocking)
  - Provider pill selector with live API-key detection
  - Drag-drop / paste / file-upload transcript input
  - Per-run stats (input tokens, output tokens, change count, latency)
  - Inline change-log accordion
  - One-click download as `.md` or `.docx`, one-click clipboard copy
  - "Load example" button for first-run users
  - Cmd/Ctrl+Enter keyboard shortcut to trigger a run
- FastAPI backend with JSON API: `/api/health`, `/api/providers`, `/api/run`, `/api/export/docx`, `/api/example`
- Auto-open browser on `clearscript serve` (suppress with `--no-open`)
- `TxtAdapter.parse_string()` public method for in-memory input

### Changed

- Server binds to `127.0.0.1` only by default (no network exposure unless explicitly opted in)
- `clearscript` package version bumped to `0.0.2`

### Planned for v0.1.0

- Full pipeline (Ingest → Pre-scan → Context Briefing → L1-L6 + L3.5 → Self-review → Batch-ask → Re-scan → Export)
- 12 ASR input formats
- 5 LLM provider adapters covering 20+ services
- SvelteKit web UI with Bauhaus design system
- Library Mode A (project-start activation) and Mode C (in-flight learning)
- Markdown + DOCX + JSON + SRT export
- PyInstaller-packaged desktop installers (.app, .exe, .AppImage)
- Bilingual documentation (English + Simplified Chinese)
- GitHub Actions CI

## [0.0.1] - 2026-04-25

### Added

- Initial repository scaffold with `uv` project layout
- Core directory structure: `src/clearscript/{core,ingest,providers,library,layers,export,storage,prompts}`
- Desensitized prompt library ported from the original personal Claude skill
- LLM provider abstraction with `anthropic` adapter
- `txt` ingest parser
- Markdown exporter
- Minimal CLI (`clearscript run <input>`)
- SQLite library schema
- Bauhaus design system specification
- README in English and Simplified Chinese
- MIT License
- Roadmap and architecture documentation
