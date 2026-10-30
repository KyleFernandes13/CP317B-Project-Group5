"""Initialize the SQLite database and create a test customer account."""

import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "store.db"
SCHEMA = BASE_DIR / "schema.sql"

TEST_EMAIL = "customer@test.com"
TEST_PASSWORD = "password123"


def initialize_database():
    """Create database tables and add a fake test customer."""
    connection = sqlite3.connect(DATABASE)

    with open(SCHEMA, "r", encoding="utf-8") as schema_file:
        connection.executescript(schema_file.read())

    password_hash = generate_password_hash(TEST_PASSWORD)

    existing_user = connection.execute(
        "SELECT id FROM users WHERE email = ?",
        (TEST_EMAIL,)
    ).fetchone()

    if existing_user:
        connection.execute(
            """
            UPDATE users
            SET password_hash = ?, role = ?
            WHERE email = ?
            """,
            (password_hash, "customer", TEST_EMAIL)
        )
    else:
        connection.execute(
            """
            INSERT INTO users (email, password_hash, role)
            VALUES (?, ?, ?)
            """,
            (TEST_EMAIL, password_hash, "customer")
        )

    connection.commit()
    connection.close()

    print("Database initialized successfully.")
    print(f"Test user: {TEST_EMAIL}")
    print(f"Test password: {TEST_PASSWORD}")


if __name__ == "__main__":
    initialize_database()
    