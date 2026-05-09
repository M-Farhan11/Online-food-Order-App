# modules/tracking.py
from collections import deque
import threading
from db import db_conn

# ═══════════════════════════════════════════════════════
# DATA STRUCTURES  —  do not change
# ═══════════════════════════════════════════════════════

order_queue = deque()   # FIFO queue of order_ids being tracked

STATUS_FLOW = [
    "Placed",
    "Preparing",
    "Out for Delivery",
    "Delivered"
]

_auto_timers = {}
_timer_lock  = threading.Lock()


# ═══════════════════════════════════════════════════════
# DB HELPERS
# ═══════════════════════════════════════════════════════

def _get_order(order_id: int) -> dict | None:
    conn   = db_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT order_id, user_id, status, payment_method, created_at "
        "FROM orders WHERE order_id = %s",
        (order_id,)
    )
    row = cursor.fetchone()
    cursor.close(); conn.close()
    return row


def _get_status(order_id: int) -> str | None:
    conn   = db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT status FROM orders WHERE order_id = %s", (order_id,)
    )
    row = cursor.fetchone()
    cursor.close(); conn.close()
    return row[0] if row else None


def _set_status(order_id: int, new_status: str):
    conn   = db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE orders SET status = %s WHERE order_id = %s",
        (new_status, order_id)
    )
    conn.commit()
    cursor.close(); conn.close()


# ═══════════════════════════════════════════════════════
# AUTO-TIMER  (background status progression)
# ═══════════════════════════════════════════════════════

def _schedule_auto_update(order_id: int):
    with _timer_lock:
        if order_id in _auto_timers:
            return
        timer = threading.Timer(
            10.0, _auto_update_status, args=(order_id,))
        timer.daemon = True
        _auto_timers[order_id] = timer
        timer.start()


def _cancel_auto_update(order_id: int):
    with _timer_lock:
        timer = _auto_timers.pop(order_id, None)
    if timer:
        timer.cancel()


def _auto_update_status(order_id: int):
    with _timer_lock:
        _auto_timers.pop(order_id, None)

    status = _get_status(order_id)
    if status is None or status not in ("Preparing", "Out for Delivery"):
        return

    try:
        idx = STATUS_FLOW.index(status)
    except ValueError:
        return

    if idx < len(STATUS_FLOW) - 1:
        new_status = STATUS_FLOW[idx + 1]
        _set_status(order_id, new_status)
        if new_status != "Delivered":
            _schedule_auto_update(order_id)


# ═══════════════════════════════════════════════════════
# QUEUE OPERATIONS  (DSA)
# ═══════════════════════════════════════════════════════

def add_order_to_queue(order_id: int) -> str:
    order = _get_order(order_id)
    if not order:
        return f"Order #{order_id} not found."
    if order["status"] == "Delivered":
        return f"Order #{order_id} is already delivered."
    if order_id in order_queue:
        return f"Order #{order_id} is already in the queue."
    order_queue.append(order_id)
    return f"Order #{order_id} added to tracking queue."


def process_next_order() -> str:
    if not order_queue:
        return "No orders in queue."

    order_id = order_queue.popleft()
    current  = _get_status(order_id)

    if current is None:
        return f"Order #{order_id} no longer exists in DB."

    try:
        idx = STATUS_FLOW.index(current)
    except ValueError:
        idx = 0

    if idx < len(STATUS_FLOW) - 1:
        new_status = STATUS_FLOW[idx + 1]
        _set_status(order_id, new_status)
        msg = f"Order #{order_id}: {current} → {new_status}"
    else:
        new_status = current
        msg = f"Order #{order_id} is already Delivered."

    if new_status != "Delivered":
        order_queue.append(order_id)

    return msg


# ═══════════════════════════════════════════════════════
# ADMIN ORDER MANAGEMENT
# ═══════════════════════════════════════════════════════

def get_orders_by_status(status: str | None = None) -> list:
    """
    Returns list of order dicts.
    Pass None to get ALL orders regardless of status.
    """
    conn   = db_conn()
    cursor = conn.cursor(dictionary=True)
    if status is None:
        cursor.execute(
            "SELECT order_id, user_id, total_amount, status, "
            "payment_method, created_at "
            "FROM orders ORDER BY created_at DESC"
        )
    else:
        cursor.execute(
            "SELECT order_id, user_id, total_amount, status, "
            "payment_method, created_at "
            "FROM orders WHERE status = %s "
            "ORDER BY created_at DESC",
            (status,)
        )
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows


def confirm_order(order_id: int) -> str:
    """
    Admin confirms an order.

    Accepted from statuses:
      - "Placed"          → Cash on Delivery order waiting to start
      - "Payment Pending" → Online order whose payment details have been
                            verified by admin; payment is NEVER declined
                            (semester project model — we assume payment valid)

    In both cases the order moves to "Preparing" and the auto-timer starts
    to progress it through Out for Delivery → Delivered automatically.
    """
    order = _get_order(order_id)
    if not order:
        return f"Order #{order_id} not found."

    confirmable = ("Placed", "Payment Pending")
    if order["status"] not in confirmable:
        return (f"Order #{order_id} cannot be confirmed from "
                f"status '{order['status']}'.")

    _set_status(order_id, "Preparing")
    _schedule_auto_update(order_id)    # starts 10-second progression timer

    if order["status"] == "Payment Pending":
        return (f"Order #{order_id} — online payment verified. "
                f"Status set to Preparing.")
    return f"Order #{order_id} confirmed. Status set to Preparing."


def cancel_order(order_id: int) -> str:
    """
    Admin cancels an order.
    Cannot cancel orders that are already Delivered or already Cancelled.
    """
    order = _get_order(order_id)
    if not order:
        return f"Order #{order_id} not found."
    if order["status"] == "Delivered":
        return f"Order #{order_id} is already Delivered and cannot be cancelled."
    if order["status"] == "Cancelled":
        return f"Order #{order_id} is already cancelled."

    _cancel_auto_update(order_id)
    _set_status(order_id, "Cancelled")
    return f"Order #{order_id} has been cancelled."


# ═══════════════════════════════════════════════════════
# CUSTOMER TRACKING
# ═══════════════════════════════════════════════════════

def track_order(order_id: int) -> str:
    status = _get_status(order_id)
    if status is None:
        return f"Order #{order_id} not found."
    in_queue   = order_id in order_queue   # linear search through deque (DSA)
    queue_note = " (in processing queue)" if in_queue else ""
    return f"Order #{order_id} — Status: {status}{queue_note}"


def get_queue_snapshot() -> list:
    return list(order_queue)


# ═══════════════════════════════════════════════════════
# CLI MENUS
# ═══════════════════════════════════════════════════════

def customer_tracking_menu(user):
    while True:
        print("\n  ── Order Tracking ──")
        print("  1. Track an order by ID")
        print("  2. Back")
        choice = input("\n  Choice: ").strip()

        if choice == "1":
            try:
                order_id = int(input("  Enter Order ID: ").strip())
            except ValueError:
                print("  Invalid ID."); continue
            order = _get_order(order_id)
            if not order:
                print(f"  Order #{order_id} not found.")
            elif order["user_id"] != user.user_id:
                print("  This order does not belong to your account.")
            else:
                print(track_order(order_id))

        elif choice == "2":
            break
        else:
            print("  Invalid choice.")


def admin_tracking_menu():
    while True:
        print("\n  ── Admin: Order Tracking ──")
        print("  1. Add order to queue")
        print("  2. Process next order (advance status)")
        print("  3. View queue")
        print("  4. Track specific order")
        print("  5. Confirm order (Placed / Payment Pending → Preparing)")
        print("  6. Cancel order")
        print("  7. Back")
        choice = input("\n  Choice: ").strip()

        if choice == "1":
            try: order_id = int(input("  Order ID: ").strip())
            except ValueError: print("  Invalid ID."); continue
            print(add_order_to_queue(order_id))

        elif choice == "2":
            print(process_next_order())

        elif choice == "3":
            snap = get_queue_snapshot()
            if not snap: print("  Queue is empty.")
            else: print("  Queue: " + " → ".join(f"#{i}" for i in snap))

        elif choice == "4":
            try: order_id = int(input("  Order ID: ").strip())
            except ValueError: print("  Invalid ID."); continue
            print(track_order(order_id))

        elif choice == "5":
            try: order_id = int(input("  Order ID: ").strip())
            except ValueError: print("  Invalid ID."); continue
            print(confirm_order(order_id))

        elif choice == "6":
            try: order_id = int(input("  Order ID: ").strip())
            except ValueError: print("  Invalid ID."); continue
            print(cancel_order(order_id))

        elif choice == "7":
            break
        else:
            print("  Invalid choice.")