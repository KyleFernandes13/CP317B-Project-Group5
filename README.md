# CP317B Project - Group 5

## E-Commerce Store Management System

CP317B Software Engineering Group Project.

## Sprint 1 Goal

Create the first working prototype of the e-commerce system. Sprint 1 will focus on allowing users to:

- Log in
- Browse products
- View product details
- Add products to a shopping cart
- Manage the shopping cart

## Technology

- Python
- Flask
- HTML
- CSS
- SQLite

## Sprint 1 User Stories

- AUTH-1: User Login
- UI-1: Browse Products
- UI-2: View Product Details
- CART-1: Add to Cart
- CART-2: Manage Cart

## Team

- Kyle Fernandes - Product Owner / Group Leader
- Muhetaer Saidaer - Scrum Master / Back-End Developer
- Trong Pham - Front-End Developer
- Ryely Squires - Testing / Documentation
- Zohaib Aamir - Developer / Support

## Product Image Setup

Product images are stored locally in static/images/.

For existing databases, run the following commands from the project root:

```bash
python -m pip install Pillow
python setup_product_images.py
```

The setup script generates local product illustrations and assigns
image references to existing sample products without deleting users,
carts, or orders.

Products without valid images display a fallback placeholder.

Administrators can assign an image to a product by entering the
filename of an existing image stored in static/images/.
