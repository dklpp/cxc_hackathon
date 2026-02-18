#!/usr/bin/env python3
"""
One-off migration script: copies all data from the local SQLite database
into the PostgreSQL (Neon) database specified by DATABASE_URL.

Run with:
    uv run python DB/migrate_sqlite_to_postgres.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ── source: SQLite ────────────────────────────────────────────────────────────
SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banking_system.db")
sqlite_engine = create_engine(f"sqlite:///{SQLITE_PATH}", echo=False)
SqliteSession = sessionmaker(bind=sqlite_engine)

# ── destination: PostgreSQL ───────────────────────────────────────────────────
PG_URL = os.environ.get("DATABASE_URL")
if not PG_URL:
    sys.exit("DATABASE_URL is not set. Aborting.")

pg_engine = create_engine(PG_URL, echo=False)
PgSession = sessionmaker(bind=pg_engine)

# ── import models so create_all knows the schema ─────────────────────────────
from DB.db_manager import Base

print("Creating tables in PostgreSQL if they don't exist...")
Base.metadata.create_all(bind=pg_engine)
print("✓ Tables ready\n")

# ── ordered list of tables (respects FK dependencies) ────────────────────────
TABLES = [
    "customers",
    "accounts",
    "debts",
    "payments",
    "communication_logs",
    "scheduled_calls",
    "call_planning_scripts",
    "planned_emails",
]


# Boolean columns that SQLite stores as 0/1 integers
BOOL_COLUMNS = {
    "accounts": {"is_active", "is_primary"},
}


def coerce_row(table: str, row: dict) -> dict:
    """Cast SQLite integer booleans to Python bools for PostgreSQL."""
    bool_cols = BOOL_COLUMNS.get(table, set())
    return {
        k: (bool(v) if k in bool_cols and v is not None else v)
        for k, v in row.items()
    }


def migrate_table(table: str, src_conn, dst_conn):
    rows = src_conn.execute(text(f"SELECT * FROM {table}")).mappings().all()
    if not rows:
        print(f"  {table}: 0 rows (skipped)")
        return

    cols = list(rows[0].keys())
    col_list = ", ".join(f'"{c}"' for c in cols)
    placeholders = ", ".join(f":{c}" for c in cols)

    # Use a savepoint so a failure here doesn't abort the whole connection
    dst_conn.execute(text(f'DELETE FROM "{table}"'))
    dst_conn.execute(
        text(f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders})'),
        [coerce_row(table, dict(r)) for r in rows],
    )
    print(f"  {table}: {len(rows)} rows migrated")


print("Migrating data...\n")
with sqlite_engine.connect() as src:
    for table in TABLES:
        # Use a fresh PG connection per table so errors don't cascade
        with pg_engine.connect() as dst:
            try:
                migrate_table(table, src, dst)
                dst.commit()
            except Exception as e:
                dst.rollback()
                print(f"  ✗ {table}: ERROR — {e}")

# Reset PostgreSQL sequences so auto-increment continues from the right value
print("\nResetting PostgreSQL sequences...")
with pg_engine.connect() as conn:
    for table in TABLES:
        try:
            conn.execute(text(
                f"SELECT setval(pg_get_serial_sequence('\"{table}\"', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM \"{table}\"), 0) + 1, false)"
            ))
        except Exception as e:
            print(f"  ✗ Could not reset sequence for {table}: {e}")
    conn.commit()

print("\n✓ Migration complete!")
