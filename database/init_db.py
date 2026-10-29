import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "store.db"
SCHEMA = BASE_DIR / "schema.sql"


def initialize_database():
    connection = sqlite3.connect(DATABASE)

    with open(SCHEMA, "r") as schema_file:
        connection.executescript(schema_file.read())

    connection.close()
    print("Database initialized successfully.")


if __name__ == "__main__":
    initialize_database()