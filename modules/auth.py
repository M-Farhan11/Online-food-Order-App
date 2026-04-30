from db import db_conn
from models import user
import hashlib
from dotenv import load_dotenv
import os

load_dotenv()
admin_id = os.getenv("admin")
admin_pass = os.getenv("ad_pass")



def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(name, phone, password):

    if not name or not phone or not password:
        return {"status" : False, "message" : "Fields cannot be empty", "user" : None}

    conn = db_conn()
    cursor = conn.cursor()

    
    cursor.execute("SELECT * FROM users WHERE phone = %s", (phone,))
    user = cursor.fetchone()

    if user:
        cursor.close()
        conn.close()
        return {"status" : False , "message": "User already exists" , "user" : "\nDuplicate"}

    
    hashed_pass = hash_password(password)

    
    cursor.execute(
        "INSERT INTO users (name, phone, password) VALUES (%s, %s, %s)",
        (name, phone, hashed_pass)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return {
            "status" : True , 
            "message" : "Registeration Successful ",
            "user" : {
                    "name" : name ,
                    "phone" : phone
            }
    }
    

def login_user(phone, password):

    if not phone or not password:
        return {"status" : False, "message" : "Fields cannot be empty" , "user" : None}

    conn = db_conn()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE phone = %s", (phone,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return {"status" : False, "message": "User Not Found" , "user" : None}

    
    hashed_pass = hash_password(password)

    if user["password"] != hashed_pass:
        return {"status" : False, "message" : "Incorrect Password" , "user" : None}

    return {
        "status" : True,
        "message" : "Login Successful",
        "user": user
    }




def handle_reg():
    while True:
<<<<<<< HEAD
        name = input("Enter Your name: ")
=======
        name = input("Enter Your name: ").strip()
>>>>>>> d9bf6c013eb25f9492ab7f388ea2cfd98c2796dd
        if not name:
            print("Name cannot be empty")
            continue
        if not all(part.isalpha() for part in name.split()):
            print("Name should contain only alphabets and spaces")
            continue

        break

    while True:
        
<<<<<<< HEAD
        phone = input("Enter your phone number: ")
=======
        phone = input("Enter your phone number: ").strip()
>>>>>>> d9bf6c013eb25f9492ab7f388ea2cfd98c2796dd
        if not phone.isdigit():
            print("Only digits allowed")
            continue  
        if len(phone)!= 11:
            print("Phone can only have 11 numbers")
<<<<<<< HEAD
=======
            continue
>>>>>>> d9bf6c013eb25f9492ab7f388ea2cfd98c2796dd
        break
        

    while True:
        
        password = input("Enter your password: ").strip()
        if len(password) <8:
            print("Password should be above 8 charachters")
            continue
        break

    return name , phone , password      

<<<<<<< HEAD

name, phone, password = handle_reg()
result = register_form(name, phone, password)
print(result)
=======
def handle_login():
    while True:
        
        phone = input("Enter your phone number(11 digits allowed only: ").strip()
        if not phone:
            print("Field Cannot be empty")
            continue
        if not phone.isdigit():
            print("Only Digits Allowed")
            continue

        if len(phone)!=11:
            print("Only 11 digits allowed")
            continue
        
        break

    while True:
      
        password = input("Enter your password: ").strip()
        if not password:
            print("Field cannot be empty")
            continue
        if len(password)<8:
            print("Password should have more than 8 characters")
            continue
        break               

    return phone , password

def admin_check():
    while True:
        admin = input("Enter Admin ID: ").strip()
        if not admin:
            print("Cannot be empty!")
            continue

        ad_pass = input("Enter Password: ").strip()
        if not ad_pass:
            print("Cannot be empty!")
            continue
        break

    if admin != admin_id or ad_pass != admin_pass:
        return {"status" : False , "message":"Wrong Id/pass"}
    else:
        return{"status" : True , "message":"Welcome! Logged in as Admin"}



def main():
    print("--- User Authentication ---")
    while True:
        
        print("1. For Login")
        print("2. For Register")
        print("3. For Admin")
        print("4. For exit")

        
        choice = input("\nEnter your choice: ")
        if not choice:
            print("Choice cannot be empty: ")
            continue
        if not choice.isdigit():
            print("Only digits Allowed!")
            continue
        

        if choice == "1":
            phone , password = handle_login()
            result = login_user(phone , password)

            print(result["message"])

            if result["status"]:
                print("Welcome ", result["user"] ["name"] )
         
            

        if choice == "2":
            name, phone, password = handle_reg()
            res = register_user(name, phone, password)

            print(res["message"])
            
            if res["status"]:
                print("Registered: " , res["user"]["name"] , res ["user"]["phone"])    
            
   

        if choice == "3":
           result = admin_check()
           print(result["message"])
            

        if choice == "4":
            exit()
            break


if __name__ == "__main__":
    main()

#python -m modules.auth    
>>>>>>> d9bf6c013eb25f9492ab7f388ea2cfd98c2796dd
