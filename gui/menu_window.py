# Online Food Order System - Food Menu

from collections import deque
from datetime import datetime


# --- MenuItem class ---

class MenuItem:
    def __init__(self, item_id, name, price, category, description="", available=True):
        self.item_id = item_id
        self.name = name
        self.price = price
        self.category = category
        self.description = description
        self.available = available

    def __repr__(self):
        status = "Available" if self.available else "Unavailable"
        return f"  [{self.item_id}] {self.name:<26} PKR {self.price:>7.2f}   ({status})"


# --- Menu class ---

class Menu:
    def __init__(self):
        self.items = {}       # dict: item_id -> MenuItem
        self.categories = {}  # dict: category -> list of item_ids

    def add_item(self, item):
        if item.item_id in self.items:
            print(f"Item {item.item_id} already exists.")
            return
        self.items[item.item_id] = item
        if item.category not in self.categories:
            self.categories[item.category] = []
        self.categories[item.category].append(item.item_id)

    def remove_item(self, item_id):
        if item_id not in self.items:
            print("Item not found.")
            return
        item = self.items.pop(item_id)
        self.categories[item.category].remove(item_id)
        print(f"Removed: {item.name}")

    def update_price(self, item_id, new_price):
        if item_id not in self.items:
            print("Item not found.")
            return
        old_price = self.items[item_id].price
        self.items[item_id].price = new_price
        print(f"Price updated for {self.items[item_id].name}: PKR {old_price} -> PKR {new_price}")

    def toggle_availability(self, item_id):
        if item_id not in self.items:
            print("Item not found.")
            return
        item = self.items[item_id]
        item.available = not item.available
        state = "available" if item.available else "unavailable"
        print(f"'{item.name}' is now {state}.")

    def get_item(self, item_id):
        return self.items.get(item_id)

    def search(self, keyword):
        # linear search through item names
        results = []
        for item in self.items.values():
            if keyword.lower() in item.name.lower():
                results.append(item)
        return results

    def get_by_category(self, category):
        ids = self.categories.get(category, [])
        return [self.items[i] for i in ids]

    def display(self):
        print("\n" + "=" * 55)
        print("        ONLINE FOOD ORDER SYSTEM - MENU")
        print("=" * 55)
        for category, ids in self.categories.items():
            print(f"\n  -- {category} --")
            for item_id in ids:
                print(self.items[item_id])
        print("\n" + "=" * 55)


# --- Cart class ---

class Cart:
    def __init__(self):
        self.cart_items = []  # list of (MenuItem, quantity)
        self.undo_stack = []  # stack for undo

    def add(self, item, qty=1):
        if not item.available:
            print(f"Sorry, '{item.name}' is not available right now.")
            return

        # if item is already in cart, increase quantity
        for i, (m, q) in enumerate(self.cart_items):
            if m.item_id == item.item_id:
                self.cart_items[i] = (m, q + qty)
                self.undo_stack.append(("add", item, qty))  # push
                print(f"Updated '{item.name}' quantity to {q + qty}")
                return

        self.cart_items.append((item, qty))
        self.undo_stack.append(("add", item, qty))  # push
        print(f"Added to cart: {item.name} x{qty}")

    def remove(self, item_id):
        for i, (item, qty) in enumerate(self.cart_items):
            if item.item_id == item_id:
                self.cart_items.pop(i)
                self.undo_stack.append(("remove", item, qty))  # push
                print(f"Removed '{item.name}' from cart.")
                return
        print("That item isn't in your cart.")

    def undo(self):
        # reverses the last cart action using the stack
        if not self.undo_stack:
            print("Nothing to undo.")
            return

        action, item, qty = self.undo_stack.pop()  # pop

        if action == "add":
            self.cart_items = [
                (m, q - qty) if m.item_id == item.item_id else (m, q)
                for m, q in self.cart_items
            ]
            self.cart_items = [(m, q) for m, q in self.cart_items if q > 0]
            print(f"Undo: removed '{item.name}' x{qty} from cart")

        elif action == "remove":
            self.cart_items.append((item, qty))
            print(f"Undo: restored '{item.name}' x{qty} to cart")

    def total(self):
        return sum(item.price * qty for item, qty in self.cart_items)

    def display(self):
        print("\n  --- Your Cart ---")
        if not self.cart_items:
            print("  (empty)")
        else:
            for item, qty in self.cart_items:
                subtotal = item.price * qty
                print(f"  {item.name:<28} x{qty}   PKR {subtotal:.2f}")
        print(f"  {'':->44}")
        print(f"  {'Total:':<28}        PKR {self.total():.2f}")

    def clear(self):
        self.cart_items.clear()
        self.undo_stack.clear()


# --- OrderQueue class ---

class OrderQueue:
    def __init__(self):
        self.queue = deque()  # queue for pending orders
        self.order_counter = 1

    def place_order(self, customer_name, cart):
        if not cart.cart_items:
            print("Your cart is empty. Add some items first.")
            return {}

        order = {
            "order_id": f"ORD-{self.order_counter:04d}",
            "customer": customer_name,
            "items": list(cart.cart_items),
            "total": cart.total(),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Queued"
        }

        self.queue.append(order)  # enqueue
        self.order_counter += 1
        cart.clear()
        print(f"\nOrder {order['order_id']} placed successfully for {customer_name}!")
        print(f"Total: PKR {order['total']:.2f}")
        return order

    def process_next(self):
        if not self.queue:
            print("No pending orders.")
            return

        order = self.queue.popleft()  # dequeue
        order["status"] = "Processed"
        print(f"\nProcessing {order['order_id']} for {order['customer']}:")
        for item, qty in order["items"]:
            print(f"   - {item.name} x{qty}")
        print(f"   Total: PKR {order['total']:.2f}")
        print(f"   Ordered at: {order['time']}")
        print(f"   Status: {order['status']}")

    def pending_count(self):
        return len(self.queue)

    def peek(self):
        if self.queue:
            o = self.queue[0]
            print(f"Next in queue: {o['order_id']} ({o['customer']})")
        else:
            print("No orders in queue.")


# --- helper to load the default menu items ---

def load_menu(menu):
    items = [
        MenuItem("B001", "Classic Beef Burger",   450.0, "Burgers", "beef patty with lettuce and tomato"),
        MenuItem("B002", "Crispy Chicken Burger", 400.0, "Burgers", "fried chicken fillet"),
        MenuItem("B003", "Double Smash Burger",   650.0, "Burgers", "two smashed beef patties"),
        MenuItem("P001", "Margherita Pizza",      700.0, "Pizzas",  "tomato base with mozzarella"),
        MenuItem("P002", "BBQ Chicken Pizza",     850.0, "Pizzas",  "BBQ sauce, chicken, peppers"),
        MenuItem("P003", "Veggie Supreme Pizza",  750.0, "Pizzas",  "mixed veggies on tomato base"),
        MenuItem("D001", "Fresh Lemonade",        150.0, "Drinks",  "chilled homemade lemonade"),
        MenuItem("D002", "Mango Shake",           200.0, "Drinks",  "thick mango milkshake"),
        MenuItem("D003", "Cola Can",               80.0, "Drinks",  "330ml cold cola"),
        MenuItem("S001", "French Fries (Large)",  220.0, "Sides",   "crispy golden fries"),
        MenuItem("S002", "Onion Rings",           180.0, "Sides",   "battered onion rings"),
    ]
    for item in items:
        menu.add_item(item)


# --- interactive session for customer ---

def customer_session(menu, order_queue, customer_name):
    cart = Cart()

    while True:
        print("\n--- What would you like to do? ---")
        print("  1. View menu")
        print("  2. Search for an item")
        print("  3. Add item to cart")
        print("  4. Remove item from cart")
        print("  5. View cart")
        print("  6. Undo last cart action")
        print("  7. Place order")
        print("  8. Back to main menu")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            menu.display()

        elif choice == "2":
            keyword = input("Enter item name to search: ").strip()
            results = menu.search(keyword)
            if results:
                print(f"\nResults for '{keyword}':")
                for item in results:
                    print(item)
            else:
                print("No items found.")

        elif choice == "3":
            menu.display()
            item_id = input("Enter item ID to add (e.g. B001): ").strip().upper()
            item = menu.get_item(item_id)
            if not item:
                print("Invalid item ID.")
                continue
            try:
                qty = int(input(f"How many '{item.name}'? ").strip())
                if qty <= 0:
                    print("Quantity must be at least 1.")
                    continue
            except ValueError:
                print("Please enter a valid number.")
                continue
            cart.add(item, qty)

        elif choice == "4":
            cart.display()
            if not cart.cart_items:
                continue
            item_id = input("Enter item ID to remove: ").strip().upper()
            cart.remove(item_id)

        elif choice == "5":
            cart.display()

        elif choice == "6":
            cart.undo()

        elif choice == "7":
            cart.display()
            if not cart.cart_items:
                continue
            confirm = input("\nConfirm order? (yes/no): ").strip().lower()
            if confirm == "yes":
                order_queue.place_order(customer_name, cart)
                print("Your order is in the queue!")
                break
            else:
                print("Order cancelled. You can keep editing your cart.")

        elif choice == "8":
            print("Going back to main menu.")
            break

        else:
            print("Invalid choice, please try again.")


# --- admin panel ---

def admin_panel(menu, order_queue):
    while True:
        print("\n--- Admin Panel ---")
        print("  1. View full menu")
        print("  2. Add new menu item")
        print("  3. Remove menu item")
        print("  4. Update item price")
        print("  5. Toggle item availability")
        print("  6. Process next order")
        print("  7. View pending orders count")
        print("  8. Back to main menu")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            menu.display()

        elif choice == "2":
            print("\nEnter new item details:")
            item_id = input("  Item ID: ").strip().upper()
            name = input("  Name: ").strip()
            try:
                price = float(input("  Price (PKR): ").strip())
            except ValueError:
                print("Invalid price.")
                continue
            category = input("  Category: ").strip()
            description = input("  Description (optional): ").strip()
            new_item = MenuItem(item_id, name, price, category, description)
            menu.add_item(new_item)
            print(f"'{name}' added to menu.")

        elif choice == "3":
            menu.display()
            item_id = input("Enter item ID to remove: ").strip().upper()
            menu.remove_item(item_id)

        elif choice == "4":
            menu.display()
            item_id = input("Enter item ID to update price: ").strip().upper()
            try:
                new_price = float(input("Enter new price (PKR): ").strip())
            except ValueError:
                print("Invalid price.")
                continue
            menu.update_price(item_id, new_price)

        elif choice == "5":
            menu.display()
            item_id = input("Enter item ID to toggle availability: ").strip().upper()
            menu.toggle_availability(item_id)

        elif choice == "6":
            order_queue.process_next()

        elif choice == "7":
            print(f"Pending orders in queue: {order_queue.pending_count()}")
            order_queue.peek()

        elif choice == "8":
            break

        else:
            print("Invalid choice.")


# --- main ---

def main():
    print("\n" + "=" * 45)
    print("    Welcome to the Online Food Order System")
    print("=" * 45)

    menu = Menu()
    order_queue = OrderQueue()
    load_menu(menu)

    while True:
        print("\n--- Main Menu ---")
        print("  1. I'm a customer")
        print("  2. Admin panel")
        print("  3. Exit")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            name = input("Enter your name: ").strip()
            if not name:
                name = "Guest"
            customer_session(menu, order_queue, name)

        elif choice == "2":
            admin_panel(menu, order_queue)

        elif choice == "3":
            print("\nThank you for choosing us, hope you have a wonderful day! SEEYA NEXT TIME!")
            break

        else:
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main()
