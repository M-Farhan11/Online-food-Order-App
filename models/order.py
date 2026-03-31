class Order:

    def __init__(self, order_id, user_id, total_amount, status="Placed"):
        self.order_id = order_id
        self.user_id = user_id
        self.total_amount = total_amount
        self.status = status