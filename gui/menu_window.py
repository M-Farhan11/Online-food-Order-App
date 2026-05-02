# Online Food Order System - Food Menu


from collections import deque
from datetime import datetime


# --- given model ---

class OrderItem:
    def __init__(self, item_id, name, category, price):
        self.item_id = item_id
        self.name = name
        self.category = category
        self.price = price


# -------------------------------------------------------
# DATA STRUCTURES
# -------------------------------------------------------

# Dictionary - stores all menu items, key = item_id
menu = {}

# Dictionary - groups item_ids by category
categories = {}

# List - cart holds (OrderItem, quantity) tuples
cart = []

# Stack (list) - tracks cart actions for undo (LIFO)
undo_stack = []

# Queue (deque) - holds placed orders for processing (FIFO)
order_queue = deque()

# simple counter for order IDs
order_counter = 1


# -------------------------------------------------------
# MENU FUNCTIONS
# -------------------------------------------------------

def add_to_menu(item):
    # store item in dictionary by item_id
    menu[item.item_id] = item

    # also add item_id under its category in categories dictionary
    if item.category not in categories:
        categories[item.category] = []
    categories[item.category].append(item.item_id)


def display_menu():
    print("\n" + "=" * 50)
    print("         ONLINE FOOD ORDER SYSTEM")
    print("=" * 50)
    for category, ids in categories.items():
        print(f"\n  -- {category} --")
        for item_id in ids:
            item = menu[item_id]
            print(f"  [{item.item_id}]  {item.name:<25}  PKR {item.price:.2f}")
    print("\n" + "=" * 50)


def search_item(keyword):
    # linear search through all items in the dictionary
    results = []
    for item in menu.values():
        if keyword.lower() in item.name.lower():
            results.append(item)
    return results


# -------------------------------------------------------
# CART FUNCTIONS
# -------------------------------------------------------

def add_to_cart(item_id, qty):
    if item_id not in menu:
        print("Item not found in menu.")
        return

    item = menu[item_id]

    # check if item already in cart list, update qty if so
    for i, (cart_item, q) in enumerate(cart):
        if cart_item.item_id == item_id:
            cart[i] = (cart_item, q + qty)
            undo_stack.append(("add", item_id, qty))  # push to stack
            print(f"Updated '{item.name}' quantity to {q + qty}")
            return

    cart.append((item, qty))
    undo_stack.append(("add", item_id, qty))  # push to stack
    print(f"Added to cart: {item.name} x{qty}")


def remove_from_cart(item_id):
    for i, (item, qty) in enumerate(cart):
        if item.item_id == item_id:
            cart.pop(i)
            undo_stack.append(("remove", item_id, qty))  # push to stack
            print(f"Removed '{item.name}' from cart.")
            return
    print("Item not found in cart.")


def undo_last_action():
    # pop last action from stack and reverse it (LIFO)
    if not undo_stack:
        print("Nothing to undo.")
        return

    action, item_id, qty = undo_stack.pop()  # pop from stack

    if action == "add":
        for i, (item, q) in enumerate(cart):
            if item.item_id == item_id:
                new_qty = q - qty
                if new_qty <= 0:
                    cart.pop(i)
                else:
                    cart[i] = (item, new_qty)
                print(f"Undo: removed '{item.name}' x{qty} from cart")
                return

    elif action == "remove":
        item = menu[item_id]
        cart.append((item, qty))
        print(f"Undo: restored '{item.name}' x{qty} to cart")


def get_cart_total():
    return sum(item.price * qty for item, qty in cart)


def display_cart():
    print("\n  --- Your Cart ---")
    if not cart:
        print("  (empty)")
    else:
        for item, qty in cart:
            subtotal = item.price * qty
            print(f"  [{item.item_id}]  {item.name:<25} x{qty}   PKR {subtotal:.2f}")
    print(f"  {'':->42}")
    print(f"  {'Total:':<30}   PKR {get_cart_total():.2f}")


# -------------------------------------------------------
# ORDER FUNCTIONS
# -------------------------------------------------------

def place_order(customer_name):
    global order_counter

    if not cart:
        print("Cart is empty. Add some items first.")
        return

    order = {
        "order_id": f"ORD-{order_counter:04d}",
        "customer": customer_name,
        "items": list(cart),       # copy current cart into order
        "total": get_cart_total(),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Queued"
    }

    order_queue.append(order)   # enqueue (FIFO)
    order_counter += 1
    cart.clear()
    undo_stack.clear()
    print(f"\nOrder {order['order_id']} placed for {customer_name}!")
    print(f"Total: PKR {order['total']:.2f}")


def process_next_order():
    if not order_queue:
        print("No pending orders.")
        return

    order = order_queue.popleft()   # dequeue
    order["status"] = "Processed"
    print(f"\nProcessing {order['order_id']} for {order['customer']}:")
    for item, qty in order["items"]:
        print(f"   - {item.name} x{qty}")
    print(f"   Total: PKR {order['total']:.2f}")
    print(f"   Time: {order['time']}")
    print(f"   Status: {order['status']}")


# -------------------------------------------------------
# MENU SETUP
# -------------------------------------------------------

def load_default_menu():
    default_items = [
        OrderItem("B001", "Classic Beef Burger",   "Burgers", 450.0),
        OrderItem("B002", "Crispy Chicken Burger", "Burgers", 400.0),
        OrderItem("B003", "Double Smash Burger",   "Burgers", 650.0),
        OrderItem("P001", "Margherita Pizza",      "Pizzas",  700.0),
        OrderItem("P002", "BBQ Chicken Pizza",     "Pizzas",  850.0),
        OrderItem("P003", "Veggie Supreme Pizza",  "Pizzas",  750.0),
        OrderItem("D001", "Fresh Lemonade",        "Drinks",  150.0),
        OrderItem("D002", "Mango Shake",           "Drinks",  200.0),
        OrderItem("D003", "Cola Can",              "Drinks",   80.0),
        OrderItem("S001", "French Fries (Large)",  "Sides",   220.0),
        OrderItem("S002", "Onion Rings",           "Sides",   180.0),
    ]
    for item in default_items:
        add_to_menu(item)


# -------------------------------------------------------
# INTERACTIVE MENUS
# -------------------------------------------------------

def customer_menu(customer_name):
    while True:
        print("\n--- Customer Menu ---")
        print("  1. View menu")
        print("  2. Search item")
        print("  3. Add item to cart")
        print("  4. Remove item from cart")
        print("  5. View cart")
        print("  6. Undo last action")
        print("  7. Place order")
        print("  8. Go back")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            display_menu()

        elif choice == "2":
            keyword = input("Search: ").strip()
            results = search_item(keyword)
            if results:
                for item in results:
                    print(f"  [{item.item_id}]  {item.name:<25}  PKR {item.price:.2f}")
            else:
                print("No items found.")

        elif choice == "3":
            display_menu()
            item_id = input("Enter item ID: ").strip().upper()
            try:
                qty = int(input("Quantity: ").strip())
                if qty <= 0:
                    print("Quantity must be at least 1.")
                    continue
            except ValueError:
                print("Invalid quantity.")
                continue
            add_to_cart(item_id, qty)

        elif choice == "4":
            display_cart()
            item_id = input("Enter item ID to remove: ").strip().upper()
            remove_from_cart(item_id)

        elif choice == "5":
            display_cart()

        elif choice == "6":
            undo_last_action()

        elif choice == "7":
            display_cart()
            if not cart:
                continue
            confirm = input("Confirm order? (yes/no): ").strip().lower()
            if confirm == "yes":
                place_order(customer_name)
                break
            else:
                print("Order not placed. You can keep editing your cart.")

        elif choice == "8":
            break

        else:
            print("Invalid choice.")


def admin_menu():
    while True:
        print("\n--- Admin Panel ---")
        print("  1. View full menu")
        print("  2. Add new item to menu")
        print("  3. Process next order")
        print("  4. View pending orders count")
        print("  5. Go back")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            display_menu()

        elif choice == "2":
            print("\nEnter new item details:")
            item_id = input("  Item ID: ").strip().upper()
            name = input("  Name: ").strip()
            category = input("  Category: ").strip()
            try:
                price = float(input("  Price (PKR): ").strip())
            except ValueError:
                print("Invalid price.")
                continue
            new_item = OrderItem(item_id, name, category, price)
            add_to_menu(new_item)
            print(f"'{name}' added to menu.")

        elif choice == "3":
            process_next_order()

        elif choice == "4":
            print(f"Pending orders: {len(order_queue)}")

        elif choice == "5":
            break

        else:
            print("Invalid choice.")


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------

def main():
    load_default_menu()

    print("\n" + "=" * 45)
    print("   Welcome to the Online Food Order System")
    print("=" * 45)

    while True:
        print("\n--- Main Menu ---")
        print("  1. Customer")
        print("  2. Admin")
        print("  3. Exit")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            name = input("Enter your name: ").strip()
            if not name:
                name = "Guest"
            customer_menu(name)

        elif choice == "2":
            admin_menu()

        elif choice == "3":
            print("\nThank you for choosing us. SEEYA NEXT TIME!")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
