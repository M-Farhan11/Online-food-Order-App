class OrderItem:
    def __init__(self, item_id, name, category, price, quantity):
        self.item_id  = item_id
        self.name     = name
        self.category = category
        self.price    = float(price)
        self.quantity = quantity
