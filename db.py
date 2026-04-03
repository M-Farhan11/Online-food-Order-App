import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

load_dotenv()
passw = os.getenv("db_pass")
host = os.getenv("db_host")
user = os.getenv("db_user")
db_name = os.getenv("db_name")

if passw is None:
    print("No password Found!")

db_pool = pooling.MySQLConnectionPool(
    pool_name="onlinefood",
    pool_size=10,
    host=host,
    user=user,
    password=passw,
    database=db_name
)

def db_conn():
    return db_pool.get_connection()

