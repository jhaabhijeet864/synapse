# Context Layer Architecture — Synapse

> *Going beyond OCR: how Synapse builds a live cognitive model of what you're doing.*

---

## The Problem with OCR-Only

OCR reads what's *visible*. But what you're cognitively engaged with is much richer than the current screen:

- You copied an error 10 seconds ago — before the screen changed
- You've been in VS Code for 90 minutes — this is deep work, not a quick look
- You switched from Slack to VS Code 3 times in 5 minutes — context switching, likely stuck
- The file you have open was last modified 3 days ago — you're returning to cold code

**OCR sees a frame. The context layer sees the movie.**

---

## Context Sources

Synapse draws from **4 ambient context sources**, all OS-level (no app extensions required):

| Source | What it captures | Signal type |
|--------|-----------------|-------------|
| **Screen OCR** | Visible text, error messages, UI state | Visual |
| **Clipboard history** | What you've copied — code snippets, error strings, URLs, text | Intentional |
| **Process focus tracker** | Which app is active, how long, how often you switch | Behavioral |
| **File system watcher** | Recently opened/modified files, project directory detection | Structural |

### Why clipboard is gold
The clipboard is the most intentional signal available without app integrations. When you copy something, you've made a deliberate decision that it matters. A copied error message + OCR of the same screen = **double confirmation** of the context, zero ambiguity.

### Why process focus is gold
Focus time reveals cognitive load:
- **Long focus + no switches** = deep work, high engagement → Synapse stays quiet
- **Rapid app switching** = stuck or overwhelmed → Synapse should be more proactive
- **Return to same app after pause** = re-orienting → good time to surface memory

---

## The Layered Fusion Architecture

Context is assembled in **two parallel lanes** that merge before Synapse reasons:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FAST LANE — Event-driven, < 100ms trigger
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Clipboard change ──────┐
  Window switch ─────────┼──▶ Event Bus ──▶ Trigger Evaluator
  Terminal output ───────┘                        │
  Manual invocation                               │
                                           (is this high-signal?)
                                                  │
                                    ┌─────────────┴────────────┐
                                    │ YES: emit to Aggregator  │
                                    │ NO:  log + continue      │
                                    └──────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SLOW LANE — Background enrichment, async, always running
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  OCR monitor (every 5s) ──────────┐
  File system watcher ─────────────┼──▶ Context Object
  Process focus stats (every 10s) ─┘    (always fresh)
  PGVector memory query                      │
                                             │ (enriches fast lane)
                                             ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGGREGATOR — Merges both lanes into a single Context Bundle
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Context Bundle {
    trigger_source: "clipboard" | "window_switch" | "manual" | "auto"
    trigger_content: <what fired the fast lane>
    screen_text: <latest OCR snapshot>
    clipboard_recent: [last 5 copied items with timestamps]
    active_app: "VS Code" | "Chrome" | "Terminal" | ...
    focus_duration_mins: 47
    switch_frequency_per_hour: 12
    project_path: "e:/myproject"
    recent_files: ["auth.py", "user_service.py"]
    memory_context: [top 3 relevant PGVector entries]
  }
                              │
                              ▼
                    Nemotron Nano Router
                    (classify + route)
                              │
                    Nemotron 3 Ultra (if needed)
                              │
                    Synapse Card → User
```

---

## Trigger Evaluation Logic

Not every event should surface a card. The Trigger Evaluator scores each fast-lane event:

### High-Signal Events (auto-trigger a card)
| Event | Signal | Reason |
|-------|--------|--------|
| Clipboard contains error/traceback | Very high | User just copied the problem |
| Window switches to app after >30min away | High | Re-orienting to cold context |
| Rapid app switching (>4 switches/5min) | High | Stuck, needs help |
| Same error appears on screen 2x in row | High | Problem persists |
| Manual invocation (Ctrl+Shift+Space) | Always | User explicitly asked |

### Low-Signal Events (log but don't trigger)
| Event | Signal | Reason |
|-------|--------|--------|
| Regular clipboard text (name, URL) | Low | Normal workflow, not a problem |
| Normal app switching (1-2/hr) | Low | Healthy context switch |
| Long focus on same app | Low | Deep work — do NOT interrupt |
| New file opened (first time) | Low | Wait and see |

### Suppression Rules
- Never trigger if user dismissed last card < 60 seconds ago
- Never trigger during detected meeting (mic active + meeting app in focus)
- Respect "do not disturb" mode (user can toggle)

---

## The Personal Model (Long-Term Memory)

Beyond session context, Synapse builds a **persistent personal model** in PGVector:

```python
class PersonalModel:
    # Work patterns
    peak_focus_hours: list[int]         # hours of day with longest focus
    frequent_apps: dict[str, float]     # app → avg daily minutes
    project_map: dict[str, ProjectCtx]  # project path → known context

    # Knowledge graph
    known_errors: list[ErrorPattern]    # errors seen + how they were resolved
    known_tools: list[str]              # languages, frameworks detected
    preferred_solutions: list[Solution] # solutions user accepted via "Apply"

    # Behavioral baseline
    avg_switch_frequency: float         # normal switches/hr for this user
    deep_work_threshold_mins: int       # min focus time = deep work for this user
```

This means:
- **Week 1:** Synapse is generic
- **Week 2:** Synapse knows your stack (Python + FastAPI + React)
- **Week 4:** Synapse knows you get stuck on async issues, prefers explicit error messages, writes tests after features

The model improves without any effort from the user.

---

## Privacy Model

Since Synapse is "privacy-first", here's exactly what leaves the machine:

| Data | Stays local | Sent to Nebius |
|------|-------------|----------------|
| Raw OCR screenshots | ✅ Never sent | — |
| Raw clipboard content | ✅ Never sent | — |
| File contents | ✅ Never sent | — |
| Content summaries (text) | ✅ Stored locally | Only as prompt input |
| Embeddings (vectors) | — | ✅ Stored in PGVector on Nebius |
| Reasoning prompts | — | ✅ Sent to Nemotron (summarized context) |
| Tavily search queries | — | ✅ Sent to Tavily (inferred topic) |

**Rule:** Raw user data never leaves the machine. Only summaries and embeddings go to cloud.

---

## Implementation Modules

### Module 1: `synapse/context/ocr.py`
- Windows OCR API wrapper
- Diff detection (only process changed text)
- PaddleOCR fallback

### Module 2: `synapse/context/clipboard.py`
- Win32 clipboard monitor (event-driven via `win32clipboard`)
- Content classifier: error/code/URL/plain text
- Rolling buffer of last 10 items with timestamps

### Module 3: `synapse/context/focus.py`
- Process focus tracker via `psutil` + `pywin32`
- Focus duration per app, switch frequency calculation
- Behavioral anomaly detection (is user stuck?)

### Module 4: `synapse/context/filesystem.py`
- `watchdog` library for file system events
- Project directory detection (`.git`, `package.json`, `pyproject.toml`)
- Recent files rolling list per project

### Module 5: `synapse/context/aggregator.py`
- Subscribes to all 4 context sources via internal event bus
- Maintains live Context Bundle (always current)
- Trigger Evaluator with scoring logic
- Suppression rules engine

### Module 6: `synapse/memory/pgvector.py`
- Read/write to PGVector on Nebius Token Factory
- Semantic search (top-k relevant memories for any context)
- Personal model update logic

### Module 7: `synapse/routing/nano_router.py`
- Send Context Bundle to Nemotron Nano
- Parse routing decision: fast/nano vs deep/ultra
- Tavily trigger decision

### Module 8: `synapse/reasoning/ultra.py`
- Construct enriched prompt from Context Bundle + memory
- Call Nemotron 3 Ultra
- Parse response: explanation + code diff + confidence

### Module 9: `synapse/tools/tavily.py`
- Search trigger + query construction
- Result parsing + local MD/PDF save
- Inject results into Context Bundle for Ultra

### Module 10: `synapse/ui/` (Tauri IPC)
- Receive card payload from FastAPI
- Render overlay card
- Handle actions: Apply, Save, Dismiss, Expand
