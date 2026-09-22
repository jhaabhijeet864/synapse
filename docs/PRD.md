# Product Requirements Document

## Overview

**Project Name:** Synapse  
**Hackathon:** Nebius × NVIDIA Global AI Hackathon  
**Track:** Personal AI Track  
**Deadline:** October 30, 2026 @ 10:30pm GMT+5:30  
**Tagline:** *"The AI that lives between your brain and your computer."*

Build a privacy-first, always-on desktop AI layer that runs natively on Windows. Synapse reads your screen via OCR, maintains persistent vector memory of your work, researches the web via Tavily, and surfaces answers through Nemotron reasoning on Nebius — proactively, before you ask.

---

## Goals

- **Primary:** Win the Personal AI Track ($20,000 Grand Prize or NVIDIA Jetson Orin Nano)
- **Secondary:** Claim $3,000 Best Use of Tavily side prize
- **Tertiary:** Qualify for City Winner Award ($500) via Builders & Brews attendance
- Build a shippable, polished product experience — not just a technical demo
- Demonstrate mastery of Nebius Token Factory + NVIDIA Nemotron integration

---

## The Core User Problem

Knowledge workers lose **2+ hours/day** to cognitive overhead — re-explaining context to stateless tools, re-searching things already found, losing work state between sessions. Current AI tools are **reactive**: you summon them, re-explain yourself, manually stitch the answer back in.

**Synapse is ambient**. It already knows what you're doing.

---

## User Stories

1. **As a developer**, when I hit a runtime error, I want Synapse to OCR my screen, retrieve relevant past sessions, and surface a fix using Nemotron — without me typing a single prompt
2. **As a researcher**, I want Synapse to automatically run Tavily searches based on what I'm reading and save the results to my disk as Markdown
3. **As a power user**, I want the assistant to remember my work patterns across sessions so it gets smarter about my habits over time
4. **As a user**, I want a polished floating overlay — not a terminal window — that feels like a premium product
5. **As a user**, I want the AI to route cheap/fast requests to Nemotron Nano and complex reasoning to Ultra, so my credits stretch further

---

## Features

### Core (Must Have — Demo-Critical)

- [ ] **Screen OCR Engine**: Capture active window content using Windows OCR API (primary) + PaddleOCR (fallback); parse error messages, code, unselectable text, charts
- [ ] **Proactive Context Trigger**: Detect screen changes (new error, new document opened, idle state) and auto-trigger Synapse analysis pipeline
- [ ] **Smart Routing**: Nemotron Nano (Nebius) classifies intent → routes to Nano (fast) or Ultra (heavy reasoning)
- [ ] **Nemotron 3 Ultra Reasoning**: Deep analysis, code diff generation, document summarization via Nebius Serverless Endpoints
- [ ] **PGVector Persistent Memory**: Store work sessions, user preferences, interaction history; semantic retrieval for cross-session context
- [ ] **Tavily Web Research Pipeline**: Auto-triggered when local context + memory insufficient; results auto-saved as MD/PDF to local filesystem
- [ ] **Floating Overlay UI**: Tauri + React card system; non-intrusive, dismissible, keyboard-shortcut accessible
- [ ] **Windows OS Integration**: Active window detection, app identification, system state awareness via pywin32

### Differentiators (Should Have — Scoring Points)

- [ ] **Proactive Mode**: Synapse surfaces answers based on screen events, not just manual invocation
- [ ] **Memory Browser**: Simple UI panel showing what Synapse remembers about your workflow
- [ ] **One-Click Actions**: "Apply fix", "Save to notes", "Search more" as quick actions on overlay cards
- [ ] **Credit-Aware Routing**: Automatically prefer Nano when Ultra budget is low; display token usage

### Stretch (Nice to Have — Add if Week 3 is Ahead)

- [ ] Voice invocation (faster-whisper CUDA) — wake-word: "Hey Synapse"
- [ ] Local model fallback for offline reasoning (Nemotron Nano ONNX)
- [ ] Multi-monitor awareness
- [ ] Cross-app workflow: "Summarize this email and draft a reply"

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Hackathon Placement | Top 3 or Track Winner |
| Side Prizes | Tavily ($3K) |
| Demo Video | ≤3 min: 30s problem, 90s working demo, 60s tech explanation |
| Repo Quality | Clear setup, MIT license, highlighted Nebius/NVIDIA usage, architecture diagram |
| Technical Implementation | OCR → routing → Nemotron → memory → Tavily all working end-to-end |
| Design Polish | Feels like a commercial overlay product, not a prototype |

---

## Timeline

| Phase | Dates | Deliverables |
|-------|-------|--------------|
| **Week 1** (Sep 22–28) | Foundation | Claim $50 credits, Nebius endpoints live, PGVector schema, repo initialized, OCR PoC working |
| **Week 2** (Sep 29–Oct 5) | Core Loop | OCR → Nano routing → Ultra reasoning → overlay card UI (wow moment works end-to-end) |
| **Week 3** (Oct 6–12) | Memory + Tavily | PGVector memory active, Tavily pipeline + auto-save, proactive trigger system |
| **Week 4** (Oct 13–19) | Polish | UI refinement, one-click actions, end-to-end test, demo video recording |
| **Week 5** (Oct 20–26) | Ship | README, architecture diagrams, demo video edit, Devpost submission |
| **Buffer** (Oct 27–30) | Contingency | Bug fixes, final submit by Oct 30 10:30pm |

---

## Non-Negotiable Requirements (Disqualification Risks)

- ✅ Runs on Nebius Token Factory or Nebius AI Cloud
- ✅ Uses ≥1 NVIDIA open-source model (Nemotron 3 Ultra + Nano)
- ✅ Public repo with MIT license visible at top
- ✅ Working demo URL (hosted app or test build)
- ✅ 3-min public YouTube demo video with audio explaining Nebius/NVIDIA usage
- ✅ README with setup instructions and "How we used NVIDIA + Nebius" section
- ✅ Feedback on Nebius Token Factory, AI Cloud, NVIDIA tools submitted