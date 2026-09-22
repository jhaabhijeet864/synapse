# Architecture Document

## System Overview

Synapse is a **hybrid local-cloud desktop AI layer** for Windows with a **layered context fusion architecture**. Context is assembled from 4 OS-level sources across two parallel processing lanes — a fast event-driven lane (< 100ms trigger) and a slow background enrichment lane — merged into a single Context Bundle before reasoning.

See [`CONTEXT_LAYER.md`](./CONTEXT_LAYER.md) for the full context layer deep-dive.

```
┌─────────────────────────────────────────────────────────┐
│                    SYNAPSE — System Flow                 │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │  Screen OCR  │───▶│  Context     │                   │
│  │  (Win OCR /  │    │  Aggregator  │                   │
│  │  PaddleOCR)  │    │  (FastAPI)   │                   │
│  └──────────────┘    └──────┬───────┘                   │
│                             │                            │
│  ┌──────────────┐           ▼                            │
│  │  OS Context  │    ┌──────────────┐                   │
│  │  (pywin32)   │───▶│ Memory Query │                   │
│  └──────────────┘    │ (PGVector on │                   │
│                       │ Nebius TF)   │                   │
│                       └──────┬───────┘                   │
│                              │                            │
│                              ▼                            │
│                       ┌──────────────┐                   │
│                       │ Nano Router  │ ──▶ [Simple] ──▶  │
│                       │ (Nemotron    │     Nano Response  │
│                       │  Nano)       │                   │
│                       └──────┬───────┘                   │
│                              │ [Complex]                  │
│                              ▼                            │
│                       ┌──────────────┐    ┌───────────┐ │
│                       │ Ultra Reason │    │  Tavily   │ │
│                       │ (Nemotron 3  │◀───│  Search   │ │
│                       │  Ultra)      │    │  (if gap) │ │
│                       └──────┬───────┘    └───────────┘ │
│                              │                            │
│                              ▼                            │
│                       ┌──────────────┐                   │
│                       │  Overlay UI  │                   │
│                       │  (Tauri +    │                   │
│                       │   React)     │                   │
│                       └──────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| OCR Capture (slow lane) | Windows OCR API + PaddleOCR | Read active window content every 5s |
| Clipboard Monitor (fast lane) | win32clipboard event hook | Capture intentional copy actions instantly |
| Process Focus Tracker (slow lane) | psutil + pywin32 | App focus time, switch frequency every 10s |
| File System Watcher (slow lane) | watchdog library | Project detection, recent modified files |
| Context Aggregator | Python asyncio event bus | Fuse all 4 sources into Context Bundle |
| Trigger Evaluator | Custom scoring engine | Score events, suppress low-signal noise |
| OS Integration | pywin32, uiautomation | Window title, app identification |
| Backend | Python 3.11 + FastAPI | Pipeline orchestration |
| Context Routing | Nemotron Nano (Nebius Serverless) | Classify intent, route to Nano or Ultra |
| Reasoning | Nemotron 3 Ultra (Nebius Serverless) | Deep reasoning, code diff, summarization |
| Vector Memory | PGVector on Nebius Token Factory | Long-term personal model + session history |
| Web Research | Tavily Search API | Fill knowledge gaps; auto-save MD/PDF |
| UI | Tauri (Rust) + React | Floating overlay card system |
| Embeddings | Nebius Embeddings API | Encode context for PGVector retrieval |

---

## Data Models

### Memory Entry (PGVector)
```python
class MemoryEntry:
    id: UUID
    user_id: str               # local machine ID
    timestamp: datetime
    app_context: str           # active app at time of capture
    content_summary: str       # OCR'd + summarized content
    embedding: vector(1536)    # semantic embedding
    tags: list[str]            # auto-generated topic tags
    source_type: str           # "ocr" | "tavily" | "manual"
    raw_content: str           # original OCR text
```

### Synapse Card (UI Response)
```typescript
interface SynapseCard {
  id: string;
  trigger: "auto" | "manual";
  context_used: string[];      // memory IDs that contributed
  response: string;            // Nemotron's answer
  actions: CardAction[];       // "Apply fix", "Save", "Search more"
  model_used: "nano" | "ultra";
  tavily_sources?: TavilyResult[];
  confidence: number;
}
```

---

## API Design

### Internal FastAPI Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/context/capture` | Receive OCR snapshot + OS context |
| `POST` | `/context/analyze` | Route context through Nano → Ultra pipeline |
| `GET`  | `/memory/search` | Semantic search over PGVector |
| `POST` | `/memory/store` | Store new memory entry |
| `POST` | `/search/tavily` | Trigger Tavily search + save results |
| `GET`  | `/health` | Health check for Tauri IPC |

### External APIs

| API | Usage |
|-----|-------|
| Nebius Serverless Endpoints | Nemotron Nano + Ultra inference |
| Nebius Token Factory (PGVector) | Memory storage + retrieval |
| Nebius Embeddings | Encode content for semantic search |
| Tavily Search API | Real-time web research |

---

## Infrastructure

```
LOCAL (Windows Machine)
├── Synapse.exe          (Tauri desktop app)
├── synapse_backend/     (Python FastAPI, runs as background service)
│   ├── ocr/             (Windows OCR + PaddleOCR wrappers)
│   ├── memory/          (PGVector client)
│   ├── routing/         (Nano router logic)
│   └── tools/           (Tavily, OS commands)
└── synapse_data/        (local saved MD/PDF from Tavily)

CLOUD (Nebius)
├── Serverless Endpoint: nemotron-nano   (fast routing)
├── Serverless Endpoint: nemotron-ultra  (heavy reasoning)
├── Token Factory:       PGVector DB     (persistent memory)
└── Embeddings API:      text-embedding  (semantic search)
```

### Startup Sequence
1. Tauri app launches → starts Python FastAPI backend via sidecar
2. Backend connects to Nebius PGVector, validates credentials
3. OCR monitor thread starts (polls active window every 5s)
4. Tauri overlay enters idle state, waits for trigger events

---

## Security

- **Local data:** All raw OCR content stored locally; only embeddings + summaries sent to Nebius
- **API keys:** Stored in OS keychain (Windows Credential Manager), never hardcoded
- **Nebius auth:** Bearer token via environment / keychain; rotated per session
- **Tavily results:** Saved locally; not re-uploaded to cloud
- **No telemetry:** Zero analytics or data collection by default
- **PGVector isolation:** Single-tenant; user's machine ID as namespace key