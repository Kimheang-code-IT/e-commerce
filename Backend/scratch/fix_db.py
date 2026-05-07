import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "app.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN last_login DATETIME")
    print("Column last_login added to users table.")
except sqlite3.OperationalError as e:
    print(f"Error or already exists: {e}")

conn.commit()
conn.close()
