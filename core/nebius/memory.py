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
    # Qwen/Qwen3-Embedding-8B → 4096-dim output (verified live Sep 2026).
    # Must match MODELS["embed"] output dim; bootstrap() migrates stale dims.
    EMBEDDING_DIM = 4096

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
    """.format(dim=EMBEDDING_DIM)

    # HNSW (not ivfflat): ivfflat caps at 2000 dims, HNSW supports 4096.
    # Created separately so old servers without HNSW still get working tables.
    INDEX_DDL = """
    CREATE INDEX IF NOT EXISTS episodic_memory_idx
    ON episodic_memories USING hnsw (context_vector vector_cosine_ops);
    """

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

        async def _init_conn(conn):
            # Register pgvector codec so vector columns round-trip as lists.
            # Non-fatal if the helper is unavailable (we use ::vector casts).
            try:
                from pgvector.asyncpg import register_vector
                await register_vector(conn)
            except Exception:
                pass

        self._pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5, init=_init_conn)

    async def bootstrap(self) -> None:
        """Create tables and indexes if they don't exist; migrate stale dims."""
        async with self._pool.acquire() as conn:
            await conn.execute(self.DDL)
            try:
                await conn.execute(self.INDEX_DDL)
            except Exception as e:
                # Old pgvector without HNSW: exact scan still works at personal scale.
                print(f"[Memory] HNSW index skipped ({e}); using exact search")
            # Migrate tables created with a wrong vector dim (e.g. legacy 1536).
            try:
                row = await conn.fetchrow(
                    """
                    SELECT atttypmod AS dim
                    FROM pg_attribute
                    JOIN pg_class ON pg_class.oid = pg_attribute.attrelid
                    WHERE pg_class.relname = 'episodic_memories'
                      AND pg_attribute.attname = 'context_vector'
                    """
                )
                # pgvector stores vector(n) typmod as n directly (NOT n+4
                # like varchar). Verified live: vector(1536) → atttypmod 1536.
                existing = row["dim"] if row and row["dim"] and row["dim"] > 0 else None
                if existing and existing != self.EMBEDDING_DIM:
                    print(f"[Memory] Migrating context_vector dim {existing} -> {self.EMBEDDING_DIM} (dropping stale rows)")
                    await conn.execute("DROP TABLE IF EXISTS episodic_memories")
                    await conn.execute(self.DDL)
                    try:
                        await conn.execute(self.INDEX_DDL)
                    except Exception as e:
                        print(f"[Memory] HNSW index skipped ({e}); using exact search")
            except Exception as e:
                print(f"[Memory] Dim check skipped: {e}")

    def _check_dim(self, vector: list) -> None:
        """Fail fast if the embedding model changed output dim."""
        if len(vector) != self.EMBEDDING_DIM:
            raise ValueError(
                f"Embedding dim mismatch: got {len(vector)}, "
                f"expected {self.EMBEDDING_DIM}. Check NEBIUS_EMBED_MODEL."
            )

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
        self._check_dim(vector)

        entry_id = str(uuid.uuid4())
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO episodic_memories
                    (id, application_context, problem_signature, resolution_summary,
                     file_extensions, context_vector)
                VALUES ($1, $2, $3, $4, $5, $6::vector)
                """,
                entry_id,
                application_context[:128],
                problem_signature,
                resolution_summary,
                file_extensions,
                vector,   # list[float]; pgvector codec registered in connect()
            )
        return entry_id

    async def search(self, query_text: str, top_k: int = 2) -> list[MemoryEntry]:
        """
        Semantic nearest-neighbor search. Returns up to top_k entries
        with similarity >= SIMILARITY_THRESHOLD.
        """
        query_vector = await self._nebius.embed(query_text)
        self._check_dim(query_vector)

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
                query_vector,   # list[float]; pgvector codec registered in connect()
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
