# docs/MEMORY_SPEC.md — Synapse Long-Term Memory Specification

# SYNAPSE Long-Term Memory Specification

## 1. Storage Infrastructure

- **Engine:** PostgreSQL 16 with `pgvector` extension hosted on Nebius Token Factory
- **Embedding Model:** `BAAI/bge-en-icl` via Nebius Embeddings API (output dimension: 1536)
- **Scope:** Long-term personal developer model. Stores user habits, recurring architectural patterns, library preferences, and past bug resolution workflows — not raw desktop history.

---

## 2. Database DDL

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- Table: User Profile & Coding Habits
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_key VARCHAR(64) UNIQUE NOT NULL,   -- e.g., 'primary_stack', 'test_framework'
    attribute_value JSONB NOT NULL,
    confidence_score FLOAT DEFAULT 1.0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: Episodic Solutions & Debugging History
CREATE TABLE episodic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    application_context VARCHAR(128) NOT NULL,  -- e.g., 'Code.exe / auth-service'
    problem_signature TEXT NOT NULL,            -- Scraped error or context trace
    resolution_summary TEXT NOT NULL,           -- Generated fix that was accepted
    file_extensions VARCHAR(32)[] NOT NULL,
    context_vector vector(1536) NOT NULL        -- Embedding of problem + resolution
);

-- Index for fast cosine similarity search
CREATE INDEX episodic_memory_idx ON episodic_memories
USING ivfflat (context_vector vector_cosine_ops)
WITH (lists = 100);
```

---

## 3. Storage & Query Lifecycle

### 3.1 Retrieval Flow (During High-Signal Event)

1. User triggers an error event in terminal/IDE
2. Core daemon extracts the raw traceback and calls Nebius Embedding endpoint to produce query vector `V_err`
3. Executes a similarity query:

```sql
SELECT id, problem_signature, resolution_summary,
       1 - (context_vector <=> $1) AS similarity
FROM episodic_memories
WHERE 1 - (context_vector <=> $1) > 0.82
ORDER BY similarity DESC
LIMIT 2;
```

4. If match found with similarity > 0.82: injected into Nemotron 3 Ultra prompt as in-context few-shot example

### 3.2 Consolidation Flow (Async, After User Accepts Fix)

1. User clicks "Apply Fix" and code executes successfully within 60 seconds
2. Daemon pushes `(problem, resolution)` pair to memory store queue
3. Embedding generated and persisted to `episodic_memories`
4. User profile updated with detected stack, language, framework preferences

---

## 4. Privacy Guarantees

| Data | Local | Nebius |
|------|-------|--------|
| Raw OCR content | ✅ Never sent | — |
| Raw clipboard text | ✅ Never sent | — |
| Problem summaries | In PGVector | Embedding + summary text |
| Resolution text | In PGVector | Embedding + resolution |
| User profile attrs | In PGVector | JSONB + key |

All data in PGVector is scoped to the user's machine ID namespace. No cross-user data sharing.

---

## 5. Personal Model Schema (user_profiles keys)

| profile_key | value type | example |
|-------------|-----------|---------|
| `primary_stack` | `{language, frameworks[]}` | `{language: "python", frameworks: ["fastapi", "sqlalchemy"]}` |
| `test_framework` | `{name}` | `{name: "pytest"}` |
| `editor` | `{name, version}` | `{name: "VS Code", version: "1.89"}` |
| `peak_focus_hours` | `int[]` | `[9, 10, 11, 14, 15]` |
| `common_errors` | `{pattern, count}[]` | `[{pattern: "NoneType", count: 7}]` |
| `preferred_solutions` | `string[]` | `["explicit null checks", "guard clauses"]` |
