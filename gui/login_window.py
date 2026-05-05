# gui/login_window.py
import tkinter as tk
from tkinter import messagebox
from gui.theme import COLORS, FONTS, PADDING
from modules.auth import login_user, register_user


class LoginWindow:
    def __init__(self, on_login_success, on_admin_success):
        """
        on_login_success(user)  — called with User object after customer login
        on_admin_success()      — called after admin login
        """
        self.on_login_success  = on_login_success
        self.on_admin_success  = on_admin_success
        self.active_tab        = "login"

        self.root = tk.Tk()
        self.root.title("QuickBite")
        self.root.geometry("460x580")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["bg"])
        self._center_window(self.root, 460, 580)

        self._build_ui()
        self.root.mainloop()

    # ── helpers ──────────────────────────────────────────

    def _center_window(self, win, w, h):
        win.update_idletasks()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _entry(self, parent, placeholder, show=None):
        frame = tk.Frame(parent, bg=COLORS["bg_input"],
                         highlightbackground=COLORS["border"],
                         highlightthickness=1)
        frame.pack(fill="x", pady=6)

        e = tk.Entry(frame, bg=COLORS["bg_input"], fg=COLORS["muted"],
                     insertbackground=COLORS["white"],
                     font=FONTS["input"], bd=0,
                     highlightthickness=0, show=show or "")
        e.insert(0, placeholder)
        e.pack(fill="x", padx=12, pady=10)

        def on_focus_in(event):
            if e.get() == placeholder:
                e.delete(0, "end")
                e.config(fg=COLORS["white"])
                if show:
                    e.config(show=show)

        def on_focus_out(event):
            if not e.get():
                e.insert(0, placeholder)
                e.config(fg=COLORS["muted"], show="")

        e.bind("<FocusIn>",  on_focus_in)
        e.bind("<FocusOut>", on_focus_out)

        # focus highlight
        frame.bind("<Enter>", lambda e: frame.config(
            highlightbackground=COLORS["red"]))
        frame.bind("<Leave>", lambda e: frame.config(
            highlightbackground=COLORS["border"]))

        return e, placeholder

    def _red_btn(self, parent, text, cmd, full=True):
        btn = tk.Button(parent, text=text, command=cmd,
                        bg=COLORS["red"], fg=COLORS["white"],
                        font=FONTS["btn"], bd=0, cursor="hand2",
                        activebackground=COLORS["red_hover"],
                        activeforeground=COLORS["white"],
                        pady=12)
        if full:
            btn.pack(fill="x", pady=(10, 4))
        return btn

    def _get_val(self, entry_tuple):
        val, placeholder = entry_tuple
        raw = val.get().strip()
        return "" if raw == placeholder else raw

    # ── build UI ──────────────────────────────────────────

    def _build_ui(self):
        # Logo bar
        logo_bar = tk.Frame(self.root, bg=COLORS["red"], height=6)
        logo_bar.pack(fill="x")

        logo_frame = tk.Frame(self.root, bg=COLORS["bg"], pady=28)
        logo_frame.pack(fill="x")

        tk.Label(logo_frame, text="🍗 QuickBite",
                 font=FONTS["logo"], bg=COLORS["bg"],
                 fg=COLORS["white"]).pack()
        tk.Label(logo_frame, text="ONLINE FOOD ORDER SYSTEM",
                 font=("Helvetica", 8, "bold"), bg=COLORS["bg"],
                 fg=COLORS["red"]).pack(pady=(2, 0))

        # Tab switcher
        tab_frame = tk.Frame(self.root, bg=COLORS["bg_card"])
        tab_frame.pack(fill="x", padx=40, pady=(0, 20))

        self.tab_login_btn = tk.Button(
            tab_frame, text="LOGIN", font=FONTS["btn_sm"],
            bd=0, cursor="hand2", pady=10,
            command=lambda: self._switch_tab("login"))
        self.tab_reg_btn = tk.Button(
            tab_frame, text="REGISTER", font=FONTS["btn_sm"],
            bd=0, cursor="hand2", pady=10,
            command=lambda: self._switch_tab("register"))
        self.tab_admin_btn = tk.Button(
            tab_frame, text="ADMIN", font=FONTS["btn_sm"],
            bd=0, cursor="hand2", pady=10,
            command=lambda: self._switch_tab("admin"))

        for btn in [self.tab_login_btn, self.tab_reg_btn, self.tab_admin_btn]:
            btn.pack(side="left", expand=True, fill="x")

        # Card container
        self.card = tk.Frame(self.root, bg=COLORS["bg_card"],
                             padx=32, pady=24)
        self.card.pack(fill="both", expand=True, padx=40, pady=(0, 40))

        self._build_login_form()
        self._switch_tab("login")

    def _switch_tab(self, tab):
        self.active_tab = tab
        # update tab colours
        for btn, name in [(self.tab_login_btn, "login"),
                          (self.tab_reg_btn,   "register"),
                          (self.tab_admin_btn, "admin")]:
            if name == tab:
                btn.config(bg=COLORS["red"],    fg=COLORS["white"])
            else:
                btn.config(bg=COLORS["bg_card"], fg=COLORS["muted"])

        for w in self.card.winfo_children():
            w.destroy()

        if   tab == "login":    self._build_login_form()
        elif tab == "register": self._build_register_form()
        elif tab == "admin":    self._build_admin_form()

    # ── login form ───────────────────────────────────────

    def _build_login_form(self):
        tk.Label(self.card, text="Welcome back",
                 font=FONTS["heading"], bg=COLORS["bg_card"],
                 fg=COLORS["white"]).pack(anchor="w", pady=(0, 4))
        tk.Label(self.card, text="Sign in to your account",
                 font=FONTS["body_sm"], bg=COLORS["bg_card"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 16))

        self.l_phone    = self._entry(self.card, "Phone number (11 digits)")
        self.l_password = self._entry(self.card, "Password", show="•")

        self._red_btn(self.card, "SIGN IN", self._do_login)

        tk.Label(self.card, text="Don't have an account? Register →",
                 font=FONTS["body_sm"], bg=COLORS["bg_card"],
                 fg=COLORS["muted"], cursor="hand2").pack(pady=(8, 0))

    def _do_login(self):
        phone    = self._get_val(self.l_phone)
        password = self._get_val(self.l_password)

        if not phone or not password:
            messagebox.showwarning("Missing fields", "Please fill in all fields.",
                                   parent=self.root); return
        if not phone.isdigit() or len(phone) != 11:
            messagebox.showwarning("Invalid phone",
                                   "Phone must be exactly 11 digits.",
                                   parent=self.root); return

        result = login_user(phone, password)
        if result["status"]:
            self.root.destroy()
            self.on_login_success(result["user"])
        else:
            messagebox.showerror("Login failed", result["message"],
                                 parent=self.root)

    # ── register form ─────────────────────────────────────

    def _build_register_form(self):
        tk.Label(self.card, text="Create account",
                 font=FONTS["heading"], bg=COLORS["bg_card"],
                 fg=COLORS["white"]).pack(anchor="w", pady=(0, 4))
        tk.Label(self.card, text="Join QuickBite today",
                 font=FONTS["body_sm"], bg=COLORS["bg_card"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 12))

        self.r_name     = self._entry(self.card, "Full name")
        self.r_phone    = self._entry(self.card, "Phone number (11 digits)")
        self.r_password = self._entry(self.card, "Password (min 8 chars)", show="•")

        self._red_btn(self.card, "CREATE ACCOUNT", self._do_register)

    def _do_register(self):
        name     = self._get_val(self.r_name)
        phone    = self._get_val(self.r_phone)
        password = self._get_val(self.r_password)

        if not all([name, phone, password]):
            messagebox.showwarning("Missing fields", "Please fill in all fields.",
                                   parent=self.root); return
        if not all(p.isalpha() for p in name.split()):
            messagebox.showwarning("Invalid name", "Name must contain letters only.",
                                   parent=self.root); return
        if not phone.isdigit() or len(phone) != 11:
            messagebox.showwarning("Invalid phone", "Phone must be 11 digits.",
                                   parent=self.root); return
        if len(password) < 8:
            messagebox.showwarning("Weak password",
                                   "Password must be at least 8 characters.",
                                   parent=self.root); return

        result = register_user(name, phone, password)
        if result["status"]:
            messagebox.showinfo("Success", "Account created! You can now log in.",
                                parent=self.root)
            self._switch_tab("login")
        else:
            messagebox.showerror("Registration failed", result["message"],
                                 parent=self.root)

    # ── admin form ────────────────────────────────────────

    def _build_admin_form(self):
        tk.Label(self.card, text="Admin Access",
                 font=FONTS["heading"], bg=COLORS["bg_card"],
                 fg=COLORS["white"]).pack(anchor="w", pady=(0, 4))
        tk.Label(self.card, text="Restricted area",
                 font=FONTS["body_sm"], bg=COLORS["bg_card"],
                 fg=COLORS["red"]).pack(anchor="w", pady=(0, 16))

        self.a_id   = self._entry(self.card, "Admin ID")
        self.a_pass = self._entry(self.card, "Admin Password", show="•")

        self._red_btn(self.card, "ADMIN LOGIN", self._do_admin_login)

    def _do_admin_login(self):
        from modules.auth import admin_login
        admin_id   = self._get_val(self.a_id)
        admin_pass = self._get_val(self.a_pass)

        if not admin_id or not admin_pass:
            messagebox.showwarning("Missing fields", "Fill in all fields.",
                                   parent=self.root); return

        result = admin_login(admin_id, admin_pass)
        if result["status"]:
            self.root.destroy()
            self.on_admin_success()
        else:
            messagebox.showerror("Access denied", result["message"],
                                 parent=self.root)