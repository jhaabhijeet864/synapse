# Project Rules & Conventions — Synapse

## Code Style

- **Language:** Python 3.11+ (backend), TypeScript + React (frontend)
- **Formatter:** `black` for Python, `prettier` for TS/TSX
- **Linter:** `ruff` for Python, `eslint` with TypeScript rules
- **Naming:**
  - Python: `snake_case` for functions/variables, `PascalCase` for classes
  - TypeScript: `camelCase` for functions/variables, `PascalCase` for components/types
- **Type hints:** Required on all Python function signatures
- **Docstrings:** Google-style for all public Python functions

## Git Workflow

- **Branch strategy:** Feature branches from `main` (`feature/ocr-capture`, `feature/pgvector-memory`)
- **Commit format:** `type(scope): short description`
  - Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
  - Example: `feat(ocr): add Windows OCR API wrapper with diff detection`
- **PRs:** Not applicable (solo project) — commit directly to `main` with descriptive messages
- **Tags:** Tag each week's milestone (`v0.1-week1`, `v0.2-week2`, etc.)

## Testing Standards

- **Unit tests:** `pytest` for Python backend modules (ocr, memory, routing, tools)
- **Target:** Core pipeline functions must have at least happy-path tests
- **Test location:** `tests/` mirroring `src/` structure
- **No test → no merge:** Any new module gets at least one smoke test
- **Frontend:** Minimal — manual testing for UI components given time constraints

## Documentation Standards

- **All public functions** must have a one-line docstring minimum
- **README** is the single source of truth for setup
- **Architecture diagram** must stay in sync with actual implementation
- **Every Nebius/NVIDIA API call** must be commented with what model/endpoint is used and why
- **TASKS.md** is updated at the start and end of every work session

## Security Conventions

- **No secrets in code** — all API keys via environment variables or Windows Credential Manager
- **No raw OCR content to cloud** — only summaries and embeddings leave the machine
- **.env files** listed in `.gitignore` from day one
- **Nebius credentials** loaded at runtime, never hardcoded

## Demo & Submission Rules

- **Wow moment first** — every feature decision is evaluated by: "does this make the demo better?"
- **Video script locked** by Week 4: 30s problem / 90s demo / 60s tech
- **README "How we used NVIDIA + Nebius"** section must be visible above the fold
- **All non-negotiable hackathon requirements** must be verified before Week 5 ends