# Task Tracker — Synapse

> Updated: 2026-09-22 · Week 1 (Sep 22–28), Personal AI Track + $3K Tavily side prize, deadline Oct 30 10:30pm GMT+5:30.
> Legend: `[x]` code-complete & locally verified · `[~]` code-complete, live verification pending · `[ ]` not started.
> Evidence paths are included so any box can be re-verified in seconds.

## Status Snapshot

- Plans/docs: DONE on paper (`.planning/PROJECT.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/MEMORY_SPEC.md`, `docs/DESIGN.md`, `docs/CONTEXT_LAYER.md`, `README.md` skeleton, `docs/RULES.md`).
- Core daemon: CODE-COMPLETE (`core/server.py`, `core/config.py`, `core/capture/*`, `core/engine/*`, `core/nebius/*`, `core/tools/*`, `core/doctor.py`). Sync tests pass (13 passed); 7 async tests skip without plugin autoload (see Blocked).
- Frontend: CODE-COMPLETE + BUILDS (`app/src/*`, `app/dist/index.html`, `src-tauri/target/release/synapse.exe`, MSI + NSIS bundles). `npm run build` passes; `tauri build` passes.
- Secrets: `.env` contains `NEBIUS_API_KEY`, `NEBIUS_PGVECTOR_URL`, `TAVILY_API_KEY` keys (values not verified here). `tavily-cli` installed via npm; CLI `auth set` + live search still to verify.
- Git: 1 commit on `main` (`d8b610f`), remote `origin/main` exists; current work (frontend, hook fixes, tauri scaffold) is MODIFIED/UNTRACKED — commit + push pending.

---

## Backlog (remaining work)

### Week 1 — Foundation (Sep 22–28)
- [ ] Verify Nebius $25 promo `NEBIUS-DEVPOST-GLOBAL26` credit landed (Nebius console → billing) — *user-side console check still open*
- [ ] Verify Builder Program +$25 (and Tavily credits) landed — *user-side console check still open*
- [x] Live-provision check: Nemotron Nano + Ultra Serverless Endpoints reachable from `core/nebius/client.py` (verified 2026-09-22, see Done → Live verification)
- [x] Live-provision check: PGVector instance reachable; `memory.connect()` + `memory.bootstrap()` + store/search round-trip OK (similarity 0.9034)
- [x] Live Nano inference smoke test (1 call: `pong`, 1691ms, 108 tokens, budget tracker updated)
- [ ] Benchmark PaddleOCR fallback accuracy on 3 samples (VS Code error, browser text, terminal) — record ms + accuracy
- [ ] Finish WinRT `_winrt_ocr` SoftwareBitmap conversion (currently placeholder in `core/capture/ocr.py:171-187`)
- [x] `tavily-cli auth set` + live search verify (token valid; `search query "NVIDIA Nemotron"` returned 10 scored results)
- [ ] Commit + push all current work (see Done → "Uncommitted" list); confirm `git status` clean

### Week 2 — Core Loop (Sep 29–Oct 5)
- [ ] Live E2E: `python core/server.py` + Tauri dev → trigger error on screen → overlay card appears
- [ ] Register global shortcut Ctrl+Shift+Space in `app/src-tauri/src/main.rs` → POST `/invoke` (plugin dep added, registration code missing)
- [ ] Verify WS heartbeat + auto-reconnect against live daemon (`useDaemonSocket` status transitions)
- [ ] Verify card actions live: Dismiss → SUPPRESSED, Apply Fix → clipboard, Save/store-memory → PGVector row
- [x] Fix pytest-asyncio config so async tests run (`pytest.ini` with `asyncio_mode = auto`; full suite 24 passed 2026-09-22 — canonical local cmd in `pytest.ini` header)

### Week 3 — Memory + Tavily (Oct 6–12)
- [ ] Live PGVector round-trip: store 1 memory → search returns it with similarity score
- [ ] Live Tavily round-trip: query → results → `~/synapse_notes/<slug>.md` file created → path shown on card
- [ ] Build toast notification for saved research (UI component missing)
- [ ] Build memory browser panel, collapsible (UI component missing)
- [ ] Tune proactive trigger thresholds (suppression 60s, emit ≥60) against real usage; log false-positive rate

### Week 4 — Polish (Oct 13–19)
- [ ] UI refinement pass per `docs/DESIGN.md` §4 (hover/active states, transitions ≤250ms)
- [ ] Direct editor bridge for Apply Fix (beyond clipboard injection) — or lock clipboard as final
- [ ] Card footer: model + latency + spend/remaining (wired in `SynapseCard.tsx`, verify with live `usage` payload)
- [ ] Full E2E test of all 4 user flows (Proactive error, Clipboard error, Manual invoke, Tavily research)
- [ ] Record raw demo clips (iterative, weekly)

### Week 5 — Ship (Oct 20–26)
- [ ] Final README: setup guide + "How we used NVIDIA + Nebius" + Mermaid diagram
- [ ] One-command setup verify on clean machine: `pip install -r core/requirements.txt` + `npm run tauri build` + `python core/server.py`
- [ ] Demo video final edit (30s problem / 90s demo / 60s tech), ≤3 min
- [ ] Upload to YouTube (unlisted → public on submit)
- [ ] Devpost submission: description, video URL, repo link, Nebius/NVIDIA feedback text

### Buffer (Oct 27–30)
- [ ] Final bug sweep + non-negotiable checklist (PRD §Non-Negotiable, 7 items)
- [ ] Submit by Oct 30 10:30pm GMT+5:30

---

## In Progress (code-complete, live verification pending)

- [x] Nebius endpoints + PGVector instance — LIVE VERIFIED 2026-09-22 (see Done → Live verification)
- [x] Nano → Ultra routing — LIVE VERIFIED 2026-09-22 (Nano `pong` + Ultra NameError answer, spend tracked)
- [x] Tavily pipeline — LIVE VERIFIED 2026-09-22 (Python: 5 results + MD saved to `~/synapse_notes/`; CLI: token valid + 10-result search)
- [~] IPC bridge daemon↔UI — code done (`core/server.py` `/ws` `/invoke` `/action/*` + `app/src/hooks/useDaemonSocket.ts` fixed); joint live run unverified
- [~] Overlay card actions — Dismiss/Apply wired (`SynapseCard.tsx` + `server.py:198-230`); live behavior unverified
- [~] OCR engine — polling + diff + PaddleOCR fallback done (`core/capture/ocr.py`, `tests/test_ocr.py`); WinRT fast path is placeholder (see Blocked)

---

## Done (verified this session unless noted)

### Plans / Docs
- [x] `.planning/PROJECT.md` — vision/scope/risks/budget locked (39 days, Personal AI + Tavily)
- [x] `docs/PRD.md` — requirements, user stories, success metrics, non-negotiables
- [x] `docs/ARCHITECTURE.md`, `docs/MEMORY_SPEC.md`, `docs/CONTEXT_LAYER.md`, `docs/DESIGN.md`, `docs/CONCEPT.md`, `docs/RULES.md`
- [x] `README.md` skeleton + `LICENSE` (MIT) exist

### Core daemon
- [x] `core/server.py` — FastAPI + WS `/ws`, REST `/health` `/invoke` `/action/*` `/usage`, startup wiring
- [x] `core/config.py` — settings + `.env` loading + validation
- [x] `core/requirements.txt` — installs clean after `paddlepaddle 2.6.1 → 2.6.2` fix
- [x] `core/capture/clipboard.py` — Win32 message-only listener, classification
- [x] `core/capture/ocr.py` — polling + hash-diff + PaddleOCR fallback (WinRT fast path TODO)
- [x] `core/capture/process_watcher.py` — focus duration, switch frequency, stuck/deep-work signals
- [x] `core/capture/filesystem.py` — watchdog project detection + recent files
- [x] `core/engine/aggregator.py` — trigger scoring (emit ≥60), suppression 60s, bundle builder
- [x] `core/engine/state_machine.py` — IDLE→CAPTURING→REASONING→READY→SUPPRESSED FSM
- [x] `core/engine/redaction.py` — PII scrub before cloud (tests pass)
- [x] `core/nebius/client.py` — Nano/Ultra/embed via OpenAI-compatible endpoint, retries, budget tracker
- [x] `core/nebius/router.py` — Nano triage JSON → Nano/Ultra/Tavily/Ignore + relevance gate 55
- [x] `core/nebius/memory.py` — PGVector DDL, store, vector search, profiles
- [x] `core/tools/tavily_search.py` — search + Markdown compile + `~/synapse_notes` auto-save
- [x] `core/tools/file_patcher.py` — unified-diff apply with backup + traversal guard
- [x] `core/doctor.py`, `scripts/setup_env.bat`, `tests/test_*.py` (4 files) exist
- [x] Full test suite: 24 passed (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests -q -p asyncio -p no:cacheprovider`)
- [x] `pytest.ini` (`asyncio_mode = auto`) + `.github/workflows/ci.yml` (backend pytest + frontend `npm run build`)
- [x] `core/doctor.py` rewritten on project conventions (keys via `core.config`, DB via asyncpg, Nebius via `NEBIUS_BASE_URL`); `python -m core.doctor` all-green (pgvector v0.8.6, 1 memory, dim 4096, Nebius reachable); root `test_db.py` folded in and deleted
- [x] Merge conflict resolved in `core/nebius/router.py` (3 hunks, kept 3432999 side: `import time` + `ultra_t0` + telemetry `logger.info` blocks) — found because the suite failed collection on it
- [x] `core/server.py` truncation repaired — a truncated 83-line rewrite (valid syntax, zero functionality) replaced the full daemon; restored 321-line version from `3432999` (lifespan, `synapse_chunk` streaming, FilePatcher apply-fix, all routes). Merge `70f2f23` committed by user; tree conflict-free
- [x] `tests/test_server_smoke.py` — regression guard: app object, 7 required routes, 11 pipeline/entry symbols, FSM states (suite now 28 passed)
- [x] Daemon boot fixes (found live 2026-09-22): repo-root `sys.path` bootstrap in `server.py` so `python core/server.py` works (was `No module named 'core'`); `win32gui.GetWindowThreadProcessId` → `win32process` in `process_watcher.py:126` + `ocr.py:104` (was killing the focus watcher on first poll). Boot verified: `Application startup complete`, Uvicorn on :8420
- [x] `tauri dev` EBUSY fix: Vite watcher crashed on `src-tauri/target/**/*.dll` during cargo compile — `vite.config.ts` now ignores `**/src-tauri/**` + `**/target/**` (build verified, 24 modules)
- [x] `src-tauri/src/main.rs` fix: `get_webview_window` needs `use tauri::Manager;` (E0599 broke dev compile; `cargo check` passes now)
- [x] Lane 2 live bugs (E2E fired, pipeline aborted REASONING→IDLE): `win32con.WM_CLIPBOARDUPDATE` doesn't exist in pywin32 — defined `0x031D` constant in `clipboard.py` (was killing fast lane on every clipboard change); Nano triage returned EMPTY with `max_tokens=256` (endpoint quirk, verified live) — bumped to 1024 + added fence-tolerant `_parse_triage_json` + 5 unit tests (suite 33 passed)
- [x] Daemon 500s root-caused from user boot log: `server.py` used `logger.info` with no `logger` defined (3432999 dropped the init) — added `setup_logging()` + module logger; clipboard thread called `asyncio.create_task` with no running loop — added `_main_loop` capture + `run_coroutine_threadsafe` bridge (`_on_clipboard_threadsafe`). Smoke test extended to guard both
- [x] Repo hygiene: `scripts/start.bat` (daemon + UI launcher), README mermaid diagram + `doctor` step + corrected pytest/live-test snippets, `.pre-commit-config.yaml` (ruff), UI `OFFLINE — LOCAL MODE` badge in `StatusIndicator`

### Frontend (builds verified)
- [x] `app/package.json` + `vite.config.ts` + `tsconfig.json` — `npm run build` passes (23 modules, `dist/index.html` emitted)
- [x] `app/src/main.tsx`, `app/src/App.tsx` (landing ↔ app switch, card + status wiring)
- [x] `app/src/components/landing/NeuronSphere.tsx` — Three.js 200-particle sphere, pulses, parallax, click cascade
- [x] `app/src/components/landing/HeroText.tsx`, `FeatureCards.tsx` — DESIGN.md hero + hardware cards
- [x] `app/src/components/hud/SynapseCard.tsx` — overlay card (header/meta/response/Tavily footer) + loading pulse
- [x] `app/src/components/shared/Button.tsx`, `app/src/types/index.ts`, `app/src/styles/theme.css` (NVIDIA palette + hw-card + CTA + card CSS)
- [x] `app/src/hooks/useDaemonSocket.ts` — P0–P2 fixes: `optsRef`, heartbeat/reconnect cleanup, `mountedRef`, AbortSignal, discriminated-union messages, exponential backoff + jitter, env URLs, `status` tri-state
- [x] `app/src-tauri/` — `tauri.conf.json`, `Cargo.toml`, `build.rs`, `src/main.rs`, `icons/`; `npm run tauri build` produces `target/release/synapse.exe` + MSI + NSIS bundles

### Tooling / Env
- [x] `tavily-cli` installed via npm (runs as `npx tavily-cli`); `gh` CLI on PATH (v2.101.0)
- [x] `.env` keys present: `NEBIUS_API_KEY`, `NEBIUS_PGVECTOR_URL`, `TAVILY_API_KEY`
- [x] Initial commit `d8b610f` on `main` with `origin/main` remote

### Live verification (2026-09-22, Lane 1)
- [x] Nano smoke: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` → `pong`, 1691ms, 108 tokens, `nano_calls=1`, spend $0.0
- [x] Ultra smoke: `nvidia/Nemotron-3-Ultra-550b-a55b` → correct 1-sentence NameError answer, 3012ms, 107 tokens, spend $0.0002, remaining $49.9998
- [x] PGVector: `connect` + `bootstrap` OK; store-1/search-1 round-trip hit at similarity 0.9034. Note: `[Memory] HNSW index skipped (column cannot have more than 2000 dimensions)` — exact search used, fine at hackathon scale
- [x] Tavily Python: 5 results + compiled MD saved to `~/synapse_notes/20260922_2029_python-nameerror-common-causes.md` (4584ms)
- [x] Tavily CLI: `auth set` (from `.env` key, never printed) → `auth test` "Token is valid"; `search query "NVIDIA Nemotron"` → 10 scored results (top 0.9403)
- [x] Gotcha recorded: smoke scripts MUST `import core.config` first — importing `core.nebius.client` alone never loads `.env` (`ValueError: NEBIUS_API_KEY not found` otherwise)

### Uncommitted (commit + push pending — from `git status` 2026-09-23)
- Modified: `README.md`, `app/src/App.tsx`, `core/doctor.py`, `docs/TASKS.md`; deleted: `test_db.py`
- Untracked: `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `pytest.ini`, `scripts/start.bat`, `tests/test_server_smoke.py`
- Branch `main` is ahead of `origin/main` by 2 commits (merge `70f2f23` + local work) — push needs explicit user approval

---

## Blocked

- **Plain `pytest` still crashes before collection (env pollution, not repo)** — `deepeval` plugin + `pydantic-settings` conflict (`SettingsError: TEMPERATURE`). Canonical local command (verified 24 passed): `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests -q -p asyncio -p no:cacheprovider` (also in `pytest.ini` header). CI is unaffected (fresh env, no deepeval).
- **WinRT OCR fast path is a stub** — `core/capture/ocr.py:_winrt_ocr` returns `""` (SoftwareBitmap conversion TODO). PaddleOCR fallback carries OCR until this is implemented. Unblock: implement WinRT imaging bridge or lock PaddleOCR as primary and note latency in README.
- **Nebius billing console unchecked** — endpoints + PGVector verified live (2026-09-22), but promo/Builder credit balances still need a user-side Nebius console → billing check before load testing.
- **Nano latency 1691ms vs 300ms triage target** — live Nano call works but misses the `<300ms` PRD target; Ultra 3012ms vs `<4s` target is inside. Unblock: profile (cold start vs steady state), consider shorter `max_tokens` / streaming for triage path.
- **Tauri global shortcut unwired** — `tauri-plugin-global-shortcut` in `Cargo.toml` but no `Ctrl+Shift+Space` registration in `src/main.rs`. Manual `/invoke` works; shortcut pending.
- **Joint daemon+UI run unverified** — both sides build independently; no live WS session recorded yet.
