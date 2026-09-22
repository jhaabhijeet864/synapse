# Task Tracker — Synapse

## Backlog

### Week 1 — Foundation (Sep 22–28)
- [ ] Claim Nebius $25 promo `NEBIUS-DEVPOST-GLOBAL26`
- [ ] Sign up for Nebius Builder Program (additional $25)
- [ ] Initialize GitHub repo with MIT license + README skeleton
- [ ] Provision Nemotron Nano + Ultra Serverless Endpoints on Nebius
- [ ] Set up PGVector instance on Nebius Token Factory
- [ ] Define PGVector schema (MemoryEntry model)
- [ ] PoC: Windows OCR API capturing active window text
- [ ] PoC: PaddleOCR as fallback, benchmark accuracy
- [ ] PoC: Nemotron Nano endpoint — test basic inference call
- [ ] Set up Python 3.11 project structure (FastAPI backend)
- [ ] Windows Credential Manager integration for API key storage

### Week 2 — Core Loop (Sep 29–Oct 5)
- [ ] OCR monitor thread (polls active window every 5s, diff detection)
- [ ] Context aggregator: merge OCR + OS context (active app, window title)
- [ ] Nano router: classify intent → route to Nano or Ultra
- [ ] Ultra reasoning call: generate response + code diff if applicable
- [ ] Tauri project scaffold + React overlay card component
- [ ] IPC bridge: FastAPI ↔ Tauri communication
- [ ] End-to-end: error on screen → card with fix appears
- [ ] Card actions: Dismiss, Copy, basic "Apply"

### Week 3 — Memory + Tavily (Oct 6–12)
- [ ] PGVector memory write: store each session's OCR context + embedding
- [ ] PGVector memory read: semantic search for relevant past context
- [ ] Memory integration in reasoning pipeline (inject into Ultra prompt)
- [ ] Tavily integration: trigger search when memory gap detected
- [ ] Tavily auto-save: results → `~/synapse_notes/topic-name.md`
- [ ] Proactive trigger logic: detect meaningful screen events
- [ ] Toast notification for saved research
- [ ] Memory browser panel (collapsible UI component)

### Week 4 — Polish (Oct 13–19)
- [ ] UI refinement: full color palette, glassmorphism card, motion
- [ ] One-click "Apply Fix" (clipboard injection or direct editor bridge)
- [ ] Credit-aware routing display (model used + latency in card footer)
- [ ] End-to-end testing: all 4 user flows working
- [ ] Demo video recording (raw clips, iterative)
- [ ] README first draft with architecture diagram

### Week 5 — Ship (Oct 20–26)
- [ ] Final README: setup guide, "How we used NVIDIA + Nebius" section
- [ ] Mermaid architecture diagram in README
- [ ] One-command setup: `pip install -e . && python synapse.py`
- [ ] Demo video final edit (30s problem / 90s demo / 60s tech)
- [ ] Upload demo video to YouTube (unlisted → public on submit)
- [ ] Devpost submission: description, video, repo link, feedback
- [ ] Submit Nebius Token Factory feedback

### Buffer (Oct 27–30)
- [ ] Final bug sweep
- [ ] Verify all non-negotiable requirements are met
- [ ] Submit by Oct 30 10:30pm GMT+5:30

---

## In Progress
<!-- Move tasks here when actively working on them -->

---

## Done
- [x] CONCEPT.md — product concept locked (Synapse)
- [x] PROJECT.md — updated with Synapse vision
- [x] PRD.md — full product requirements documented
- [x] ARCHITECTURE.md — system architecture defined
- [x] DESIGN.md — UI/UX design system defined

---

## Blocked
<!-- Add blocked tasks with reason and unblocking condition -->