from modules.auth import register_form, login_user

def main():

    while True:
        print("\n--- Online Food App Auth ---")
        print("1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Enter choice: ")

        if choice == "1":
            name = input("Enter name: ")
            phone = input("Enter phone: ")
            password = input("Enter password: ")

            msg = register_form(name, phone, password)
            print(msg)

        elif choice == "2":
            phone = input("Enter phone: ")
            password = input("Enter password: ")

            user, msg = login_user(phone, password)

            if user:
                print(f"Welcome {user['name']}")
                print("User ID:", user["user_id"])
            else:
                print(msg)

        elif choice == "3":
            print("Exiting...")
            break

        else:
            print("Invalid choice")


main()

