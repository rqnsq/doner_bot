"""
Database service module for Mama Doner Mini App.

Single responsibility: encapsulates all database access logic.
Uses aiosqlite with raw SQL for simplicity and performance.

Public API:
- init_db(db_path: str) -> None
- fetch_menu(db_path: str) -> list[dict]
- fetch_categories(db_path: str) -> list[str]
- save_order(db_path: str, user_id: int, cart_items: list, total_price: float) -> None
- save_pending_cart(db_path: str, cart_items: list) -> int
- fetch_pending_cart(db_path: str, order_id: int) -> list[dict] | None
- delete_pending_cart(db_path: str, order_id: int) -> None
- add_menu_item(db_path: str, name: str, price: float, description: str, category: str, emoji: str) -> None
- delete_menu_item(db_path: str, name: str) -> bool
"""

import os
import logging
import aiosqlite
import json
from typing import Optional

logging.basicConfig(level=logging.INFO)


async def init_db(db_path: str) -> None:
    """Initialize DB schema and seed minimal data if needed.

    This function is idempotent and safe to call on every startup.

    Args:
        db_path: Path to SQLite database file.
    """
    if not os.path.exists(os.path.dirname(db_path) or "data"):
        os.makedirs(os.path.dirname(db_path) or "data", exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                items_json TEXT,
                total_price REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                category TEXT,
                emoji TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS pending_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cart_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed menu if empty
        async with db.execute("SELECT count(*) FROM menu") as cur:
            row = await cur.fetchone()
            if row is None or row[0] == 0:
                initial_items = [
                    ("Classic Kebab", 120.0, "Chicken, cucumber, tomatoes, house sauce", "Classic", "🌯"),
                    ("Cheese Bomb", 140.0, "Three types of cheese, garlic sauce, chicken", "Cheese", "🧀"),
                    ("Spicy Dragon", 135.0, "Jalapeno, hot chili sauce, beef", "Spicy", "🌶️"),
                    ("Vegan Style", 110.0, "Falafel, hummus, fresh vegetables", "Vegan", "🥗"),
                    ("Cola Zero", 50.0, "0.5L, cold", "Drinks", "🥤"),
                    ("Ayran", 40.0, "Homemade, salted", "Drinks", "🥛")
                ]
                await db.executemany(
                    "INSERT INTO menu (name, price, description, category, emoji) VALUES (?, ?, ?, ?, ?)",
                    initial_items
                )

        # Seed categories if empty
        async with db.execute("SELECT count(*) FROM categories") as cur2:
            r = await cur2.fetchone()
            if r is None or r[0] == 0:
                seed = [("Classic",), ("Cheese",), ("Spicy",), ("Vegan",), ("Drinks",)]
                await db.executemany("INSERT OR IGNORE INTO categories (name) VALUES (?)", seed)

        await db.commit()
    logging.info("Database initialized: %s", db_path)
    if db_path.endswith('.db') or db_path.endswith('.sqlite'):
        logging.warning(
            "Using SQLite (%s) - for production consider PostgreSQL for concurrency and reliability.",
            db_path
        )


async def fetch_menu(db_path: str) -> list:
    """Return list of active menu items as dicts.

    Args:
        db_path: Path to SQLite database file.

    Returns:
        List of menu item dictionaries with keys: id, name, price, description, category, emoji, is_active.
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM menu WHERE is_active = 1") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def fetch_categories(db_path: str) -> list:
    """Return list of categories.

    Args:
        db_path: Path to SQLite database file.

    Returns:
        List of category names (strings).
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        categories = []
        async with db.execute("SELECT DISTINCT category FROM menu WHERE is_active = 1") as cur:
            rows = await cur.fetchall()
            categories = [dict(r)["category"] for r in rows if dict(r).get("category")]

        if not categories:
            async with db.execute("SELECT name FROM categories ORDER BY name") as c2:
                rows2 = await c2.fetchall()
                categories = [dict(r)["name"] for r in rows2 if dict(r).get("name")]

        if not categories:
            return ["Classic", "Cheese", "Spicy", "Vegan", "Drinks"]

        # Convert all categories to English format
        categories = [cat for cat in categories]
        
        return categories


async def save_order(db_path: str, user_id: int, cart_items: list, total_price: float) -> None:
    """Persist an order to DB.

    Args:
        db_path: Path to SQLite database file.
        user_id: Telegram user ID.
        cart_items: List of items in cart (will be stored as JSON).
        total_price: Total order amount.
    """
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO orders (user_id, items_json, total_price) VALUES (?, ?, ?)",
            (user_id, json.dumps(cart_items, ensure_ascii=False), total_price)
        )
        await db.commit()


async def save_pending_cart(db_path: str, cart_items: list) -> int:
    """Save pending cart to DB and return the ID.

    Args:
        db_path: Path to SQLite database file.
        cart_items: List of items in cart.

    Returns:
        Integer ID of the saved pending order (for use in invoice payload).
    """
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "INSERT INTO pending_orders (cart_json) VALUES (?)",
            (json.dumps(cart_items, ensure_ascii=False),)
        )
        await db.commit()
        order_id = cursor.lastrowid
        return order_id if order_id is not None else 0


async def fetch_pending_cart(db_path: str, order_id: int) -> Optional[list]:
    """Fetch cart_items from pending_orders by ID.

    Args:
        db_path: Path to SQLite database file.
        order_id: ID of the pending order.

    Returns:
        List of cart items (parsed from JSON) or None if not found.
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT cart_json FROM pending_orders WHERE id = ?", (order_id,)) as cur:
            row = await cur.fetchone()
            if row:
                return json.loads(row['cart_json'])
            return None


async def delete_pending_cart(db_path: str, order_id: int) -> None:
    """Delete pending order after successful payment.

    Args:
        db_path: Path to SQLite database file.
        order_id: ID of the pending order to delete.
    """
    async with aiosqlite.connect(db_path) as db:
        await db.execute("DELETE FROM pending_orders WHERE id = ?", (order_id,))
        await db.commit()


async def add_menu_item(
    db_path: str,
    name: str,
    price: float,
    description: str,
    category: str,
    emoji: str
) -> None:
    """Add a new menu item. Raises ValueError if item exists or validation fails.

    Args:
        db_path: Path to SQLite database file.
        name: Item name.
        price: Item price (must be >= 0).
        description: Item description.
        category: Item category.
        emoji: Item emoji.

    Raises:
        ValueError: If item already exists, name is invalid, or price is invalid.
    """
    if not name or not name.strip():
        raise ValueError('invalid_name')
    try:
        price = float(price)
    except (ValueError, TypeError):
        raise ValueError('invalid_price')
    if price < 0:
        raise ValueError('invalid_price')

    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT id FROM menu WHERE name = ?", (name,))
        existing = await cursor.fetchone()
        if existing:
            raise ValueError("exists")
        await db.execute(
            "INSERT INTO menu (name, price, description, category, emoji) VALUES (?, ?, ?, ?, ?)",
            (name, price, description, category, emoji)
        )
        await db.commit()


async def delete_menu_item(db_path: str, name: str) -> bool:
    """Delete menu item by name.

    Args:
        db_path: Path to SQLite database file.
        name: Item name to delete.

    Returns:
        True if item was deleted, False if not found.
    """
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT id FROM menu WHERE name = ?", (name,))
        row = await cursor.fetchone()
        if not row:
            return False
        await db.execute("DELETE FROM menu WHERE name = ?", (name,))
        await db.commit()
        return True
