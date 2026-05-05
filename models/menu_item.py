class MenuItem:
    def __init__(self, item_id, name, category, price,
                 available=True, image_path=None):
        self.item_id    = item_id
        self.name       = name
        self.category   = category
        self.price      = float(price)
        self.available  = available
        self.image_path = image_path