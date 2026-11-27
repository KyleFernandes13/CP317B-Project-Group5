
"""Main Flask application for the E-Commerce Store Management System."""
# pylint: disable=too-many-lines

import os
import secrets
import sqlite3
from decimal import Decimal, InvalidOperation
from functools import wraps
from pathlib import Path

from flask import (
    Flask, abort, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY", "sprint1-development-key"
)
BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database" / "store.db"


def get_db_connection():
    """Open the store database with foreign key enforcement."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def login_required(view_function):
    """Restrict pages to authenticated users."""
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view_function(*args, **kwargs)
    return wrapped_view


def admin_required(view_function):
    """Restrict management pages to authenticated administrators."""
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("user_role") != "admin":
            abort(403)
        return view_function(*args, **kwargs)
    return wrapped_view


def add_sample_products():
    """Seed a new catalogue only; do not restore deleted products."""
    connection = get_db_connection()

    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")

            count = connection.execute(
                "SELECT COUNT(*) FROM products"
            ).fetchone()[0]

            seeded = connection.execute(
                "SELECT seq FROM sqlite_sequence WHERE name = 'products'"
            ).fetchone()

            if count == 0 and seeded is None:
                sample_products = [
                    (
                        "Wireless Headphones",
                        "Comfortable wireless headphones with clear sound and long battery life.",
                        79.99,
                        "headphones.png"
                    ),
                    (
                        "Mechanical Keyboard",
                        "A compact mechanical keyboard designed for gaming and everyday use.",
                        89.99,
                        "keyboard.png"
                    ),
                    (
                        "Wireless Mouse",
                        "Lightweight wireless mouse with adjustable sensitivity.",
                        39.99,
                        "mouse.png"
                    ),
                    (
                        "USB-C Hub",
                        "Multi-port USB-C hub with USB, HDMI, and card reader connections.",
                        49.99,
                        "usb_hub.png"
                    ),
                    (
                        "Laptop Stand",
                        "Adjustable aluminum laptop stand for a more comfortable workspace.",
                        34.99,
                        "laptop_stand.png"
                    ),
                    (
                        "Webcam",
                        "1080p webcam with built-in microphone for video calls and meetings.",
                        59.99,
                        "webcam.png"
                    )
                ]

                connection.executemany(
                    """
                    INSERT INTO products (name, description, price, image)
                    VALUES (?, ?, ?, ?)
                    """,
                    sample_products
                )

    finally:
        connection.close()


def get_products():
    """Return the current product catalogue."""
    connection = get_db_connection()

    try:
        return connection.execute(
            "SELECT * FROM products ORDER BY id"
        ).fetchall()

    finally:
        connection.close()


# Authentication

@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate a local store account."""
    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = get_db_connection()

        try:
            user = connection.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            ).fetchone()

        finally:
            connection.close()

        if user is None or not check_password_hash(
            user["password_hash"], password
        ):
            error = "Invalid email or password."

        else:
            session.clear()

            session["user_id"] = user["id"]
            session["user_email"] = user["email"]
            session["user_role"] = user["role"]

            return redirect(url_for("product_catalogue"))

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """End the active session."""
    session.clear()

    return redirect(url_for("login"))


@app.route("/")
@login_required
def home():
    """Redirect users to the product catalogue."""
    return redirect(url_for("product_catalogue"))


# Product Images - UI-3

@app.template_global()
def product_image_url(filename):
    """Return a valid local product image or a fallback placeholder."""

    image_directory = (
        BASE_DIR / "static" / "images"
    ).resolve()

    fallback = url_for(
        "static",
        filename="images/placeholder.png"
    )

    if not filename or not filename.strip():
        return fallback

    filename = filename.strip()

    if "/" in filename or "\\" in filename or "\0" in filename:
        return fallback

    try:
        image_path = (image_directory / filename).resolve()

        if (
            image_path.parent == image_directory
            and image_path.is_file()
            and image_path.suffix.lower() in {
                ".png", ".jpg", ".jpeg", ".webp", ".gif"
            }
        ):
            return url_for(
                "static",
                filename="images/" + filename
            )

    except (OSError, RuntimeError, ValueError):
        return fallback

    return fallback


# Product catalogue

@app.route("/products")
@login_required
def product_catalogue():
    """Display available products."""
    return render_template(
        "products.html",
        products=get_products()
    )


@app.route("/products/<int:product_id>")
@login_required
def product_details(product_id):
    """Display details for a selected product."""
    connection = get_db_connection()

    try:
        product = connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

    finally:
        connection.close()

    if product is None:
        abort(404)

    return render_template(
        "product_details.html",
        product=product
    )


# Shopping cart

@app.route("/cart")
@login_required
def cart():
    """Display the customer's shopping cart."""
    connection = get_db_connection()

    try:
        cart_rows = connection.execute(
            """
            SELECT
                cart_items.id,
                products.name,
                products.price,
                cart_items.quantity
            FROM cart_items
            JOIN products
                ON cart_items.product_id = products.id
            WHERE cart_items.user_id = ?
            ORDER BY cart_items.id
            """,
            (session["user_id"],)
        ).fetchall()

    finally:
        connection.close()

    cart_items = []
    total = Decimal("0.00")

    for row in cart_rows:
        item = dict(row)

        item["price"] = Decimal(str(item["price"]))
        item["subtotal"] = item["price"] * item["quantity"]

        total += item["subtotal"]
        cart_items.append(item)

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )


def get_cart_quantity():
    """Validate the submitted cart quantity."""
    try:
        quantity = int(request.form.get("quantity", ""))

    except ValueError:
        abort(
            400,
            description="Quantity must be a positive whole number."
        )

    if quantity < 1:
        abort(
            400,
            description="Quantity must be a positive whole number."
        )

    return quantity


@app.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    """Add a product to the customer's cart."""
    quantity = get_cart_quantity()
    connection = get_db_connection()

    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")

            product = connection.execute(
                "SELECT id FROM products WHERE id = ?",
                (product_id,)
            ).fetchone()

            if product is None:
                abort(404)

            item = connection.execute(
                """
                SELECT id, quantity
                FROM cart_items
                WHERE user_id = ? AND product_id = ?
                """,
                (
                    session["user_id"],
                    product_id
                )
            ).fetchone()

            if item is None:
                connection.execute(
                    """
                    INSERT INTO cart_items (
                        user_id,
                        product_id,
                        quantity
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        session["user_id"],
                        product_id,
                        quantity
                    )
                )

            else:
                connection.execute(
                    """
                    UPDATE cart_items
                    SET quantity = ?
                    WHERE id = ? AND user_id = ?
                    """,
                    (
                        quantity + item["quantity"],
                        item["id"],
                        session["user_id"]
                    )
                )

    finally:
        connection.close()

    return redirect(url_for("cart"))


@app.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required
def update_cart_item(item_id):
    """Update the quantity of a cart item."""
    quantity = get_cart_quantity()
    connection = get_db_connection()

    try:
        with connection:
            result = connection.execute(
                """
                UPDATE cart_items
                SET quantity = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    quantity,
                    item_id,
                    session["user_id"]
                )
            )

            if result.rowcount == 0:
                abort(404)

    finally:
        connection.close()

    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_cart_item(item_id):
    """Remove an item from the customer's cart."""
    connection = get_db_connection()

    try:
        with connection:
            result = connection.execute(
                """
                DELETE FROM cart_items
                WHERE id = ? AND user_id = ?
                """,
                (
                    item_id,
                    session["user_id"]
                )
            )

            if result.rowcount == 0:
                abort(404)

    finally:
        connection.close()

    return redirect(url_for("cart"))


# Simulated Checkout - ORD-4

CHECKOUT_FIELDS = {
    "full_name": "Full name",
    "address": "Street address",
    "city": "City",
    "province": "Province",
    "postal_code": "Postal code"
}

PAYMENT_METHODS = {
    "mock_card": "Simulated Credit Card",
    "mock_paypal": "Simulated PayPal",
    "mock_debit": "Simulated Debit Card"
}


def checkout_csrf_token():
    """Create a security token for the checkout form."""
    if "checkout_csrf" not in session:
        session["checkout_csrf"] = secrets.token_hex(32)

    return session["checkout_csrf"]


def validate_checkout_form():
    """Validate fictional shipping information and mock payment."""

    form = {
        field: request.form.get(field, "").strip()
        for field in CHECKOUT_FIELDS
    }

    form["payment_method"] = request.form.get(
        "payment_method", ""
    )

    for field, label in CHECKOUT_FIELDS.items():

        if not form[field]:
            return form, f"{label} is required."

        if len(form[field]) > 200:
            return form, f"{label} is too long."

    if form["payment_method"] not in PAYMENT_METHODS:
        return form, "Please select a valid payment method."

    return form, None


def render_checkout_page(form=None, error=None):
    """Display the order summary using current database prices."""

    connection = get_db_connection()

    try:
        cart_rows = connection.execute(
            """
            SELECT
                products.name,
                products.price,
                cart_items.quantity
            FROM cart_items
            JOIN products
                ON cart_items.product_id = products.id
            WHERE cart_items.user_id = ?
            ORDER BY cart_items.id
            """,
            (session["user_id"],)
        ).fetchall()

    finally:
        connection.close()

    if not cart_rows:
        abort(400, description="Your cart is empty.")

    cart_items = []
    total = Decimal("0.00")

    for row in cart_rows:
        item = dict(row)

        item["price"] = Decimal(str(item["price"]))
        item["subtotal"] = item["price"] * item["quantity"]

        total += item["subtotal"]
        cart_items.append(item)

    return render_template(
        "checkout.html",
        cart_items=cart_items,
        total=total,
        form=form or {},
        error=error,
        payment_methods=PAYMENT_METHODS,
        csrf_token=checkout_csrf_token()
    )


@app.route("/checkout")
@login_required
def checkout():
    """Display the simulated checkout page."""

    return render_checkout_page()


# Customer orders - Sprint 2 and Sprint 3

@app.route("/orders/place", methods=["POST"])
@login_required
def place_order():
    """Validate checkout and convert the cart into a stored order."""

    expected_token = session.get("checkout_csrf", "")
    submitted_token = request.form.get("csrf_token", "")

    if not expected_token or not secrets.compare_digest(
        expected_token.encode("utf-8"),
        submitted_token.encode("utf-8")
    ):
        abort(400, description="Invalid checkout submission.")

    form, error = validate_checkout_form()

    if error:
        return render_checkout_page(form, error), 400

    connection = get_db_connection()

    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")

            cart_rows = connection.execute(
                """
                SELECT
                    cart_items.product_id,
                    products.name,
                    products.price,
                    cart_items.quantity
                FROM cart_items
                JOIN products
                    ON cart_items.product_id = products.id
                WHERE cart_items.user_id = ?
                ORDER BY cart_items.id
                """,
                (session["user_id"],)
            ).fetchall()

            if not cart_rows:
                abort(400, description="Your cart is empty.")

            total = Decimal("0.00")

            for item in cart_rows:
                total += (
                    Decimal(str(item["price"]))
                    * item["quantity"]
                )

            cursor = connection.execute(
                """
                INSERT INTO orders (
                    user_id,
                    total,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, datetime('now', 'localtime'))
                """,
                (
                    session["user_id"],
                    float(total),
                    "Placed"
                )
            )

            order_id = cursor.lastrowid

            connection.executemany(
                """
                INSERT INTO order_items (
                    order_id,
                    product_id,
                    product_name,
                    price,
                    quantity
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        order_id,
                        item["product_id"],
                        item["name"],
                        item["price"],
                        item["quantity"]
                    )
                    for item in cart_rows
                ]
            )

            connection.execute(
                """
                DELETE FROM cart_items
                WHERE user_id = ?
                """,
                (session["user_id"],)
            )

    except sqlite3.Error:
        abort(500, description="Unable to place order.")

    finally:
        connection.close()

    session.pop("checkout_csrf", None)

    return redirect(
        url_for("order_confirmation", order_id=order_id)
    )


@app.route("/orders/<int:order_id>/confirmation")
@login_required
def order_confirmation(order_id):
    """Display confirmation for a completed order."""
    connection = get_db_connection()

    try:
        order = connection.execute(
            """
            SELECT id, total, status, created_at
            FROM orders
            WHERE id = ? AND user_id = ?
            """,
            (
                order_id,
                session["user_id"]
            )
        ).fetchone()

    finally:
        connection.close()

    if order is None:
        abort(404)

    return render_template(
        "order_confirmation.html",
        order=order
    )


@app.route("/orders")
@login_required
def order_history():
    """Display the customer's previous orders."""
    connection = get_db_connection()

    try:
        orders = connection.execute(
            """
            SELECT id, total, status, created_at
            FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (session["user_id"],)
        ).fetchall()

    finally:
        connection.close()

    return render_template(
        "orders.html",
        orders=orders
    )


@app.route("/orders/<int:order_id>")
@login_required
def order_details(order_id):
    """Display details and status for a selected order."""
    connection = get_db_connection()

    try:
        order = connection.execute(
            """
            SELECT id, total, status, created_at
            FROM orders
            WHERE id = ? AND user_id = ?
            """,
            (
                order_id,
                session["user_id"]
            )
        ).fetchone()

        if order is None:
            abort(404)

        item_rows = connection.execute(
            """
            SELECT product_name, price, quantity
            FROM order_items
            WHERE order_id = ?
            ORDER BY id
            """,
            (order_id,)
        ).fetchall()

    finally:
        connection.close()

    order_items = []

    for row in item_rows:
        item = dict(row)

        item["price"] = Decimal(str(item["price"]))
        item["subtotal"] = item["price"] * item["quantity"]

        order_items.append(item)

    return render_template(
        "order_details.html",
        order=order,
        order_items=order_items
    )


# Administrator order management - ADM-2

@app.route("/admin/orders")
@admin_required
def admin_orders():
    """Display customer orders for administrators."""
    connection = get_db_connection()

    try:
        orders = connection.execute(
            """
            SELECT
                orders.id,
                users.email,
                orders.created_at,
                orders.total,
                orders.status
            FROM orders
            JOIN users
                ON orders.user_id = users.id
            ORDER BY orders.id DESC
            """
        ).fetchall()

    finally:
        connection.close()

    return render_template(
        "admin_orders.html",
        orders=orders,
        statuses=(
            "Placed",
            "Processing",
            "Shipped",
            "Completed"
        )
    )


@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def update_order_status(order_id):
    """Update the status of a customer order."""
    status = request.form.get("status", "")

    if status not in (
        "Placed",
        "Processing",
        "Shipped",
        "Completed"
    ):
        abort(400, description="Select a valid order status.")

    connection = get_db_connection()

    try:
        with connection:
            result = connection.execute(
                """
                UPDATE orders
                SET status = ?
                WHERE id = ?
                """,
                (
                    status,
                    order_id
                )
            )

            if result.rowcount == 0:
                abort(404)

    finally:
        connection.close()

    return redirect(url_for("admin_orders"))


# Administrator product management - ADM-1

def admin_product_csrf_token():
    """Return a session-specific token for product management forms."""

    if "admin_product_csrf" not in session:
        session["admin_product_csrf"] = secrets.token_hex(32)

    return session["admin_product_csrf"]


def validate_admin_product_csrf():
    """Reject invalid administrator product form submissions."""

    expected = session.get("admin_product_csrf", "")
    submitted = request.form.get("csrf_token", "")

    if not expected or not secrets.compare_digest(
        expected.encode("utf-8"),
        submitted.encode("utf-8")
    ):
        abort(400, description="Invalid form submission.")


def validate_product_form():
    """Check product information on the server before writing it."""

    product = {
        "name": request.form.get("name", "").strip(),
        "description": request.form.get("description", "").strip(),
        "price": request.form.get("price", "").strip(),
        "image": request.form.get("image", "").strip()
    }

    if not product["name"]:
        return product, "Product name is required."

    if len(product["name"]) > 100:
        return product, "Product name cannot exceed 100 characters."

    if not product["description"]:
        return product, "Product description is required."

    if len(product["description"]) > 2000:
        return product, "Product description is too long."

    try:
        price = Decimal(product["price"])

        if not price.is_finite():
            return product, "Enter a valid product price."

        if price < 0 or price > Decimal("999999.99"):
            return product, "Price must be between $0 and $999,999.99."

        if price != price.quantize(Decimal("0.01")):
            return product, "Price cannot have more than two decimal places."

    except InvalidOperation:
        return product, "Enter a valid product price."

    image = product["image"]

    if image:
        allowed_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".gif"
        }

        if (
            len(image) > 255
            or "/" in image
            or "\\" in image
            or "\0" in image
            or Path(image).suffix.lower() not in allowed_extensions
        ):
            return product, "Enter a valid local image filename."

        image_directory = (
            BASE_DIR / "static" / "images"
        ).resolve()

        try:
            image_path = (
                image_directory / image
            ).resolve()

            if (
                image_path.parent != image_directory
                or not image_path.is_file()
            ):
                return product, "Image file was not found in static/images."

        except (OSError, RuntimeError, ValueError):
            return product, "Enter a valid local image filename."

    product["price"] = float(price)

    return product, None


@app.route("/admin/products")
@admin_required
def admin_products():
    """Display the product catalogue for administrators."""

    return render_template(
        "admin_products.html",
        products=get_products(),
        csrf_token=admin_product_csrf_token()
    )


@app.route("/admin/products/add", methods=["GET", "POST"])
@admin_required
def admin_add_product():
    """Allow an administrator to create a new product."""

    product = {
        "name": "",
        "description": "",
        "price": "",
        "image": ""
    }

    error = None

    if request.method == "POST":
        validate_admin_product_csrf()

        product, error = validate_product_form()

        if error is None:
            connection = get_db_connection()

            try:
                with connection:
                    connection.execute(
                        """
                        INSERT INTO products (
                            name,
                            description,
                            price,
                            image
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            product["name"],
                            product["description"],
                            product["price"],
                            product["image"]
                        )
                    )

            finally:
                connection.close()

            return redirect(url_for("admin_products"))

    return render_template(
        "admin_product_form.html",
        title="Add Product",
        product=product,
        error=error,
        csrf_token=admin_product_csrf_token()
    ), 400 if error else 200


@app.route(
    "/admin/products/<int:product_id>/edit",
    methods=["GET", "POST"]
)
@admin_required
def admin_edit_product(product_id):
    """Allow an administrator to update an existing product."""

    connection = get_db_connection()

    try:
        existing_product = connection.execute(
            """
            SELECT *
            FROM products
            WHERE id = ?
            """,
            (product_id,)
        ).fetchone()

        if existing_product is None:
            abort(404)

        product = dict(existing_product)
        error = None

        if request.method == "POST":
            validate_admin_product_csrf()

            product, error = validate_product_form()

            if error is None:
                with connection:
                    result = connection.execute(
                        """
                        UPDATE products
                        SET name = ?,
                            description = ?,
                            price = ?,
                            image = ?
                        WHERE id = ?
                        """,
                        (
                            product["name"],
                            product["description"],
                            product["price"],
                            product["image"],
                            product_id
                        )
                    )

                    if result.rowcount == 0:
                        abort(404)

                return redirect(url_for("admin_products"))

    finally:
        connection.close()

    return render_template(
        "admin_product_form.html",
        title="Edit Product",
        product=product,
        error=error,
        csrf_token=admin_product_csrf_token()
    ), 400 if error else 200


@app.route(
    "/admin/products/<int:product_id>/delete",
    methods=["POST"]
)
@admin_required
def admin_delete_product(product_id):
    """Remove a product while preserving historical orders."""

    validate_admin_product_csrf()

    connection = get_db_connection()

    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")

            product = connection.execute(
                """
                SELECT id
                FROM products
                WHERE id = ?
                """,
                (product_id,)
            ).fetchone()

            if product is None:
                abort(404)

            # Remove the unavailable product from active carts.
            connection.execute(
                """
                DELETE FROM cart_items
                WHERE product_id = ?
                """,
                (product_id,)
            )

            # Preserve names, quantities, and prices in historical orders.
            connection.execute(
                """
                UPDATE order_items
                SET product_id = NULL
                WHERE product_id = ?
                """,
                (product_id,)
            )

            connection.execute(
                """
                DELETE FROM products
                WHERE id = ?
                """,
                (product_id,)
            )

    except sqlite3.Error:
        abort(500, description="Unable to remove product.")

    finally:
        connection.close()

    return redirect(url_for("admin_products"))


if __name__ == "__main__":
    add_sample_products()
    app.run(debug=True)
