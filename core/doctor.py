# core/doctor.py
import os
import sys
import time
from dotenv import load_dotenv
from openai import OpenAI
import psycopg2

load_dotenv()

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def check_env(var_name):
    val = os.getenv(var_name)
    if val:
        print(f"[{GREEN}PASS{RESET}] Env var {var_name} detected")
        return True
    print(f"[{RED}FAIL{RESET}] Env var {var_name} is missing")
    return False


def check_nebius():
    try:
        client = OpenAI(
            base_url="https://api.tokenfactory.nebius.com/v1/",
            api_key=os.getenv("NEBIUS_API_KEY")
        )
        t0 = time.time()
        # Verify endpoint responsiveness
        models = client.models.list()
        ms = int((time.time() - t0) * 1000)
        print(f"[{GREEN}PASS{RESET}] Nebius Token Factory connection OK ({ms}ms)")
        return True
    except Exception as e:
        print(f"[{RED}FAIL{RESET}] Nebius API error: {e}")
        return False


def check_postgres_pgvector():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
        version = cur.fetchone()
        if version:
            print(f"[{GREEN}PASS{RESET}] PostgreSQL connected with pgvector v{version[0]}")
            return True
        print(f"[{RED}FAIL{RESET}] pgvector extension not installed in database")
        return False
    except Exception as e:
        print(f"[{RED}FAIL{RESET}] PostgreSQL connection error: {e}")
        return False


def run_diagnostics():
    print(f"\n--- SYNAPSE HEALTH CHECK ---")
    results = [
        check_env("NEBIUS_API_KEY"),
        check_env("DATABASE_URL"),
        check_env("TAVILY_API_KEY"),
        check_postgres_pgvector(),
        check_nebius()
    ]
    if all(results):
        print(f"\n{GREEN}All systems operational. Ready to run Synapse.{RESET}\n")
    else:
        print(f"\n{RED}Environment verification failed. Check errors above.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    run_diagnostics()