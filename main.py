# main.py  — GUI entry point
from gui.login_window import LoginWindow
from gui.menu_window  import MenuWindow
from gui.admin_window import AdminWindow


def launch_customer(user):
    MenuWindow(user=user, on_logout=launch_login)


def launch_admin():
    AdminWindow(on_logout=launch_login)


def launch_login():
    LoginWindow(
        on_login_success=launch_customer,
        on_admin_success=launch_admin
    )


if __name__ == "__main__":
    launch_login()