# modules/menu.py  — updated: loads image_path from DB
from collections import deque
from db import db_conn
from models.menu_item import MenuItem

# ═══════════════════════════════════════════════════════
# DATA STRUCTURES  — do not change
# ═══════════════════════════════════════════════════════

menu        = {}
categories  = {}
cart        = []
undo_stack  = []
order_queue = deque()


# ═══════════════════════════════════════════════════════
# DB
# ═══════════════════════════════════════════════════════

def load_menu_from_db(include_unavailable: bool = False):
    menu.clear()
    categories.clear()

    conn   = db_conn()
    cursor = conn.cursor(dictionary=True)
    query = (
        "SELECT item_id, name, category, price, is_available, image_path "
        "FROM menu_items "
    )
    if not include_unavailable:
        query += "WHERE is_available = 1 "
    query += "ORDER BY category, name"
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close(); conn.close()

    for row in rows:
        item = MenuItem(
            row["item_id"], row["name"], row["category"],
            row["price"], available=bool(row["is_available"]),
            image_path=row["image_path"]
        )
        menu[item.item_id] = item
        categories.setdefault(item.category, []).append(item.item_id)


def add_item_to_db(name, category, price, image_path=None):
    conn   = db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO menu_items (name, category, price, image_path) "
        "VALUES (%s, %s, %s, %s)",
        (name, category, price, image_path)
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close(); conn.close()

    item = MenuItem(new_id, name, category, price, image_path=image_path)
    menu[new_id] = item
    categories.setdefault(category, []).append(new_id)
    return item


def remove_item_from_db(item_id):
    conn   = db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE menu_items SET is_available = 0 WHERE item_id = %s",
        (item_id,)
    )
    conn.commit()
    cursor.close(); conn.close()

    if item_id in menu:
        menu[item_id].available = False


def update_item_image(item_id, image_path):
    conn   = db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE menu_items SET image_path = %s WHERE item_id = %s",
        (image_path, item_id)
    )
    conn.commit()
    cursor.close(); conn.close()

    if item_id in menu:
        menu[item_id].image_path = image_path


def set_item_availability(item_id, available: bool):
    conn   = db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE menu_items SET is_available = %s WHERE item_id = %s",
        (1 if available else 0, item_id)
    )
    conn.commit()
    cursor.close(); conn.close()

    if item_id in menu:
        menu[item_id].available = available


def update_item_price(item_id, new_price):
    """Update item price. Only affects future orders (snapshots protect old orders)."""
    conn   = db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE menu_items SET price = %s WHERE item_id = %s",
        (new_price, item_id)
    )
    conn.commit()
    cursor.close(); conn.close()

    if item_id in menu:
        menu[item_id].price = new_price


def load_all_menu_items():
    """Load all menu items including unavailable ones. Used by admin panel."""
    load_menu_from_db(include_unavailable=True)


# ═══════════════════════════════════════════════════════
# MENU DISPLAY (CLI)
# ═══════════════════════════════════════════════════════

def display_menu():
    print("\n" + "=" * 55)
    print("          ONLINE FOOD ORDER SYSTEM — MENU")
    print("=" * 55)
    for category, ids in categories.items():
        print(f"\n  ── {category} ──")
        for item_id in ids:
            item = menu[item_id]
            print(f"  [{item.item_id:>3}]  {item.name:<28}  PKR {item.price:.0f}")
    print("\n" + "=" * 55)


# ═══════════════════════════════════════════════════════
# SEARCH
# ═══════════════════════════════════════════════════════

def search_item(keyword):
    keyword = keyword.lower()
    return [item for item in menu.values() if keyword in item.name.lower()]


# ═══════════════════════════════════════════════════════
# CART
# ═══════════════════════════════════════════════════════

def add_to_cart(item_id, qty):
    if item_id not in menu:
        print("  Item not found."); return
    item = menu[item_id]
    for i, (ci, q) in enumerate(cart):
        if ci.item_id == item_id:
            cart[i] = (ci, q + qty)
            undo_stack.append(("add", item_id, qty))
            return
    cart.append((item, qty))
    undo_stack.append(("add", item_id, qty))


def remove_from_cart(item_id):
    for i, (item, qty) in enumerate(cart):
        if item.item_id == item_id:
            cart.pop(i)
            undo_stack.append(("remove", item_id, qty))
            return


def undo_last_action():
    if not undo_stack:
        return
    action, item_id, qty = undo_stack.pop()
    if action == "add":
        for i, (item, q) in enumerate(cart):
            if item.item_id == item_id:
                new_qty = q - qty
                if new_qty <= 0:
                    cart.pop(i)
                else:
                    cart[i] = (item, new_qty)
                return
    elif action == "remove":
        if item_id in menu:
            cart.append((menu[item_id], qty))


def get_cart_total():
    return sum(item.price * qty for item, qty in cart)


def clear_cart():
    cart.clear()
    undo_stack.clear()


def display_cart():
    """Displays cart contents in CLI format (for debugging/testing)."""
    if not cart:
        print("\n  Cart is empty.")
        return
    
    print("\n" + "=" * 55)
    print("          YOUR CART")
    print("=" * 55)
    for idx, (item, qty) in enumerate(cart, 1):
        subtotal = item.price * qty
        print(f"  {idx}. {item.name:<30}  Rs.{subtotal:>7.0f}  (x{qty})")
    print("  " + "─" * 51)
    print(f"  {'TOTAL':<37}  Rs.{get_cart_total():>7.0f}")
    print("=" * 55)