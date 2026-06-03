"""Drop all tables and recreate schema. Works with PostgreSQL (Docker) and SQLite (local dev).

Usage (Docker):
  docker compose exec backend python app/scripts/reset_db.py

After reset, create the first admin at /setup in the frontend (no auto-seed on startup).
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import inspect, text

from app.core.database import engine
from app.main import init_db


def _dialect_name() -> str:
    return engine.dialect.name


def _reset_postgresql(conn) -> None:
    conn.execute(text("DROP SCHEMA public CASCADE"))
    conn.execute(text("CREATE SCHEMA public"))
    conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
    conn.execute(text("GRANT ALL ON SCHEMA public TO CURRENT_USER"))


def _reset_sqlite(conn) -> None:
    conn.execute(text("PRAGMA foreign_keys=OFF"))
    inspector = inspect(engine)
    for table in inspector.get_table_names():
        print(f"Dropping table: {table}")
        conn.execute(text(f'DROP TABLE IF EXISTS "{table}"'))
    conn.execute(text("PRAGMA foreign_keys=ON"))


def reset_database() -> None:
    dialect = _dialect_name()
    print(f"Resetting database (dialect={dialect})...")

    with engine.begin() as conn:
        if dialect == "postgresql":
            print("PostgreSQL: dropping and recreating public schema...")
            _reset_postgresql(conn)
        elif dialect == "sqlite":
            print("SQLite: dropping all tables...")
            _reset_sqlite(conn)
        else:
            inspector = inspect(engine)
            for table in inspector.get_table_names():
                print(f"Dropping table: {table}")
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))

    print("Recreating tables...")
    init_db()
    print("Database reset complete.")
    print("Open the app at /setup to create the first administrator (if no users exist).")


if __name__ == "__main__":
    reset_database()
