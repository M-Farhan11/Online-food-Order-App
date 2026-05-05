# modules/payment.py
from db import db_conn
from models.order import Order
from models.order_item import OrderItem
from modules.menu import clear_cart


# ═══════════════════════════════════════════════════════
# DOUBLY LINKED LIST  —  do not change
# ═══════════════════════════════════════════════════════

class OrderNode:
    def __init__(self, order):
        self.order = order
        self.prev  = None
        self.next  = None


class OrderHistoryDLL:
    """DLL of Order objects. HEAD = newest, TAIL = oldest."""
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def prepend(self, order):
        node = OrderNode(order)
        if self.head is None:
            self.head = self.tail = node
        else:
            node.next      = self.head
            self.head.prev = node
            self.head      = node
        self.size += 1

    def newest_first(self) -> list:
        result, curr = [], self.head
        while curr:
            result.append(curr.order)
            curr = curr.next
        return result

    def is_empty(self) -> bool:
        return self.size == 0


history_dll = OrderHistoryDLL()


# ═══════════════════════════════════════════════════════
# DB  —  insert / fetch
# ═══════════════════════════════════════════════════════

def insert_order(user_id: int, total: float, method: str) -> Order:
    """
    Inserts a row into orders table.
    Returns an Order object with the new order_id.
    """
    conn   = db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (user_id, total_amount, status, payment_method) "
        "VALUES (%s, %s, 'Placed', %s)",
        (user_id, total, method)
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close(); conn.close()

    return Order(new_id, user_id, total, "Placed", method)


def insert_order_items(order_id: int, cart: list):
    """
    Saves snapshot of each cart item into order_items table.
    cart = [(MenuItem, qty), ...]
    Stores name/category/price at time of order — not a live reference.
    Uses executemany for one efficient DB round-trip.
    """
    rows = [
        (order_id, item.item_id, item.name, item.category, item.price, qty)
        for item, qty in cart
    ]
    conn   = db_conn()
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO order_items "
        "(order_id, item_id, item_name, item_category, item_price, quantity) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        rows
    )
    conn.commit()
    cursor.close(); conn.close()


def insert_payment(order_id: int, method: str, amount: float,
                   payment_details: str = None):
    """Inserts one row into payments table."""
    conn   = db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO payments (order_id, method, amount, transaction_ref) "
        "VALUES (%s, %s, %s, %s)",
        (order_id, method, amount, payment_details)
    )
    conn.commit()
    cursor.close(); conn.close()


def get_orders_by_user(user_id: int) -> list:
    """
    Returns a list of Order objects (each with .items populated).
    Single JOIN query — no N+1 problem.
    """
    conn   = db_conn()
    cursor = conn.cursor(dictionary=True)

    # One query: orders + their items via LEFT JOIN
    cursor.execute(
        """
        SELECT
            o.order_id, o.total_amount, o.status,
            o.payment_method, o.created_at,
            oi.item_id, oi.item_name, oi.item_category,
            oi.item_price, oi.quantity
        FROM orders o
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.user_id = %s
        ORDER BY o.created_at DESC, oi.id
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    cursor.close(); conn.close()

    # Build Order objects, grouping rows by order_id
    orders_map = {}
    for row in rows:
        oid = row["order_id"]
        if oid not in orders_map:
            orders_map[oid] = Order(
                order_id       = oid,
                user_id        = user_id,
                total_amount   = row["total_amount"],
                status         = row["status"],
                payment_method = row["payment_method"],
                created_at     = row["created_at"],
                items          = []
            )
        if row["item_id"] is not None:
            orders_map[oid].items.append(
                OrderItem(
                    item_id  = row["item_id"],
                    name     = row["item_name"],
                    category = row["item_category"],
                    price    = row["item_price"],
                    quantity = row["quantity"]
                )
            )

    return list(orders_map.values())


# ═══════════════════════════════════════════════════════
# BILL + PAYMENT FLOW
# ═══════════════════════════════════════════════════════

def display_bill(cart: list) -> float:
    print("\n" + "=" * 60)
    print("                    BILL SUMMARY")
    print("=" * 60)
    print(f"  {'#':<4} {'Item':<28} {'Cat':<10}  {'Price':>8}")
    print("  " + "─" * 54)

    total = 0.0
    for idx, (item, qty) in enumerate(cart, 1):
        subtotal = item.price * qty
        total   += subtotal
        label    = f"(x{qty})" if qty > 1 else ""
        print(f"  {idx:<4} {item.name:<28} {item.category:<10}  "
              f"Rs.{subtotal:>7.0f}  {label}")

    print("  " + "─" * 54)
    print(f"  {'TOTAL':<50}  Rs.{total:>7.0f}")
    print("=" * 60)
    return total


def choose_payment_method() -> str | None:
    print("\n  Payment Method:")
    print("  1. Cash on Delivery")
    print("  2. Online Payment")
    print("  0. Cancel")
    while True:
        ch = input("\n  Choice: ").strip()
        if ch == "1": return "Cash on Delivery"
        if ch == "2": return "Online Payment"
        if ch == "0": return None
        print("  Enter 1, 2 or 0.")


def simulate_online_payment(total: float) -> str | None:
    """Returns transaction_ref string, or None if cancelled."""
    print(f"\n  ── Online Payment ──")
    print(f"  Amount Due: Rs. {total:.0f}")
    ref = input("  Transaction reference (0 to cancel): ").strip()
    if ref == "0" or not ref:
        print("  Payment cancelled."); return None
    print(f"  ✔ Payment confirmed.  Ref: {ref}")
    return ref


# ═══════════════════════════════════════════════════════
# PLACE ORDER
# ═══════════════════════════════════════════════════════

def place_order(cart: list, user) -> Order | None:
    """
    Accepts cart [(MenuItem, qty)] and a User object.
    Saves order + items + payment to DB.
    Pushes Order object into DLL.
    Returns Order object on success, None if cancelled.
    """
    if not cart:
        print("  Cart is empty."); return None

    total  = display_bill(cart)
    method = choose_payment_method()
    if method is None:
        print("  Order cancelled."); return None

    transaction_ref = None
    if method == "Online Payment":
        transaction_ref = simulate_online_payment(total)
        if transaction_ref is None:
            return None

    confirm = input("\n  Confirm order? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("  Order not placed."); return None

    # Save to DB
    order = insert_order(user.user_id, total, method)
    insert_order_items(order.order_id, cart)
    insert_payment(order.order_id, method, total, transaction_ref)

    # Push into DLL
    history_dll.prepend(order)

    clear_cart()

    print(f"\n  ✔ Order #{order.order_id} placed!")
    print(f"  Method: {method}   |   Total: Rs. {total:.0f}")
    print("  Thank you for your order!\n")
    return order


# ═══════════════════════════════════════════════════════
# ORDER HISTORY  —  DLL
# ═══════════════════════════════════════════════════════

def load_history(user):
    """Fetch from DB, rebuild DLL (newest at head)."""
    history_dll.__init__()
    orders = get_orders_by_user(user.user_id)
    for order in reversed(orders):      # oldest first → prepend → head = newest
        history_dll.prepend(order)


def display_history(user):
    load_history(user)

    if history_dll.is_empty():
        print("\n  No past orders."); return

    print("\n" + "=" * 60)
    print("                 MY ORDER HISTORY")
    print("=" * 60)

    for order in history_dll.newest_first():
        print(f"\n  Order #{order.order_id}   {order.created_at}")
        print("  " + "─" * 54)
        for oi in order.items:
            print(f"    • {oi.name:<28} x{oi.quantity}  Rs.{oi.price * oi.quantity:.0f}")
        print("  " + "─" * 54)
        print(f"  Total: Rs. {order.total_amount:.0f}  |  "
              f"{order.payment_method}  |  {order.status}")

    print("\n" + "=" * 60)


# ═══════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════

def run_payment(cart: list, user) -> str:
    """Returns 'order_placed' or 'back'."""
    while True:
        print("\n" + "╔" + "═" * 44 + "╗")
        print("║         PAYMENT & ORDER PANEL              ║")
        print("╠" + "═" * 44 + "╣")
        print("║  1. View Bill Summary                      ║")
        print("║  2. Place Order & Pay                      ║")
        print("║  3. My Order History  (DLL)                ║")
        print("║  4. Back to Menu & Cart                    ║")
        print("╚" + "═" * 44 + "╝")

        choice = input("\n  Choice: ").strip()

        if choice == "1":
            display_bill(cart)
        elif choice == "2":
            order = place_order(cart, user)
            if order:
                return "order_placed"
        elif choice == "3":
            display_history(user)
        elif choice == "4":
            return "back"
        else:
            print("  Invalid choice.")