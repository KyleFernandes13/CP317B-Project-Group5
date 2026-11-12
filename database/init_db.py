"""Initialize the SQLite database and create fake local test accounts."""

import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "store.db"
SCHEMA = BASE_DIR / "schema.sql"

TEST_EMAIL = "customer@test.com"
TEST_PASSWORD = "password123"

ADMIN_EMAIL = "admin@test.com"
ADMIN_PASSWORD = "admin123"


def initialize_database():
    """Create database tables and fake customer and admin accounts."""
    connection = sqlite3.connect(DATABASE)

    with open(SCHEMA, "r", encoding="utf-8") as schema_file:
        connection.executescript(schema_file.read())

    customer_password_hash = generate_password_hash(TEST_PASSWORD)

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
            (
                customer_password_hash,
                "customer",
                TEST_EMAIL
            )
        )
    else:
        connection.execute(
            """
            INSERT INTO users (email, password_hash, role)
            VALUES (?, ?, ?)
            """,
            (
                TEST_EMAIL,
                customer_password_hash,
                "customer"
            )
        )

    admin_password_hash = generate_password_hash(ADMIN_PASSWORD)

    existing_admin = connection.execute(
        "SELECT id FROM users WHERE email = ?",
        (ADMIN_EMAIL,)
    ).fetchone()

    if existing_admin:
        connection.execute(
            """
            UPDATE users
            SET password_hash = ?, role = ?
            WHERE email = ?
            """,
            (
                admin_password_hash,
                "admin",
                ADMIN_EMAIL
            )
        )
    else:
        connection.execute(
            """
            INSERT INTO users (email, password_hash, role)
            VALUES (?, ?, ?)
            """,
            (
                ADMIN_EMAIL,
                admin_password_hash,
                "admin"
            )
        )

    connection.commit()
    connection.close()

    print("Database initialized successfully.")
    print(f"Test user: {TEST_EMAIL}")
    print(f"Test password: {TEST_PASSWORD}")
    print(f"Admin user: {ADMIN_EMAIL}")
    print(f"Admin password: {ADMIN_PASSWORD}")


if __name__ == "__main__":
    initialize_database()