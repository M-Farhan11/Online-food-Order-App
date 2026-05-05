class Order:
    def __init__(self, order_id, user_id, total_amount,
                 status="Placed", payment_method="Cash on Delivery",
                 created_at=None, items=None):
        self.order_id       = order_id
        self.user_id        = user_id
        self.total_amount   = float(total_amount)
        self.status         = status
        self.payment_method = payment_method
        self.created_at     = created_at    # datetime object or string
        self.items          = items or []   # list of OrderItem objects