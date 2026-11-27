
"""Generate original product illustrations and assign catalogue images."""

import sqlite3
from pathlib import Path

from PIL import Image, ImageDraw


BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "static" / "images"
DATABASE = BASE_DIR / "database" / "store.db"

PRODUCT_IMAGES = {
    "Wireless Headphones": "headphones.png",
    "Mechanical Keyboard": "keyboard.png",
    "Wireless Mouse": "mouse.png",
    "USB-C Hub": "usb_hub.png",
    "Laptop Stand": "laptop_stand.png",
    "Webcam": "webcam.png"
}

DARK = "#263343"
GRAY = "#667587"
SILVER = "#BAC4CE"
BLUE = "#5288C7"


def create_images():
    """Generate seven local PNG image assets."""

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    def canvas():
        image = Image.new("RGB", (800, 600), "#F4F6F8")
        return image, ImageDraw.Draw(image)

    def save(image, filename):
        destination = IMAGE_DIR / filename

        if not destination.exists():
            image.save(destination)

    # Wireless headphones
    image, draw = canvas()

    draw.ellipse(
        (180, 485, 620, 525), fill="#DDE2E7"
    )
    draw.arc(
        (220, 95, 580, 475),
        180, 360, fill=DARK, width=42
    )
    draw.arc(
        (238, 113, 562, 457),
        180, 360, fill=GRAY, width=10
    )

    for x in (195, 495):
        draw.rounded_rectangle(
            (x, 260, x + 110, 480),
            radius=45, fill=DARK
        )
        draw.rounded_rectangle(
            (x + 12, 280, x + 98, 460),
            radius=32, fill=GRAY
        )

    save(image, "headphones.png")

    # Mechanical keyboard
    image, draw = canvas()

    draw.rounded_rectangle(
        (75, 188, 725, 450),
        radius=24, fill=DARK
    )

    for row in range(4):
        for column in range(13):
            x = 96 + column * 46
            y = 208 + row * 44

            draw.rounded_rectangle(
                (x, y, x + 39, y + 36),
                radius=5, fill=GRAY
            )

    draw.rounded_rectangle(
        (245, 392, 555, 430),
        radius=6, fill=BLUE
    )

    save(image, "keyboard.png")

    # Wireless mouse
    image, draw = canvas()

    draw.ellipse(
        (265, 485, 535, 525), fill="#DDE2E7"
    )
    draw.rounded_rectangle(
        (275, 95, 525, 500),
        radius=120, fill=DARK
    )
    draw.line(
        (400, 105, 400, 260),
        fill=SILVER, width=4
    )
    draw.line(
        (282, 260, 518, 260),
        fill=SILVER, width=4
    )
    draw.rounded_rectangle(
        (382, 150, 418, 218),
        radius=12, fill=GRAY
    )
    draw.ellipse(
        (392, 290, 408, 306),
        fill=BLUE
    )

    save(image, "mouse.png")

    # USB-C hub
    image, draw = canvas()

    draw.rounded_rectangle(
        (140, 215, 610, 405),
        radius=30, fill=SILVER
    )
    draw.rounded_rectangle(
        (155, 305, 595, 395),
        radius=15, fill=GRAY
    )

    for x in (180, 270, 360, 450):
        draw.rounded_rectangle(
            (x, 327, x + 65, 366),
            radius=5, fill=DARK
        )
        draw.rectangle(
            (x + 8, 339, x + 57, 350),
            fill=BLUE
        )

    draw.line(
        (610, 260, 680, 260, 680, 155),
        fill=DARK, width=15
    )
    draw.rounded_rectangle(
        (655, 115, 705, 170),
        radius=8, fill=GRAY
    )

    save(image, "usb_hub.png")

    # Laptop stand
    image, draw = canvas()

    draw.polygon(
        [(190, 440), (570, 440),
         (650, 490), (115, 490)],
        fill=SILVER
    )
    draw.polygon(
        [(285, 435), (335, 435),
         (495, 190), (445, 190)],
        fill=GRAY
    )
    draw.polygon(
        [(195, 165), (605, 165),
         (525, 295), (115, 295)],
        fill=SILVER
    )
    draw.line(
        (115, 295, 525, 295),
        fill=GRAY, width=12
    )
    draw.rounded_rectangle(
        (155, 267, 235, 287),
        radius=5, fill=DARK
    )
    draw.rounded_rectangle(
        (410, 267, 490, 287),
        radius=5, fill=DARK
    )

    save(image, "laptop_stand.png")

    # Webcam
    image, draw = canvas()

    draw.rounded_rectangle(
        (175, 175, 625, 365),
        radius=65, fill=DARK
    )
    draw.ellipse(
        (310, 180, 490, 360), fill=GRAY
    )
    draw.ellipse(
        (330, 200, 470, 340), fill="#142436"
    )
    draw.ellipse(
        (355, 225, 445, 315), fill="#315C85"
    )
    draw.ellipse(
        (370, 235, 400, 265), fill="#A6D2F5"
    )
    draw.ellipse(
        (545, 250, 560, 265), fill=BLUE
    )
    draw.rounded_rectangle(
        (360, 365, 440, 440),
        radius=12, fill=GRAY
    )
    draw.rounded_rectangle(
        (290, 425, 510, 470),
        radius=15, fill=DARK
    )

    save(image, "webcam.png")

    # Missing-image placeholder
    image, draw = canvas()

    draw.rounded_rectangle(
        (235, 150, 565, 410),
        radius=20, outline=GRAY, width=8
    )
    draw.ellipse(
        (280, 190, 340, 250),
        fill=SILVER
    )
    draw.polygon(
        [(250, 390), (355, 280),
         (430, 350), (485, 290),
         (550, 390)],
        fill=SILVER
    )
    draw.line(
        (230, 140, 570, 420),
        fill=GRAY, width=10
    )

    save(image, "placeholder.png")

    print("Seven local product image assets are ready.")


def assign_existing_images():
    """Assign images without resetting existing store data."""

    if not DATABASE.is_file():
        raise FileNotFoundError(
            "Initialize the existing store database first."
        )

    connection = sqlite3.connect(DATABASE)

    try:
        with connection:
            updated = 0

            for name, filename in PRODUCT_IMAGES.items():
                cursor = connection.execute(
                    """
                    UPDATE products
                    SET image = ?
                    WHERE name = ?
                    AND (
                        image IS NULL
                        OR TRIM(image) = ''
                    )
                    """,
                    (filename, name)
                )

                updated += cursor.rowcount

    finally:
        connection.close()

    print(f"Updated {updated} existing product image references.")


if __name__ == "__main__":
    create_images()
    assign_existing_images()
