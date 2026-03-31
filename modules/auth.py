from db import db_conn
from models import user
import hashlib



def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_form(name, phone, password):

    if not name or not phone or not password:
        return "All fields are required"

    conn = db_conn()
    cursor = conn.cursor()

    
    cursor.execute("SELECT * FROM users WHERE phone = %s", (phone,))
    user = cursor.fetchone()

    if user:
        cursor.close()
        conn.close()
        return "User already exists"

    
    hashed_pass = hash_password(password)

    
    cursor.execute(
        "INSERT INTO users (name, phone, password) VALUES (%s, %s, %s)",
        (name, phone, hashed_pass)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return "Registration Successful"
    

def login_user(phone, password):

    if not phone or not password:
        return None, "All fields are required"

    conn = db_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE phone = %s", (phone,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return None, "User not found"

    
    hashed_pass = hash_password(password)

    if user["password"] != hashed_pass:
        return None, "Incorrect password"

    return user, "Login Successful"




