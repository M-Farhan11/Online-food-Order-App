# modules/auth.py
import bcrypt
from dotenv import load_dotenv
import os
from db import db_conn
from models.user import User

load_dotenv()

ADMIN_ID   = os.getenv("admin")
ADMIN_PASS = os.getenv("ad_pass")


# ─────────────────────────────────────────────
# PASSWORD HELPERS  (bcrypt)
# ─────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Returns a bcrypt hash string (60 chars)."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ─────────────────────────────────────────────
# CORE LOGIC
# ─────────────────────────────────────────────

def register_user(name: str, phone: str, password: str) -> dict:
    if not all([name, phone, password]):
        return {"status": False, "message": "Fields cannot be empty", "user": None}

    conn   = db_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT user_id FROM users WHERE phone = %s", (phone,))
    if cursor.fetchone():
        cursor.close(); conn.close()
        return {"status": False, "message": "Phone number already registered", "user": None}

    hashed = hash_password(password)
    cursor.execute(
        "INSERT INTO users (name, phone, password) VALUES (%s, %s, %s)",
        (name, phone, hashed)
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close(); conn.close()

    return {
        "status":  True,
        "message": "Registration successful",
        "user":    User(new_id, name, phone)
    }


def login_user(phone: str, password: str) -> dict:
    if not all([phone, password]):
        return {"status": False, "message": "Fields cannot be empty", "user": None}

    conn   = db_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT user_id, name, phone, password FROM users WHERE phone = %s",
        (phone,)
    )
    row = cursor.fetchone()
    cursor.close(); conn.close()

    if not row:
        return {"status": False, "message": "User not found", "user": None}

    if not verify_password(password, row["password"]):
        return {"status": False, "message": "Incorrect password", "user": None}

    return {
        "status":  True,
        "message": "Login successful",
        "user":    User(row["user_id"], row["name"], row["phone"])
    }


def admin_login(admin_id: str, admin_pass: str) -> dict:
    if not all([admin_id, admin_pass]):
        return {"status": False, "message": "Fields cannot be empty"}
    if admin_id != ADMIN_ID or admin_pass != ADMIN_PASS:
        return {"status": False, "message": "Invalid admin credentials"}
    return {"status": True, "message": "Welcome, Admin!"}


# ─────────────────────────────────────────────
# INPUT HANDLERS  (CLI)
# ─────────────────────────────────────────────

def handle_register() -> tuple:
    while True:
        name = input("  Name: ").strip()
        if not name:
            print("  Name cannot be empty."); continue
        if not all(p.isalpha() for p in name.split()):
            print("  Name must contain letters only."); continue
        break

    while True:
        phone = input("  Phone (11 digits): ").strip()
        if not phone.isdigit() or len(phone) != 11:
            print("  Enter exactly 11 digits."); continue
        break

    while True:
        password = input("  Password (min 8 chars): ").strip()
        if len(password) < 8:
            print("  Password too short."); continue
        break

    return name, phone, password


def handle_login() -> tuple:
    while True:
        phone = input("  Phone: ").strip()
        if not phone.isdigit() or len(phone) != 11:
            print("  Enter exactly 11 digits."); continue
        break

    while True:
        password = input("  Password: ").strip()
        if not password:
            print("  Password cannot be empty."); continue
        break

    return phone, password


def handle_admin_login() -> tuple:
    admin_id   = input("  Admin ID: ").strip()
    admin_pass = input("  Password: ").strip()
    return admin_id, admin_pass


# ─────────────────────────────────────────────
# CLI ENTRY
# ─────────────────────────────────────────────

def main():
    print("\n=== User Authentication ===")
    while True:
        print("\n  1. Login")
        print("  2. Register")
        print("  3. Admin Login")
        print("  4. Exit")

        choice = input("\n  Choice: ").strip()
        if not choice.isdigit():
            print("  Digits only."); continue

        if choice == "1":
            phone, password = handle_login()
            result = login_user(phone, password)
            print(f"\n  {result['message']}")
            if result["status"]:
                print(f"  Welcome, {result['user'].name}!")

        elif choice == "2":
            name, phone, password = handle_register()
            result = register_user(name, phone, password)
            print(f"\n  {result['message']}")

        elif choice == "3":
            admin_id, admin_pass = handle_admin_login()
            result = admin_login(admin_id, admin_pass)
            print(f"\n  {result['message']}")

        elif choice == "4":
            break
        else:
            print("  Invalid choice.")


if __name__ == "__main__":
    main()