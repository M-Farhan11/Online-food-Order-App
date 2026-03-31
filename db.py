import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

load_dotenv()
passw = os.getenv("db_pass")

if passw is None:
    print("No password Found!")

db_pool = pooling.MySQLConnectionPool(
    pool_name="onlinefood",
    pool_size=10,
    host="localhost",
    user="root",
    password=passw,
    database="online_food_app"
)

def db_conn():
    return db_pool.get_connection()

