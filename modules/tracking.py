from db import db_conn
from collections import deque
import time

# ---------------- DATA STRUCTURES ---------------- #

order_queue = deque()

STATUS_FLOW = [
    "Placed",
    "Preparing",
    "Out for Delivery",
    "Delivered"
]

# ---------------- VALIDATION ---------------- #

def is_valid_order(order_id):
    conn = db_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()

    cursor.close()
    conn.close()

    return order


# ---------------- ADD ORDER TO TRACKING ---------------- #

def add_order(order_id):
    order = is_valid_order(order_id)

    if not order:
        return "Invalid Order ID"

    if order["status"] == "Delivered":
        return "Order already delivered"

    order_queue.append(order_id)
    return "Order added to tracking"


# ---------------- UPDATE ORDER STATUS ---------------- #

def update_status(order_id):

    conn = db_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT status FROM orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()

    if not order:
        cursor.close()
        conn.close()
        return

    current_status = order["status"]

    try:
        index = STATUS_FLOW.index(current_status)
    except ValueError:
        index = 0

    # Move to next status if not delivered
    if index < len(STATUS_FLOW) - 1:
        new_status = STATUS_FLOW[index + 1]

        cursor.execute(
            "UPDATE orders SET status = %s WHERE order_id = %s",
            (new_status, order_id)
        )
        conn.commit()

    cursor.close()
    conn.close()


# ---------------- PROCESS QUEUE ---------------- #

def process_orders():

    if not order_queue:
        print("No orders to process")
        return

    order_id = order_queue.popleft()

    update_status(order_id)

    # Check updated status
    conn = db_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT status FROM orders WHERE order_id = %s", (order_id,))
    order = cursor.fetchone()

    cursor.close()
    conn.close()

    if order and order["status"] != "Delivered":
        order_queue.append(order_id)


# ---------------- TRACK ORDER ---------------- #

def track_order(order_id):

    order = is_valid_order(order_id)

    if not order:
        return "Invalid Order ID"

    return f"Order Status: {order['status']}"