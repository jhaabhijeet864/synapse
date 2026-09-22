"""
core/nebius/memory.py
─────────────────────
PGVector connector & embedding pipelines.

Handles long-term personal model storage on Nebius Token Factory.
Stores episodic memories (problem → resolution pairs) and retrieves
semantically similar past experiences to inject into reasoning prompts.

Schema: see docs/MEMORY_SPEC.md for full DDL.
"""

import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import asyncpg


@dataclass
class MemoryEntry:
    id: str
    application_context: str      # e.g., "Code.exe / auth-service"
    problem_signature: str        # Error text or context summary
    resolution_summary: str       # What fix was accepted
    file_extensions: list[str]    # e.g., [".py", ".toml"]
    similarity: float = 0.0       # Set during retrieval
    timestamp: Optional[datetime] = None


class PGVectorMemory:
    """
    Async PGVector client for Synapse's long-term personal memory.

    Operations:
      - store()   → embed + persist a (problem, resolution) pair
      - search()  → semantic nearest-neighbor search for current context
      - bootstrap() → run DDL on first launch

    Usage:
        memory = PGVectorMemory()
        await memory.connect()
        await memory.bootstrap()

        # After user accepts a fix:
        await memory.store(app_ctx, problem, resolution, [".py"])

        # Before Ultra reasoning:
        memories = await memory.search(current_context_text, top_k=2)
    """

    SIMILARITY_THRESHOLD = 0.82
    EMBEDDING_DIM = 1536           # Must match MODELS["embed"] output dim

    DDL = """
    CREATE EXTENSION IF NOT EXISTS vector;

    CREATE TABLE IF NOT EXISTS user_profiles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        profile_key VARCHAR(64) UNIQUE NOT NULL,
        attribute_value JSONB NOT NULL,
        confidence_score FLOAT DEFAULT 1.0,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS episodic_memories (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        application_context VARCHAR(128) NOT NULL,
        problem_signature TEXT NOT NULL,
        resolution_summary TEXT NOT NULL,
        file_extensions VARCHAR(32)[] NOT NULL,
        context_vector vector({dim}) NOT NULL
    );

    CREATE INDEX IF NOT EXISTS episodic_memory_idx
    ON episodic_memories USING ivfflat (context_vector vector_cosine_ops)
    WITH (lists = 100);
    """.format(dim=EMBEDDING_DIM)

    def __init__(self, client=None):
        """
        Args:
            client: NebiusClient instance for generating embeddings.
                    Injected to avoid circular imports.
        """
        self._nebius = client
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Initialize async connection pool to Nebius PGVector."""
        dsn = os.environ.get("NEBIUS_PGVECTOR_URL")
        if not dsn:
            raise ValueError("NEBIUS_PGVECTOR_URL not set in environment")
        self._pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)

    async def bootstrap(self) -> None:
        """Create tables and indexes if they don't exist."""
        async with self._pool.acquire() as conn:
            await conn.execute(self.DDL)

    async def store(
        self,
        application_context: str,
        problem_signature: str,
        resolution_summary: str,
        file_extensions: list[str],
    ) -> str:
        """Embed and persist a new episodic memory. Returns the new UUID."""
        # Build text to embed: problem + resolution for rich semantic retrieval
        embed_text = f"Problem: {problem_signature}\nResolution: {resolution_summary}"
        vector = await self._nebius.embed(embed_text)

        entry_id = str(uuid.uuid4())
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO episodic_memories
                    (id, application_context, problem_signature, resolution_summary,
                     file_extensions, context_vector)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                entry_id,
                application_context[:128],
                problem_signature,
                resolution_summary,
                file_extensions,
                str(vector),   # asyncpg-pgvector expects list or str
            )
        return entry_id

    async def search(self, query_text: str, top_k: int = 2) -> list[MemoryEntry]:
        """
        Semantic nearest-neighbor search. Returns up to top_k entries
        with similarity >= SIMILARITY_THRESHOLD.
        """
        query_vector = await self._nebius.embed(query_text)

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, application_context, problem_signature,
                       resolution_summary, file_extensions, timestamp,
                       1 - (context_vector <=> $1::vector) AS similarity
                FROM episodic_memories
                WHERE 1 - (context_vector <=> $1::vector) > $2
                ORDER BY similarity DESC
                LIMIT $3
                """,
                str(query_vector),
                self.SIMILARITY_THRESHOLD,
                top_k,
            )

        return [
            MemoryEntry(
                id=str(row["id"]),
                application_context=row["application_context"],
                problem_signature=row["problem_signature"],
                resolution_summary=row["resolution_summary"],
                file_extensions=list(row["file_extensions"] or []),
                similarity=round(float(row["similarity"]), 4),
                timestamp=row["timestamp"],
            )
            for row in rows
        ]

    async def update_profile(self, key: str, value: dict, confidence: float = 1.0) -> None:
        """Upsert a user profile attribute (e.g., preferred language, framework)."""
        import json
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_profiles (profile_key, attribute_value, confidence_score)
                VALUES ($1, $2, $3)
                ON CONFLICT (profile_key) DO UPDATE
                    SET attribute_value = EXCLUDED.attribute_value,
                        confidence_score = EXCLUDED.confidence_score,
                        updated_at = CURRENT_TIMESTAMP
                """,
                key,
                json.dumps(value),
                confidence,
            )

    async def get_profile(self, key: str) -> Optional[dict]:
        """Retrieve a user profile attribute."""
        import json
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT attribute_value FROM user_profiles WHERE profile_key = $1", key
            )
        return json.loads(row["attribute_value"]) if row else None

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
