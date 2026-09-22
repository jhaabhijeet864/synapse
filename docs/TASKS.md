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
- [ ] Verify Nebius $25 promo `NEBIUS-DEVPOST-GLOBAL26` credit landed (Nebius console → billing)
- [ ] Verify Builder Program +$25 (and Tavily credits) landed
- [ ] Live-provision check: Nemotron Nano + Ultra Serverless Endpoints reachable from `core/nebius/client.py`
- [ ] Live-provision check: PGVector instance reachable; run `memory.connect()` + `memory.bootstrap()` against real `NEBIUS_PGVECTOR_URL`
- [ ] Live Nano inference smoke test (1 call, log latency + tokens, confirm budget tracker updates)
- [ ] Benchmark PaddleOCR fallback accuracy on 3 samples (VS Code error, browser text, terminal) — record ms + accuracy
- [ ] Finish WinRT `_winrt_ocr` SoftwareBitmap conversion (currently placeholder in `core/capture/ocr.py:171-187`)
- [ ] `tavily-cli auth set` + `tavily-cli search "test" --json` live verify
- [ ] Commit + push all current work (see Done → "Uncommitted" list); confirm `git status` clean

### Week 2 — Core Loop (Sep 29–Oct 5)
- [ ] Live E2E: `python core/server.py` + Tauri dev → trigger error on screen → overlay card appears
- [ ] Register global shortcut Ctrl+Shift+Space in `app/src-tauri/src/main.rs` → POST `/invoke` (plugin dep added, registration code missing)
- [ ] Verify WS heartbeat + auto-reconnect against live daemon (`useDaemonSocket` status transitions)
- [ ] Verify card actions live: Dismiss → SUPPRESSED, Apply Fix → clipboard, Save/store-memory → PGVector row
- [ ] Fix pytest-asyncio config so async tests run in normal `pytest` (see Blocked)

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

- [~] Nebius endpoints + PGVector instance — code done (`core/nebius/client.py`, `core/nebius/memory.py`), `.env` keys present; live reachability unverified
- [~] Nano → Ultra routing — code done (`core/nebius/router.py`, `tests/test_nebius_routing.py` sync pass); live inference unverified
- [~] Tavily pipeline — code done (`core/tools/tavily_search.py` search + compile + auto-save); live API call + file save unverified
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
- [x] Sync test suite: 13 passed (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests -q -p no:cacheprovider`)

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

### Uncommitted (commit + push pending — from `git status`)
- Modified: `.env.example`, `app/src/hooks/useDaemonSocket.ts`, `app/src/styles/theme.css`, `core/capture/ocr.py`, `core/config.py`, `core/engine/redaction.py`, `core/nebius/client.py`, `core/nebius/memory.py`, `core/requirements.txt`, `docs/MEMORY_SPEC.md`
- Untracked: `app/index.html`, `app/package.json`, `app/package-lock.json`, `app/src-tauri/`, `app/src/App.tsx`, `app/src/components/`, `app/src/main.tsx`, `app/src/vite-env.d.ts`, `app/tsconfig*.json`, `app/vite.config.ts`, `core/doctor.py`, `test_db.py`, `tests/test_redaction.py`

---

## Blocked

- **pytest default run crashes before collection** — `deepeval` plugin + `pydantic-settings` conflict (`SettingsError: TEMPERATURE`). Workaround (verified): `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests -q -p no:cacheprovider` → 13 passed, 7 async skipped. Unblock: add `pytest-asyncio` explicit config (`asyncio_mode = "auto"` in `pytest.ini`/`pyproject`) or run with `-p asyncio`, then re-run full suite.
- **WinRT OCR fast path is a stub** — `core/capture/ocr.py:_winrt_ocr` returns `""` (SoftwareBitmap conversion TODO). PaddleOCR fallback carries OCR until this is implemented. Unblock: implement WinRT imaging bridge or lock PaddleOCR as primary and note latency in README.
- **Nebius live calls unverified** — endpoints, credits, PGVector reachability unknown from repo alone. Unblock: Nebius console check + 1 live Nano call + `memory.bootstrap()` run.
- **Tavily CLI auth unverified** — earlier `auth test` → "No token configured". `.env` key now present per user; CLI-side `auth set` + live search still to confirm.
- **Tauri global shortcut unwired** — `tauri-plugin-global-shortcut` in `Cargo.toml` but no `Ctrl+Shift+Space` registration in `src/main.rs`. Manual `/invoke` works; shortcut pending.
- **Joint daemon+UI run unverified** — both sides build independently; no live WS session recorded yet.
