# core/doctor.py
"""Synapse environment diagnostics.

Covers what the old root-level test_db.py did (pgvector extension, tables,
row counts, embedding-dim check) plus API-key presence and Nebius
reachability — using project conventions (core.config for .env,
asyncpg for Postgres, Nebius OpenAI-compatible base URL).

Usage:
    python -m core.doctor          # full check (hits live PGVector)
    python -m core.doctor --env    # keys only, no network calls

Exit code 0 = all pass, 1 = something failed.
"""

import argparse
import asyncio
import os
import sys

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"[{GREEN}PASS{RESET}] {msg}")


def fail(msg: str) -> None:
    print(f"[{RED}FAIL{RESET}] {msg}")


def check_env(var_name: str) -> bool:
    if os.getenv(var_name):
        ok(f"Env var {var_name} detected")
        return True
    fail(f"Env var {var_name} is missing")
    return False


async def check_pgvector() -> bool:
    """Extension + tables + row counts + embedding-dim check (ex-test_db.py)."""
    from core.nebius.memory import PGVectorMemory

    dsn = os.getenv("NEBIUS_PGVECTOR_URL")
    if not dsn:
        fail("NEBIUS_PGVECTOR_URL missing, skipping DB checks")
        return False
    try:
        import asyncpg

        pool = await asyncpg.create_pool(dsn, min_size=1, max_size=1)
        async with pool.acquire() as conn:
            ext = await conn.fetchval(
                "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
            )
            if not ext:
                fail("pgvector extension not installed in database")
                await pool.close()
                return False
            ok(f"PostgreSQL connected with pgvector v{ext}")

            mem_count = await conn.fetchval("SELECT COUNT(*) FROM episodic_memories;")
            ok(f"Episodic memories: {mem_count}")
            prof_count = await conn.fetchval("SELECT COUNT(*) FROM user_profiles;")
            ok(f"User profiles: {prof_count}")

            dim = await conn.fetchval(
                """
                SELECT atttypmod FROM pg_attribute
                JOIN pg_class ON pg_class.oid = pg_attribute.attrelid
                WHERE pg_class.relname = 'episodic_memories'
                  AND pg_attribute.attname = 'context_vector';
                """
            )
            print(f"       context_vector dim: {dim}")
            if dim != PGVectorMemory.EMBEDDING_DIM:
                fail(
                    f"Expected dim {PGVectorMemory.EMBEDDING_DIM}. "
                    "Run memory.bootstrap() to migrate."
                )
                await pool.close()
                return False
            ok(f"Vector dim matches embedding model ({dim})")
        await pool.close()
        return True
    except Exception as e:
        fail(f"PostgreSQL error: {e}")
        return False


def check_nebius() -> bool:
    """Nebius endpoint reachability via models list (no inference spend)."""
    try:
        from openai import OpenAI

        from core.nebius.client import NEBIUS_BASE_URL

        client = OpenAI(base_url=NEBIUS_BASE_URL, api_key=os.getenv("NEBIUS_API_KEY"))
        models = client.models.list()
        ids = [m.id for m in models.data[:5]]
        ok(f"Nebius reachable at {NEBIUS_BASE_URL} (e.g. {', '.join(ids)})")
        return True
    except Exception as e:
        fail(f"Nebius API error: {e}")
        return False


def main() -> None:
    from core.config import settings  # noqa: F401 — loads .env

    parser = argparse.ArgumentParser(description="Synapse environment diagnostics")
    parser.add_argument("--env", action="store_true", help="keys only, no network calls")
    args = parser.parse_args()

    print("\n--- SYNAPSE HEALTH CHECK ---")
    results = [
        check_env("NEBIUS_API_KEY"),
        check_env("NEBIUS_PGVECTOR_URL"),
        check_env("TAVILY_API_KEY"),
    ]
    if not args.env:
        results.append(asyncio.run(check_pgvector()))
        results.append(check_nebius())

    if all(results):
        print(f"\n{GREEN}All systems operational. Ready to run Synapse.{RESET}\n")
    else:
        print(f"\n{RED}Environment verification failed. Check errors above.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
