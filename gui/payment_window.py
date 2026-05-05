# gui/payment_window.py
import tkinter as tk
from tkinter import messagebox
from gui.theme import COLORS, FONTS
from modules.payment import insert_order, insert_order_items, insert_payment
from modules.menu import clear_cart


class PaymentWindow:
    def __init__(self, parent, cart, user, on_success):
        """
        parent     — parent tkinter window
        cart       — [(MenuItem, qty), ...]
        user       — User object
        on_success — callback(order_id) called after successful order
        """
        self.cart       = cart
        self.user       = user
        self.on_success = on_success
        self.total      = sum(item.price * qty for item, qty in cart)

        self.win = tk.Toplevel(parent)
        self.win.title("Checkout")
        self.win.geometry("480x620")
        self.win.resizable(False, False)
        self.win.configure(bg=COLORS["bg"])
        self.win.grab_set()   # modal
        self._center(480, 620, parent)
        self._build_ui()

    def _center(self, w, h, parent):
        self.win.update_idletasks()
        px = parent.winfo_x()
        py = parent.winfo_y()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        self.win.geometry(f"{w}x{h}+{px+(pw-w)//2}+{py+(ph-h)//2}")

    # ── UI ────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.win, bg=COLORS["red"], pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="CHECKOUT", font=FONTS["heading"],
                 bg=COLORS["red"], fg=COLORS["white"]).pack()

        # Scrollable bill
        bill_frame = tk.Frame(self.win, bg=COLORS["bg_card"],
                              padx=20, pady=16)
        bill_frame.pack(fill="both", expand=True, padx=20, pady=(16, 0))

        tk.Label(bill_frame, text="ORDER SUMMARY",
                 font=FONTS["btn_sm"], bg=COLORS["bg_card"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 10))

        # Items list
        canvas = tk.Canvas(bill_frame, bg=COLORS["bg_card"],
                           highlightthickness=0, height=200)
        scrollbar = tk.Scrollbar(bill_frame, orient="vertical",
                                 command=canvas.yview)
        items_frame = tk.Frame(canvas, bg=COLORS["bg_card"])

        items_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=items_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for item, qty in self.cart:
            row = tk.Frame(items_frame, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"{item.name}",
                     font=FONTS["body"], bg=COLORS["bg_card"],
                     fg=COLORS["off_white"], anchor="w").pack(side="left")
            tk.Label(row, text=f"x{qty}",
                     font=FONTS["body_sm"], bg=COLORS["bg_card"],
                     fg=COLORS["muted"]).pack(side="left", padx=8)
            tk.Label(row, text=f"Rs.{item.price * qty:.0f}",
                     font=FONTS["body"], bg=COLORS["bg_card"],
                     fg=COLORS["white"]).pack(side="right")

        # Divider
        tk.Frame(bill_frame, bg=COLORS["border"], height=1).pack(
            fill="x", pady=10)

        # Total
        total_row = tk.Frame(bill_frame, bg=COLORS["bg_card"])
        total_row.pack(fill="x")
        tk.Label(total_row, text="TOTAL",
                 font=FONTS["btn"], bg=COLORS["bg_card"],
                 fg=COLORS["white"]).pack(side="left")
        tk.Label(total_row, text=f"Rs. {self.total:.0f}",
                 font=("Georgia", 16, "bold"), bg=COLORS["bg_card"],
                 fg=COLORS["red"]).pack(side="right")

        # Payment method section
        method_frame = tk.Frame(self.win, bg=COLORS["bg"], padx=20, pady=12)
        method_frame.pack(fill="x")

        tk.Label(method_frame, text="PAYMENT METHOD",
                 font=FONTS["btn_sm"], bg=COLORS["bg"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 8))

        self.method_var = tk.StringVar(value="Cash on Delivery")
        methods = [("Cash on Delivery", "💵"), ("Online Payment", "💳")]

        for method, icon in methods:
            rb_frame = tk.Frame(method_frame, bg=COLORS["bg_card"],
                                padx=12, pady=10)
            rb_frame.pack(fill="x", pady=3)
            tk.Radiobutton(rb_frame,
                           text=f"  {icon}  {method}",
                           variable=self.method_var, value=method,
                           font=FONTS["body"],
                           bg=COLORS["bg_card"], fg=COLORS["white"],
                           selectcolor=COLORS["bg_card"],
                           activebackground=COLORS["bg_card"],
                           activeforeground=COLORS["white"],
                           cursor="hand2",
                           command=self._toggle_ref_field).pack(anchor="w")

        # Transaction ref (online only)
        self.ref_frame = tk.Frame(self.win, bg=COLORS["bg"], padx=20)
        tk.Label(self.ref_frame, text="Online payment details",
                 font=FONTS["body_sm"], bg=COLORS["bg"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 4))
        self.ref_entry_frame = tk.Frame(self.ref_frame,
                                        bg=COLORS["bg_input"],
                                        highlightbackground=COLORS["border"],
                                        highlightthickness=1)
        self.ref_entry_frame.pack(fill="x")
        self.payment_entry = tk.Entry(self.ref_entry_frame,
                                      bg=COLORS["bg_input"],
                                      fg=COLORS["white"],
                                      insertbackground=COLORS["white"],
                                      font=FONTS["input"], bd=0,
                                      highlightthickness=0)
        self.payment_entry.insert(0, "Jazzcash / Easypaisa number")
        self.payment_entry.config(fg=COLORS["muted"])
        self.payment_entry.pack(fill="x", padx=12, pady=10)
        self.payment_entry.bind("<FocusIn>",  self._payment_focus_in)
        self.payment_entry.bind("<FocusOut>", self._payment_focus_out)
        self._toggle_ref_field()

        # Place order button
        btn_frame = tk.Frame(self.win, bg=COLORS["bg"], padx=20, pady=12)
        btn_frame.pack(fill="x")
        self.place_button = tk.Button(btn_frame, text="PLACE ORDER",
                                      command=self._place_order,
                                      bg=COLORS["red"], fg=COLORS["white"],
                                      font=FONTS["btn"], bd=0, cursor="hand2",
                                      activebackground=COLORS["red_hover"],
                                      activeforeground=COLORS["white"],
                                      pady=14)
        self.place_button.pack(fill="x")
        tk.Button(btn_frame, text="Cancel",
                  command=self.win.destroy,
                  bg=COLORS["bg"], fg=COLORS["muted"],
                  font=FONTS["body_sm"], bd=0, cursor="hand2").pack(pady=(6, 0))

    def _toggle_ref_field(self):
        if self.method_var.get() == "Online Payment":
            self.ref_frame.pack(fill="x", padx=20, pady=(0, 8))
        else:
            self.ref_frame.pack_forget()

    def _payment_focus_in(self, e):
        if self.payment_entry.get() == "Jazzcash / Easypaisa number":
            self.payment_entry.delete(0, "end")
            self.payment_entry.config(fg=COLORS["white"])

    def _payment_focus_out(self, e):
        if not self.payment_entry.get():
            self.payment_entry.insert(0, "Jazzcash / Easypaisa number")
            self.payment_entry.config(fg=COLORS["muted"])

    def _place_order(self):
        method = self.method_var.get()
        payment_details = None

        if method == "Online Payment":
            details = self.payment_entry.get().strip()
            if not details or details == "Jazzcash / Easypaisa number":
                messagebox.showwarning("Missing payment details",
                    "Please enter your Jazzcash or Easypaisa number.",
                    parent=self.win)
                return
            payment_details = details

        confirm = messagebox.askyesno(
            "Confirm Order",
            f"Place order?\n\nTotal: Rs. {self.total:.0f}\nMethod: {method}",
            parent=self.win)
        if not confirm:
            return

        if method == "Online Payment":
            self.place_button.config(state="disabled")
            self.payment_entry.config(state="disabled")
            self._show_loader()
            self.win.after(5000,
                           lambda: self._finalize_order(method,
                                                        payment_details))
        else:
            self._finalize_order(method, payment_details)

    def _show_loader(self):
        self.loading_dots = 0
        if not hasattr(self, "loader_label") or self.loader_label is None:
            self.loader_label = tk.Label(self.win,
                                         text="Processing payment... ⏳",
                                         font=FONTS["body_sm"],
                                         bg=COLORS["bg"],
                                         fg=COLORS["muted"])
            self.loader_label.pack(fill="x", padx=20, pady=(0, 8))
        self._animate_loader()

    def _animate_loader(self):
        self.loading_dots = (self.loading_dots + 1) % 4
        dots = "." * self.loading_dots
        self.loader_label.config(text=f"Processing payment{dots} ⏳")
        if self.place_button.cget("state") == "disabled":
            self.win.after(500, self._animate_loader)

    def _finalize_order(self, method, payment_details):
        order = insert_order(self.user.user_id, self.total, method)
        insert_order_items(order.order_id, self.cart)
        insert_payment(order.order_id, method, self.total, payment_details)
        clear_cart()

        messagebox.showinfo("Order Confirmed",
            f"✔ Order #{order.order_id} confirmed!",
            parent=self.win)
        self.win.destroy()
        self.on_success(order.order_id)