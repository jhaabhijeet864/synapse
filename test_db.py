"""Quick PGVector connectivity test for Synapse."""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn_str = os.getenv("NEBIUS_PGVECTOR_URL")  # matches your .env key

if not conn_str:
    print("ERROR: NEBIUS_PGVECTOR_URL not set in .env")
    exit(1)

try:
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()

    # 1. Ensure pgvector extension exists
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()
    print("[OK] pgvector extension enabled")

    # 2. Bootstrap tables if they don't exist yet
    # NOTE: context_vector dim must match the embedding model:
    # Qwen/Qwen3-Embedding-8B → 4096 (see core/nebius/memory.py EMBEDDING_DIM).
    cur.execute("""
        CREATE TABLE IF NOT EXISTS episodic_memories (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            application_context VARCHAR(128) NOT NULL,
            problem_signature TEXT NOT NULL,
            resolution_summary TEXT NOT NULL,
            file_extensions VARCHAR(32)[] NOT NULL,
            context_vector vector(4096) NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            profile_key VARCHAR(64) UNIQUE NOT NULL,
            attribute_value JSONB NOT NULL,
            confidence_score FLOAT DEFAULT 1.0,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    print("[OK] Tables created / verified")

    # 3. Check row count
    cur.execute("SELECT COUNT(*) FROM episodic_memories;")
    count = cur.fetchone()[0]
    print(f"[OK] Connected successfully! Episodic memories: {count}")

    cur.execute("SELECT COUNT(*) FROM user_profiles;")
    count = cur.fetchone()[0]
    print(f"[OK] User profiles: {count}")

    # 4. Verify vector dim matches the embedding model (4096 for Qwen3-Embedding-8B)
    # NOTE: pgvector stores vector(n) typmod as n directly (verified live).
    cur.execute("""
        SELECT atttypmod AS dim
        FROM pg_attribute
        JOIN pg_class ON pg_class.oid = pg_attribute.attrelid
        WHERE pg_class.relname = 'episodic_memories'
          AND pg_attribute.attname = 'context_vector';
    """)
    dim = cur.fetchone()[0]
    print(f"[OK] context_vector dim: {dim}")
    if dim != 4096:
        print(f"[WARN] Expected dim 4096 (Qwen/Qwen3-Embedding-8B). Run bootstrap to migrate.")

    cur.close()
    conn.close()
    print("\n[SUCCESS] Database is ready for Synapse.")

except Exception as e:
    print(f"[FAILED] Connection failed: {e}")
