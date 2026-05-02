from modules.tracking import add_order, process_orders, track_order
import time
from db import db_conn
import mysql.connector
order_id = int(input("Enter Order ID: "))

print(add_order(order_id))

for i in range(4):
    msg = add_order(order_id)

    if "Invalid" in msg:
        exit()
    time.sleep(3)
    process_orders()
    print(track_order(order_id))