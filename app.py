"""Main Flask application for the E-Commerce Store Management System."""

import os
import sqlite3
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash


app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY",
    "sprint1-development-key"
)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database" / "store.db"


def get_db_connection():
    """Create and return a connection to the SQLite database."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def login_required(view_function):
    """Require a user to be logged in before viewing a page."""
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        return view_function(*args, **kwargs)

    return wrapped_view


def add_sample_products():
    """Add sample products if the products table is currently empty."""
    connection = get_db_connection()

    product_count = connection.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if product_count == 0:
        sample_products = [
            (
                "Wireless Headphones",
                "Comfortable wireless headphones with clear sound and long battery life.",
                79.99,
                ""
            ),
            (
                "Mechanical Keyboard",
                "A compact mechanical keyboard designed for gaming and everyday use.",
                89.99,
                ""
            ),
            (
                "Wireless Mouse",
                "Lightweight wireless mouse with adjustable sensitivity.",
                39.99,
                ""
            ),
            (
                "USB-C Hub",
                "Multi-port USB-C hub with USB, HDMI, and card reader connections.",
                49.99,
                ""
            ),
            (
                "Laptop Stand",
                "Adjustable aluminum laptop stand for a more comfortable workspace.",
                34.99,
                ""
            ),
            (
                "Webcam",
                "1080p webcam with built-in microphone for video calls and meetings.",
                59.99,
                ""
            )
        ]

        connection.executemany(
            """
            INSERT INTO products (name, description, price, image)
            VALUES (?, ?, ?, ?)
            """,
            sample_products
        )

        connection.commit()

    connection.close()


def get_products():
    """Return all products stored in the database."""
    connection = get_db_connection()

    product_rows = connection.execute(
        "SELECT * FROM products ORDER BY id"
    ).fetchall()

    connection.close()

    return product_rows


@app.route("/login", methods=["GET", "POST"])
def login():
    """Allow a customer to log in using stored account credentials."""
    error = None

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        connection.close()

        if user is None or not check_password_hash(
            user["password_hash"],
            password
        ):
            error = "Invalid email or password."
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["user_email"] = user["email"]
            session["user_role"] = user["role"]

            return redirect(url_for("product_catalogue"))

    return render_template(
        "login.html",
        error=error
    )


@app.route("/logout")
def logout():
    """Log the current user out and return to the login page."""
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def home():
    """Redirect logged-in users to the product catalogue."""
    return redirect(url_for("product_catalogue"))


@app.route("/products")
@login_required
def product_catalogue():
    """Display all available products."""
    return render_template(
        "products.html",
        products=get_products()
    )


@app.route("/products/<int:product_id>")
@login_required
def product_details(product_id):
    """Display the details for one selected product."""
    connection = get_db_connection()

    product = connection.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    connection.close()

    if product is None:
        abort(404)

    return render_template(
        "product_details.html",
        product=product
    )


if __name__ == "__main__":
    add_sample_products()
    app.run(debug=True)
