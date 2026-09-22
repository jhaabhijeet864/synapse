<div align="center">

# 🧠 SYNAPSE

**The ambient, privacy-first AI layer between your brain and Windows.**

*Built for the [Nebius × NVIDIA Global AI Hackathon](https://devpost.com/software/synapse) — Personal AI Track*

[![License: MIT](https://img.shields.io/badge/License-MIT-76B900.svg)](LICENSE)
[![Powered By: NVIDIA Nemotron](https://img.shields.io/badge/Powered%20By-NVIDIA%20Nemotron-76B900.svg)](https://nebius.com)
[![Infrastructure: Nebius](https://img.shields.io/badge/Cloud-Nebius%20Token%20Factory-1A1A1A.svg)](https://nebius.com)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-1A1A1A.svg)](https://python.org)
[![Tauri v2](https://img.shields.io/badge/UI-Tauri%20v2-1A1A1A.svg)](https://tauri.app)

[📺 Watch Demo](#) &nbsp;·&nbsp; [🏗️ Architecture](#system-architecture) &nbsp;·&nbsp; [🚀 Quickstart](#quickstart)

</div>

---

## ⚡ The Core Innovation

Developers lose **2+ hours every day** to cognitive overhead — re-explaining context to stateless tools, re-searching things already found, losing work state between sessions. Every AI tool is reactive: you summon it, re-explain yourself, manually stitch the answer back in.

**Synapse is ambient.** It already knows what you're working on.

It watches your screen via OCR, remembers your work across sessions via PGVector, researches the web via Tavily, and surfaces exact answers through Nemotron reasoning on Nebius — **before you ask, without breaking your flow.**

---

## 🚀 How We Used NVIDIA & Nebius

> This section is highlighted for hackathon judges.

| Service | How Synapse uses it |
|---------|---------------------|
| **Nemotron Nano** (Nebius Serverless) | Fast triage in ~150ms — classifies context, decides routing |
| **Nemotron 3 Ultra** (Nebius Serverless) | Deep reasoning — generates code diffs, explains errors, synthesizes research |
| **PGVector on Nebius Token Factory** | Long-term personal memory — stores work patterns, past fixes, preferences |
| **Nebius Embeddings API** | Encodes context into vectors for semantic memory search |
| **Tavily Search API** | Real-time web research triggered by Nemotron when local context is insufficient |

### The Smart Routing Architecture

```
User error appears on screen
         │
    Clipboard / OCR captures it (< 10ms)
         │
    Nemotron Nano (Nebius) — triage in ~150ms
         │                        │
    [Simple]                  [Complex]
         │                        │
    Nano answers             Nemotron 3 Ultra
    directly                 + PGVector memory
                             + Tavily (if needed)
         │                        │
         └──────────┬─────────────┘
                    │
            Floating overlay card
            appears on screen
```

This architecture is **credit-efficient by design** — Nano handles ~70% of requests at 4x lower cost than Ultra.

---

## 🏗️ System Architecture

```
┌─────────────────────────── LOCAL (Windows) ──────────────────────────────┐
│                                                                           │
│  FAST LANE (< 10ms)          SLOW LANE (background)                      │
│  ┌──────────────┐            ┌──────────────┐  ┌──────────────┐          │
│  │  Clipboard   │            │  Screen OCR  │  │  Filesystem  │          │
│  │  Win32 Hook  │            │  WinRT API   │  │  Watcher     │          │
│  └──────┬───────┘            └──────┬───────┘  └──────┬───────┘          │
│         │                           │                  │                  │
│         ▼                    ┌──────▼──────────────────▼──────┐          │
│   Event Bus                  │     Context Aggregator          │          │
│         │                    │   (Trigger Scoring & Fusion)    │          │
│         └──────────────────▶ └─────────────────┬──────────────┘          │
│                                                 │                         │
│                              ┌──────────────────▼──────────────┐         │
│                              │    PII Redactor (local only)     │         │
│                              └──────────────────┬──────────────┘         │
│                                                 │                         │
│                         FastAPI Daemon :8420  ◀─┘                        │
│                              WebSocket ──────────▶ Tauri + React UI      │
└─────────────────────────────────────────────────────────────────────────┘
                                   │ HTTPS
                                   ▼
┌─────────────────────── NEBIUS CLOUD ──────────────────────────────────────┐
│                                                                            │
│   Nemotron Nano ──triage──▶ Nemotron 3 Ultra ◀── PGVector Memory          │
│   (Serverless EP)            (Serverless EP)      (Token Factory)          │
│                                    ▲                                       │
│                               Tavily Search API                            │
└────────────────────────────────────────────────────────────────────────────┘
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/CONTEXT_LAYER.md`](docs/CONTEXT_LAYER.md) for the full specification.

---

## 🛠️ Quickstart

### Prerequisites
- Windows 10/11 (64-bit)
- Python 3.11+
- Node.js 18+ & Rust/Cargo (for Tauri)
- Nebius account with Token Factory access
- Tavily API key

### 1-Command Setup

```powershell
git clone https://github.com/YOUR_USERNAME/synapse.git
cd synapse
scripts\setup_env.bat
```

### Configure Keys

```powershell
# Edit .env with your keys (created from .env.example by setup script)
notepad .env
```

```ini
NEBIUS_API_KEY=your_nebius_token_factory_api_key
NEBIUS_PGVECTOR_URL=postgresql://user:pass@host:5432/synapse
TAVILY_API_KEY=tvly-your_key
```

### Launch

```powershell
# Terminal 1 — Python daemon
.venv\Scripts\activate
python core/server.py

# Terminal 2 — Native UI
cd app
npm run tauri dev
```

---

## 📁 Project Structure

```
synapse/
├── core/                    # Python daemon (FastAPI + all AI logic)
│   ├── capture/             # Screen OCR, clipboard, process focus, filesystem
│   ├── engine/              # Context aggregator, redactor, state machine
│   ├── nebius/              # Nemotron client, Nano/Ultra router, PGVector memory
│   ├── tools/               # Tavily search, file patcher
│   └── server.py            # FastAPI + WebSocket IPC server
├── app/                     # Tauri v2 + React frontend
│   └── src/
│       ├── components/      # NeuronSphere, ContextCard, DiffViewer, HUD
│       ├── hooks/           # useDaemonSocket (WebSocket)
│       └── styles/          # NVIDIA design system
├── docs/                    # Full technical documentation
│   ├── ARCHITECTURE.md
│   ├── CONTEXT_LAYER.md     # Beyond-OCR ambient context layer
│   ├── DESIGN.md            # NVIDIA aesthetic design system
│   └── MEMORY_SPEC.md       # PGVector schema & personal model
├── tests/                   # Pytest unit tests
└── scripts/setup_env.bat    # 1-click Windows setup
```

---

## 🧪 Running Tests

```powershell
# Offline tests — no API keys needed
pytest tests\ -v

# Live integration test (requires .env)
python -c "
import asyncio
from core.nebius.client import NebiusClient
async def test():
    c = NebiusClient()
    print(await c.complete_nano('Hello from Synapse'))
asyncio.run(test())
"
```

---

## 📋 Hackathon Submission Checklist

- [x] Runs on **Nebius Token Factory** (PGVector) and **Nebius AI Cloud** (Serverless Endpoints)
- [x] Uses **NVIDIA Nemotron** open-source models (Nano + 3 Ultra)
- [x] Integrates **PGVector** persistent memory
- [x] Integrates **Tavily Search** with local auto-save
- [ ] 3-minute public YouTube demo video *(Week 4)*
- [ ] Working demo URL *(Week 5)*
- [x] MIT license
- [x] README with setup instructions and NVIDIA/Nebius usage explanation

---

## 📄 License

MIT — see [LICENSE](LICENSE)
