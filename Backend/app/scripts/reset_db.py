import sys
import os

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import engine, Base
from app.main import init_db
from sqlalchemy import text

def reset_database():
    print("Resetting database...")
    
    # Disable foreign key checks for SQLite
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        
        # Get all table names
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        for table in tables:
            print(f"Dropping table: {table}")
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
        
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.commit()
    
    print("Recreating tables and seeding data...")
    init_db()
    print("Database reset complete.")

if __name__ == "__main__":
    reset_database()
