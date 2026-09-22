# SYNAPSE — Product Concept

> *"The AI that lives between your brain and your computer."*

---

## The Problem

Knowledge workers — developers, researchers, analysts, students — lose **2+ hours every day** to cognitive overhead: re-reading context they already know, re-searching things they've already found, re-explaining their situation to tools that have no memory of them.

Every AI tool today is **stateless and reactive**. You have to summon it, re-explain yourself, and manually stitch the answer back into your workflow.

**The real problem isn't AI capability. It's AI presence.**

Nobody has built an AI that is genuinely *ambient* — one that already knows what you're doing, what you were doing, and what you probably need next — without you lifting a finger to explain yourself.

This is specific, real, and affects every technical judge on the panel personally.

---

## The Solution

**Synapse** is a privacy-first desktop AI layer that runs natively on Windows. It watches your screen (with your permission), builds a live model of your cognitive context, and surfaces exactly the right answer — before you even ask.

It doesn't replace your workflow. It **augments your attention**.

### One-Sentence Pitch
> *"Synapse is the always-on AI that reads your screen, remembers your work, searches the web for you, and answers with Nemotron — so you never have to context-switch again."*

---

## The Wow Moment (Core Demo)

> User is in VS Code, staring at a cryptic runtime error.
>
> Without typing a single word, a **floating Synapse overlay card** appears:
> - It has already OCR'd the error message from screen
> - Retrieved a relevant memory: *"you hit this in the auth module 3 days ago"*
> - Pulled a live Tavily result from the exact GitHub issue that fixes it
> - Generated a code diff using Nemotron 3 Ultra
>
> **One click → error explained. Second click → fix applied.**
>
> The user never opened a browser. Never typed a prompt. Never broke flow.

This is the moment that wins. It is visual, instant, and emotionally resonant for any technical judge.

---

## Why It's Non-Obvious

| What others build | What Synapse does |
|-------------------|-------------------|
| Reactive chatbot — you ask, it answers | **Proactive** — it surfaces answers without being asked |
| Chat history as "memory" | **Persistent vector memory** — a model of your work patterns |
| You paste context manually | **Screen is the context** — OCR reads your workspace live |
| One model for everything | **Smart routing** — Nano for triage, Ultra for reasoning |

---

## The Name: SYNAPSE

A synapse is the connection point where neurons transfer information — exactly what this product does: connecting screen context → AI reasoning → your workflow.

**Why it works:**
- Implies **memory, intelligence, speed, and biological naturalness**
- Pronounceable, memorable, logo-ready
- No major product namespace conflicts in the AI space
- Tagline writes itself: **"Think faster."**

**Runner-ups considered:**
- *Vigil* — always watching, always ready
- *Orbit* — always around your work

---

## Scope Decision (What We Build vs. What We Cut)

### ✅ Build (Non-negotiable for the demo)

| Feature | Why |
|---------|-----|
| Screen capture + OCR (Windows OCR API / PaddleOCR) | The "eyes" — makes the wow moment possible |
| Nemotron 3 Ultra via Nebius Serverless | Required NVIDIA integration; handles heavy reasoning |
| Nemotron Nano for context routing | Fast triage, smart credit usage |
| PGVector persistent memory (Nebius Token Factory) | The "long-term memory" — key differentiator |
| Tavily web search → auto-save MD/PDF | Tavily side prize ($3K); fits the ambient flow naturally |
| Floating native overlay UI (Tauri + React) | Makes it feel like a product, not a demo script |
| Python 3.11 + FastAPI backend | Orchestrates the full tool pipeline |
| Windows OS integration (pywin32) | Active window detection, app context |

### ❌ Cut (Too risky for 39 days, solo)

| Feature | Reason |
|---------|--------|
| Vosk/Whisper voice input | Adds unreliable complexity; add only if ahead in Week 3 |
| MediaPipe gesture invocation | High setup cost, 0 judge points if it breaks live |
| Hermes Agent framework | Use lightweight custom tool routing — same result |
| Multi-monitor support | Stretch goal only after core is polished |

---

## User Narrative for Judges

> "Every developer has a second brain — their terminal history, their bookmarks, their notes app, their Stack Overflow tabs. Synapse unifies all of it into one ambient AI layer. It's not a chatbot. It's not a copilot. It's the connective tissue between your attention and your tools — powered by Nemotron's reasoning on Nebius infrastructure, with your data staying on your machine."

### Judging Criteria Alignment

| Criterion | How Synapse hits it |
|-----------|---------------------|
| **Technological Implementation** | Hybrid local/cloud, OCR, PGVector, Nemotron Nano+Ultra routing, Nebius Serverless |
| **Design** | Floating overlay UI — polished product, not terminal output |
| **Potential Impact** | 2B+ knowledge workers globally; universal daily pain |
| **Quality of Idea** | Proactive ambient AI is genuinely non-obvious in 2026 |

---

## Repository Strategy

README hero section must have:
1. A GIF of the wow moment (record during Week 4)
2. **"How we use NVIDIA + Nebius"** section near the top
3. One-command setup: `pip install -e . && python synapse.py`
4. Mermaid architecture diagram
5. MIT license badge in the header

Effortless judging = better scores.
