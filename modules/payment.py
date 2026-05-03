
from modules.menu import clear_cart
from models.order import Order ,order_item, user 
from db import db_conn
from collections import deque


# ═══════════════════════════════════════════════════════
# DOUBLY LINKED LIST  —  stores Order objects
# ═══════════════════════════════════════════════════════

class OrderNode:
    def __init__(self, order):          # order is an Order object
        self.order = order
        self.prev  = None
        self.next  = None

class OrderHistoryDLL:
    """
    DLL of Order objects.
    HEAD = newest order,  TAIL = oldest order.
    """
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def prepend(self, order):
        """Insert Order object at head (newest first)"""
        node = OrderNode(order)
        if self.head is None:
            self.head = self.tail = node
        else:
            node.next       = self.head
            self.head.prev  = node
            self.head       = node
        self.size += 1

    def newest_first(self):
        """Returns list of Order objects, newest → oldest"""
        result, curr = [], self.head
        while curr:
            result.append(curr.order)
            curr = curr.next
        return result

    def is_empty(self):
        return self.size == 0


# module-level DLL
history_dll = OrderHistoryDLL()


# ═══════════════════════════════════════════════════════
# BILL SUMMARY
# ═══════════════════════════════════════════════════════

def display_bill(cart):
    """
    cart = [(item_dict, qty), ...]
    Prints formatted bill, returns total (float).
    """
    print("\n" + "=" * 60)
    print("                    BILL SUMMARY")
    print("=" * 60)
    print(f"  {'#':<4} {'Item':<28} {'Category':<12}  {'Price':>8}")
    print("  " + "─" * 56)

    total = 0
    for idx, (item, qty) in enumerate(cart, 1):
        subtotal = item["price"] * qty
        total   += subtotal
        label    = f"(x{qty})" if qty > 1 else ""
        print(f"  {idx:<4} {item['name']:<28} {item['category']:<12}  "
              f"Rs. {subtotal:>6.0f}  {label}")

    print("  " + "─" * 56)
    print(f"  {'TOTAL':<52}  Rs. {total:>6.0f}")
    print("=" * 60)
    return total


# ═══════════════════════════════════════════════════════
# PAYMENT METHOD
# ═══════════════════════════════════════════════════════

def choose_payment_method():
    print("\n  Select Payment Method:")
    print("  1. Cash on Delivery")
    print("  2. Online Payment")
    print("  0. Cancel")
    while True:
        ch = input("\n  Enter choice: ").strip()
        if ch == "1": return "Cash on Delivery"
        elif ch == "2": return "Online Payment"
        elif ch == "0": return None
        else: print("  Enter 1, 2 or 0.")


def simulate_online_payment(total):
    print(f"\n  ── Online Payment ──")
    print(f"  Amount Due: Rs. {total:.0f}")
    ref = input("  Enter transaction reference (or 0 to cancel): ").strip()
    if ref == "0" or not ref:
        print("  Payment cancelled.")
        return False
    print(f"  ✔ Payment of Rs. {total:.0f} confirmed.  Ref: {ref}")
    return True


# ═══════════════════════════════════════════════════════
# PLACE ORDER  —  saves Order + OrderItem objects to DB
# ═══════════════════════════════════════════════════════

def place_order(cart, user):
    """
    Accepts cart and User object.
    Creates Order object, saves to DB, pushes to DLL.
    Returns Order object on success, None if cancelled.
    """
    if not cart:
        print("  Cart is empty.")
        return None

    total  = display_bill(cart)
    method = choose_payment_method()
    if method is None:
        print("  Order cancelled.")
        return None

    if method == "Online Payment":
        if not simulate_online_payment(total):
            return None

    print(f"\n  Payment Method : {method}")
    confirm = input("  Confirm order? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("  Order not placed.")
        return None

    # insert_order returns an Order object
    order = insert_order(user.user_id, total, method)
    insert_order_items(order.order_id, cart)

    # update Order object status
    order.status = "Placed"

    # push Order object into DLL
    history_dll.prepend(order)

    clear_cart()

    print(f"\n  ✔ Order #{order.order_id} placed successfully!")
    print(f"  Payment : {method}   |   Total : Rs. {order.total_amount:.0f}")
    print("  Thank you for your order!\n")
    return order


# ═══════════════════════════════════════════════════════
# ORDER HISTORY  —  DLL of Order objects
# ═══════════════════════════════════════════════════════

def load_history(user):
    """
    Fetches Order objects from DB via get_orders_by_user().
    Each Order object already has .items (list of OrderItem objects).
    Rebuilds DLL with newest at head.
    """
    history_dll.__init__()

    orders = get_orders_by_user(user.user_id)   # list of Order objects
    for order in reversed(orders):              # oldest first → prepend → head = newest
        history_dll.prepend(order)


def display_history(user):
    """Loads Order objects from DB into DLL, prints newest → oldest."""
    load_history(user)

    if history_dll.is_empty():
        print("\n  No past orders found.")
        return

    print("\n" + "=" * 60)
    print("                  MY ORDER HISTORY")
    print("=" * 60)

    for order in history_dll.newest_first():
        print(f"\n  Order #{order.order_id}   {order.created_at}")
        print("  " + "─" * 54)
        for oi in order.items:                  # oi = OrderItem object
            print(f"    • {oi.name}  x{oi.quantity}")
        print("  " + "─" * 54)
        print(f"  Total: Rs. {order.total_amount:.0f}  |  "
              f"{order.payment_method}  |  {order.status}")

    print("\n" + "=" * 60)


# ═══════════════════════════════════════════════════════
# PAYMENT MODULE MAIN MENU
# ═══════════════════════════════════════════════════════

def run_payment(cart, user):
    """
    Entry point. Accepts cart + User object.
    Returns "order_placed" or "back".
    """
    while True:
        print("\n" + "╔" + "═" * 44 + "╗")
        print("║          PAYMENT & ORDER PANEL             ║")
        print("╠" + "═" * 44 + "╣")
        print("║  1. View Bill Summary                      ║")
        print("║  2. Place Order & Pay                      ║")
        print("║  3. My Order History  (DLL)                ║")
        print("║  4. Back to Menu & Cart                    ║")
        print("╚" + "═" * 44 + "╝")

        choice = input("\n  Enter choice: ").strip()

        if choice == "1":
            display_bill(cart)

        elif choice == "2":
            order = place_order(cart, user)     # passes User object
            if order:
                return "order_placed"

        elif choice == "3":
            display_history(user)               # passes User object

        elif choice == "4":
            return "back"

        else:
            print("  Invalid choice.")