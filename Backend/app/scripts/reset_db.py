"""Delete all data and recreate empty tables. PostgreSQL (Docker) or SQLite (local dev).

Usage (Docker — from repo root):
  docker compose exec backend python app/scripts/reset_db.py --yes

Local:
  cd Backend && python app/scripts/reset_db.py --yes

After reset, create the first admin at /setup in the frontend.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import inspect, text

from app.core.config import settings
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


def reset_database(*, yes: bool = False) -> None:
    if not yes:
        print("This will DELETE ALL DATA in the database and recreate empty tables.")
        print(f"Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
        answer = input("Type YES to continue: ").strip()
        if answer != "YES":
            print("Aborted.")
            return

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
    print("Database reset complete — all data removed.")
    print("Open the app at /setup to create the first administrator.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete all database data and recreate schema.")
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompt (required for scripts/CI).",
    )
    args = parser.parse_args()
    reset_database(yes=args.yes)


if __name__ == "__main__":
    main()
