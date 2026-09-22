# Project Overview

## Vision

Build **Synapse** — a privacy-first, always-on desktop AI layer that runs natively on Windows. Synapse watches your screen, remembers your work across sessions, researches the web via Tavily, and surfaces exactly the right answer through Nemotron reasoning on Nebius — all before you even ask.

> *"The AI that lives between your brain and your computer."*

**Winning Target:** Personal AI Track → $20,000 Grand Prize (or NVIDIA Jetson Orin Nano) + $3,000 Tavily Best Use side prize.

---

## Scope

### In Scope
- Screen-aware OCR context capture (active window, live error reading, unselectable text)
- Hybrid local↔cloud architecture: local OS integration + cloud reasoning via Nebius Serverless Endpoints
- Smart routing: Nemotron Nano (triage/fast calls) + Nemotron 3 Ultra (heavy reasoning)
- Persistent vector memory: PGVector on Nebius Token Factory (work patterns, preferences, session history)
- Tavily web research → auto-save results to local filesystem (PDF/Markdown)
- Floating native desktop overlay UI (Tauri + React) — polished product feel
- Python 3.11 backend (FastAPI) orchestrating the full tool pipeline
- Windows OS integration (pywin32 + uiautomation) for active window detection
- Public GitHub repo with MIT license, comprehensive README, architecture diagrams
- 3-minute demo video showcasing the "wow moment" + Nebius/NVIDIA integration explanation

### Out of Scope
- Voice input (Vosk/Whisper) — added only if Week 3 is ahead of schedule
- Gesture invocation (MediaPipe) — too risky for solo 39-day build
- Hermes Agent / NemoClaw framework — replaced by lightweight custom tool routing
- Mobile app / web-only interface
- Training/fine-tuning models (using pre-trained Nemotron only)
- Physical hardware/robotics
- Multi-user SaaS platform (single-user, local-first)
- Multi-monitor support (stretch goal)

---

## Stakeholders

| Role | Entity | Interest |
|------|--------|----------|
| **Builder** | Me (solo) | Win hackathon, showcase portfolio, learn Nebius/NVIDIA stack |
| **Platform Sponsor** | Nebius | Demonstrate Token Factory + Serverless capabilities |
| **Model Sponsor** | NVIDIA | Showcase Nemotron 3 Ultra/Nano on open infrastructure |
| **API Partner** | Tavily | Drive adoption via $3K Best Use prize |
| **Judges** | Devpost panel | Evaluate: Implementation, Design, Impact, Idea Quality |
| **Community** | Devpost/Discord | Feedback, visibility, potential collaborators |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Nebius credits insufficient | Medium | High | Claim both $25 promos early; use Nano for routing, Ultra only for heavy reasoning; monitor daily |
| OCR accuracy on complex UIs | Medium | Medium | Test Windows OCR API first (fast + built-in); fallback to PaddleOCR |
| PGVector / Token Factory API instability | Low | High | Prototype memory module Week 1; local SQLite fallback for demo |
| Time overrun on UI polish | High | High | Use Tauri for rapid native-feeling dev; scope to floating card overlay only |
| Tavily integration complexity | Low | Medium | Allocate dedicated Week 3 slot; use Python SDK |
| Demo video quality | Medium | High | Record iterative clips weekly; final edit Week 5; rigid script (30/90/60) |
| Judges miss Nebius/NVIDIA in demo | Medium | High | Explicit 60-second tech explanation segment; README "How we used" section |

---

## Budget & Resources

### Compute Credits (Free)
- **Nebius Token Factory:** $25 via promo code `NEBIUS-DEVPOST-GLOBAL26`
- **Nebius Builder Program:** $25 + Tavily API credits
- **Total Cloud Budget:** $50 + Tavily credits

### Local Hardware
- **GPU:** RTX 2050 (4GB VRAM) — sufficient for PaddleOCR, Windows OCR, local processing
- **OS:** Windows 10/11 (native target)
- **RAM:** 16GB+ recommended

### Software Stack

| Layer | Technology |
|-------|-----------|
| Screen Capture | Windows OCR API (primary), PaddleOCR (fallback) |
| Context Routing | Nemotron Nano (Nebius Serverless) |
| Reasoning | Nemotron 3 Ultra (Nebius Serverless Endpoints) |
| Vector Memory | PGVector on Nebius Token Factory |
| Web Search | Tavily Search API → local MD/PDF save |
| Backend | Python 3.11 + FastAPI |
| OS Integration | pywin32 + uiautomation |
| UI | Tauri (Rust + React) — floating overlay |
| Repo | GitHub (MIT license) |

### Timeline Budget
- **39 days** (Sep 22 → Oct 30)
- **~5 weeks** structured sprints
- **Buffer:** 3 days before deadline

---

## Key Success Factors

1. **The wow moment works in the demo** — OCR → memory → Tavily → Nemotron diff, zero prompts typed
2. **Proactive, not reactive** — the core design principle that separates Synapse from every other submission
3. **Tavily integration** as guaranteed side-prize path ($3K)
4. **Polished floating overlay UI** — "coherent product experience" per judging rubric
5. **Repository as launch page** — make grading effortless for judges
6. **Demo video discipline** — strict 30/90/60 structure (problem → demo → tech explanation)
7. **Ruthless scope** — 5 great features beat 10 broken ones every time