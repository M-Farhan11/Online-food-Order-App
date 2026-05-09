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
        self.cart        = cart
        self.user        = user
        self.on_success  = on_success
        self.total       = sum(item.price * qty for item, qty in cart)
        self._animating  = False

        self.win = tk.Toplevel(parent)
        self.win.title("Checkout")
        self.win.geometry("480x640")
        self.win.resizable(False, False)
        self.win.configure(bg=COLORS["bg"])
        self.win.grab_set()
        self._center(480, 640, parent)
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

        # ── Bill summary ──────────────────────────────────
        bill_frame = tk.Frame(self.win, bg=COLORS["bg_card"],
                              padx=20, pady=16)
        bill_frame.pack(fill="both", expand=True, padx=20, pady=(16, 0))

        tk.Label(bill_frame, text="ORDER SUMMARY",
                 font=FONTS["btn_sm"], bg=COLORS["bg_card"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 10))

        # Scrollable items
        canvas = tk.Canvas(bill_frame, bg=COLORS["bg_card"],
                           highlightthickness=0, height=160)
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
            tk.Label(row, text=item.name,
                     font=FONTS["body"], bg=COLORS["bg_card"],
                     fg=COLORS["off_white"], anchor="w").pack(side="left")
            tk.Label(row, text=f"  x{qty}",
                     font=FONTS["body_sm"], bg=COLORS["bg_card"],
                     fg=COLORS["muted"]).pack(side="left")
            tk.Label(row, text=f"Rs.{item.price * qty:.0f}",
                     font=FONTS["body"], bg=COLORS["bg_card"],
                     fg=COLORS["white"]).pack(side="right")

        tk.Frame(bill_frame, bg=COLORS["border"], height=1).pack(
            fill="x", pady=10)

        total_row = tk.Frame(bill_frame, bg=COLORS["bg_card"])
        total_row.pack(fill="x")
        tk.Label(total_row, text="TOTAL",
                 font=FONTS["btn"], bg=COLORS["bg_card"],
                 fg=COLORS["white"]).pack(side="left")
        tk.Label(total_row, text=f"Rs. {self.total:.0f}",
                 font=("Georgia", 16, "bold"),
                 bg=COLORS["bg_card"], fg=COLORS["red"]).pack(side="right")

        # ── Payment method ────────────────────────────────
        method_frame = tk.Frame(self.win, bg=COLORS["bg"], padx=20, pady=10)
        method_frame.pack(fill="x")

        tk.Label(method_frame, text="PAYMENT METHOD",
                 font=FONTS["btn_sm"], bg=COLORS["bg"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 8))

        self.method_var = tk.StringVar(value="Cash on Delivery")

        for method, icon in [("Cash on Delivery", "💵"),
                              ("Online Payment",   "💳")]:
            rb_frame = tk.Frame(method_frame, bg=COLORS["bg_card"],
                                padx=12, pady=10)
            rb_frame.pack(fill="x", pady=3)
            tk.Radiobutton(
                rb_frame,
                text=f"  {icon}  {method}",
                variable=self.method_var, value=method,
                font=FONTS["body"],
                bg=COLORS["bg_card"], fg=COLORS["white"],
                selectcolor=COLORS["bg_card"],
                activebackground=COLORS["bg_card"],
                activeforeground=COLORS["white"],
                cursor="hand2",
                command=self._toggle_online_fields
            ).pack(anchor="w")

        # ── Online payment fields (hidden by default) ─────
        # This frame is always created here and toggled via pack/pack_forget
        self.online_frame = tk.Frame(self.win, bg=COLORS["bg"], padx=20)

        tk.Label(self.online_frame,
                 text="Online Payment Details",
                 font=FONTS["body_sm"], bg=COLORS["bg"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 4))

        # JazzCash / Easypaisa number
        box1 = tk.Frame(self.online_frame, bg=COLORS["bg_input"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        box1.pack(fill="x", pady=(0, 6))
        self.phone_entry = tk.Entry(
            box1, bg=COLORS["bg_input"], fg=COLORS["muted"],
            insertbackground=COLORS["white"],
            font=FONTS["input"], bd=0, highlightthickness=0)
        self.phone_entry.insert(0, "JazzCash / Easypaisa number")
        self.phone_entry.pack(fill="x", padx=12, pady=10)
        self._placeholder_bind(
            self.phone_entry, "JazzCash / Easypaisa number")

        # Transaction reference
        '''box2 = tk.Frame(self.online_frame, bg=COLORS["bg_input"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        box2.pack(fill="x")
        self.ref_entry = tk.Entry(
            box2, bg=COLORS["bg_input"], fg=COLORS["muted"],
            insertbackground=COLORS["white"],
            font=FONTS["input"], bd=0, highlightthickness=0)
        self.ref_entry.insert(0, "Transaction reference number")
        self.ref_entry.pack(fill="x", padx=12, pady=10)
        self._placeholder_bind(
            self.ref_entry, "Transaction reference number")

        # ── Loader label (hidden until processing) ────────
        self.loader_label = tk.Label(
            self.win, text="",
            font=FONTS["body_sm"], bg=COLORS["bg"],
            fg=COLORS["muted"])'''

        # ── Action buttons ────────────────────────────────
        btn_frame = tk.Frame(self.win, bg=COLORS["bg"], padx=20, pady=12)
        btn_frame.pack(fill="x", side="bottom")

        self.place_btn = tk.Button(
            btn_frame, text="PLACE ORDER",
            command=self._place_order,
            bg=COLORS["red"], fg=COLORS["white"],
            font=FONTS["btn"], bd=0, cursor="hand2",
            activebackground=COLORS["red_hover"],
            activeforeground=COLORS["white"],
            pady=13)
        self.place_btn.pack(fill="x")

        tk.Button(btn_frame, text="Cancel",
                  command=self.win.destroy,
                  bg=COLORS["bg"], fg=COLORS["muted"],
                  font=FONTS["body_sm"], bd=0,
                  cursor="hand2").pack(pady=(6, 0))

    # ── helpers ───────────────────────────────────────────

    def _placeholder_bind(self, entry, placeholder):
        """Attach focus-in/out placeholder behaviour."""
        def fi(e):
            if entry.get() == placeholder:
                entry.delete(0, "end")
                entry.config(fg=COLORS["white"])
        def fo(e):
            if not entry.get().strip():
                entry.insert(0, placeholder)
                entry.config(fg=COLORS["muted"])
        entry.bind("<FocusIn>",  fi)
        entry.bind("<FocusOut>", fo)

    def _get_field(self, entry, placeholder):
        val = entry.get().strip()
        return "" if val == placeholder else val

    def _toggle_online_fields(self):
        """Show / hide online payment fields based on selected method."""
        if self.method_var.get() == "Online Payment":
            # Insert before the loader label and buttons (near bottom)
            self.online_frame.pack(fill="x", pady=(0, 4))
        else:
            self.online_frame.pack_forget()

    # ── order placement ───────────────────────────────────

    def _place_order(self):
        method = self.method_var.get()

        if method == "Online Payment":
            phone = self._get_field(
                self.phone_entry, "JazzCash / Easypaisa number")
            '''ref   = self._get_field(
                self.ref_entry, "Transaction reference number")'''

            if not phone:
                messagebox.showwarning(
                    "Missing Details",
                    "Please enter your JazzCash / Easypaisa number.",
                    parent=self.win)
                return
            '''if not ref:
                messagebox.showwarning(
                    "Missing Details",
                    "Please enter the transaction reference number.",
                    parent=self.win)
                return'''

            payment_details = f"{phone}"
        else:
            payment_details = None

        confirm = messagebox.askyesno(
            "Confirm Order",
            f"Place order?\n\nTotal: Rs. {self.total:.0f}\nMethod: {method}",
            parent=self.win)
        if not confirm:
            return

        if method == "Online Payment":
            # Disable inputs, show animated loader, finalize after 3 s
            self.place_btn.config(state="disabled", text="Processing...")
            self.phone_entry.config(state="disabled")
            #self.ref_entry.config(state="disabled")
            #self.loader_label.config(text="Processing payment ⏳")
           # self.loader_label.pack(padx=20, pady=(0, 4))
            self._animating = True
            self._animate_loader(0)
            self.win.after(
                3000,
                lambda: self._finalize_order(method, payment_details))
        else:
            self._finalize_order(method, payment_details)

    def _animate_loader(self, tick):
        if not self._animating:
            return
        dots = "." * (tick % 4)
        #self.loader_label.config(
            #text=f"Processing payment{dots} ⏳")
        self.win.after(400, lambda: self._animate_loader(tick + 1))

    def _finalize_order(self, method, payment_details):
        self._animating = False

        # insert_order sets status to "Payment Pending" for online orders
        # and "Placed" for cash — handled inside the module
        order = insert_order(self.user.user_id, self.total, method)
        insert_order_items(order.order_id, self.cart)
        insert_payment(order.order_id, method, self.total, payment_details)
        clear_cart()

        if method == "Online Payment":
            msg = (f"✔ Payment received!\n\n"
                   f"Order #{order.order_id} is pending admin confirmation.\n"
                   f"You will see it as 'Payment Pending' until the admin\n"
                   f"confirms your payment details and starts preparing.")
        else:
            msg = (f"✔ Order #{order.order_id} placed!\n\n"
                   f"Pay Rs. {self.total:.0f} on delivery.")

        messagebox.showinfo("Order Confirmed", msg, parent=self.win)
        self.win.destroy()
        self.on_success(order.order_id)