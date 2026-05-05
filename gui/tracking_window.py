# gui/tracking_window.py
import tkinter as tk
from tkinter import messagebox
from gui.theme import COLORS, FONTS, STATUS_COLORS
from modules.tracking import _get_order, _get_status
from modules.payment import get_orders_by_user


class TrackingWindow:
    def __init__(self, parent, user):
        self.user   = user
        self.parent = parent

        self.win = tk.Toplevel(parent)
        self.win.title("My Orders")
        self.win.geometry("560x620")
        self.win.resizable(False, False)
        self.win.configure(bg=COLORS["bg"])
        self.win.grab_set()
        self._center(560, 620)
        self._build_ui()
        self._load_orders()

    def _center(self, w, h):
        self.win.update_idletasks()
        px = self.parent.winfo_x()
        py = self.parent.winfo_y()
        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        self.win.geometry(f"{w}x{h}+{px+(pw-w)//2}+{py+(ph-h)//2}")

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.win, bg=COLORS["red"], pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📦  MY ORDERS",
                 font=FONTS["heading"], bg=COLORS["red"],
                 fg=COLORS["white"]).pack()

        # Quick track bar
        track_frame = tk.Frame(self.win, bg=COLORS["bg_card"],
                               padx=20, pady=12)
        track_frame.pack(fill="x")

        tk.Label(track_frame, text="Track by Order ID:",
                 font=FONTS["body_sm"], bg=COLORS["bg_card"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 6))

        input_row = tk.Frame(track_frame, bg=COLORS["bg_card"])
        input_row.pack(fill="x")

        entry_box = tk.Frame(input_row, bg=COLORS["bg_input"],
                             highlightbackground=COLORS["border"],
                             highlightthickness=1)
        entry_box.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.track_entry = tk.Entry(entry_box,
                                    bg=COLORS["bg_input"],
                                    fg=COLORS["white"],
                                    insertbackground=COLORS["white"],
                                    font=FONTS["input"], bd=0,
                                    highlightthickness=0)
        self.track_entry.pack(fill="x", padx=10, pady=8)
        self.track_entry.bind("<Return>", lambda e: self._quick_track())

        tk.Button(input_row, text="TRACK",
                  command=self._quick_track,
                  bg=COLORS["red"], fg=COLORS["white"],
                  font=FONTS["btn_sm"], bd=0, cursor="hand2",
                  padx=18, pady=8,
                  activebackground=COLORS["red_hover"],
                  activeforeground=COLORS["white"]).pack(side="right")

        # Status result
        self.status_result = tk.Label(track_frame, text="",
                                      font=FONTS["body"],
                                      bg=COLORS["bg_card"],
                                      fg=COLORS["white"])
        self.status_result.pack(anchor="w", pady=(8, 0))

        # Divider
        tk.Frame(self.win, bg=COLORS["border"], height=1).pack(fill="x",
                                                                pady=(12, 0))

        # Order history heading
        hist_hdr = tk.Frame(self.win, bg=COLORS["bg"], padx=20, pady=10)
        hist_hdr.pack(fill="x")
        tk.Label(hist_hdr, text="ORDER HISTORY",
                 font=FONTS["btn_sm"], bg=COLORS["bg"],
                 fg=COLORS["muted"]).pack(side="left")
        tk.Button(hist_hdr, text="↻ Refresh",
                  command=self._load_orders,
                  bg=COLORS["bg"], fg=COLORS["muted"],
                  font=FONTS["body_sm"], bd=0, cursor="hand2").pack(side="right")

        # Scrollable orders list
        container = tk.Frame(self.win, bg=COLORS["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        canvas = tk.Canvas(container, bg=COLORS["bg"],
                           highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                 command=canvas.yview)
        self.orders_frame = tk.Frame(canvas, bg=COLORS["bg"])

        self.orders_frame.bind("<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.orders_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        canvas.bind("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

    def _quick_track(self):
        raw = self.track_entry.get().strip()
        if not raw.isdigit():
            self.status_result.config(text="⚠  Enter a valid numeric Order ID.",
                                      fg=COLORS["warning"]); return

        order_id = int(raw)
        order    = _get_order(order_id)

        if not order:
            self.status_result.config(text=f"✗  Order #{order_id} not found.",
                                      fg="#E74C3C"); return
        if order["user_id"] != self.user.user_id:
            self.status_result.config(text="✗  This order is not yours.",
                                      fg="#E74C3C"); return

        status = order["status"]
        color  = STATUS_COLORS.get(status, COLORS["white"])
        self.status_result.config(
            text=f"Order #{order_id}  →  {status}",
            fg=color)

    def _load_orders(self):
        for w in self.orders_frame.winfo_children():
            w.destroy()

        orders = get_orders_by_user(self.user.user_id)

        if not orders:
            tk.Label(self.orders_frame,
                     text="No orders yet. Place your first order!",
                     font=FONTS["body"], bg=COLORS["bg"],
                     fg=COLORS["muted"]).pack(pady=30)
            return

        for order in orders:
            self._render_order_card(order)

    def _render_order_card(self, order):
        card = tk.Frame(self.orders_frame, bg=COLORS["bg_card"],
                        padx=14, pady=12)
        card.pack(fill="x", pady=(0, 8))

        # Top row: order id + status badge
        top = tk.Frame(card, bg=COLORS["bg_card"])
        top.pack(fill="x")

        tk.Label(top, text=f"Order #{order.order_id}",
                 font=FONTS["subhead"], bg=COLORS["bg_card"],
                 fg=COLORS["white"]).pack(side="left")

        status_color = STATUS_COLORS.get(order.status, COLORS["muted"])
        tk.Label(top, text=f"  {order.status}  ",
                 font=FONTS["body_sm"], bg=status_color,
                 fg=COLORS["white"]).pack(side="right")

        # Date + payment
        tk.Label(card, text=f"{order.created_at}  ·  {order.payment_method}",
                 font=FONTS["body_sm"], bg=COLORS["bg_card"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(4, 8))

        # Items
        for oi in order.items:
            item_row = tk.Frame(card, bg=COLORS["bg_card"])
            item_row.pack(fill="x", pady=1)
            tk.Label(item_row, text=f"• {oi.name}",
                     font=FONTS["body_sm"], bg=COLORS["bg_card"],
                     fg=COLORS["off_white"]).pack(side="left")
            tk.Label(item_row, text=f"x{oi.quantity}",
                     font=FONTS["body_sm"], bg=COLORS["bg_card"],
                     fg=COLORS["muted"]).pack(side="left", padx=6)
            tk.Label(item_row,
                     text=f"Rs.{oi.price * oi.quantity:.0f}",
                     font=FONTS["body_sm"], bg=COLORS["bg_card"],
                     fg=COLORS["white"]).pack(side="right")

        # Divider + total
        tk.Frame(card, bg=COLORS["border"], height=1).pack(
            fill="x", pady=(8, 6))
        total_row = tk.Frame(card, bg=COLORS["bg_card"])
        total_row.pack(fill="x")
        tk.Label(total_row, text="Total",
                 font=FONTS["body_sm"], bg=COLORS["bg_card"],
                 fg=COLORS["muted"]).pack(side="left")
        tk.Label(total_row, text=f"Rs. {order.total_amount:.0f}",
                 font=FONTS["price"], bg=COLORS["bg_card"],
                 fg=COLORS["red"]).pack(side="right")

        # Progress bar
        self._render_status_bar(card, order.status)

    def _render_status_bar(self, parent, current_status):
        stages = ["Placed", "Preparing", "Out for Delivery", "Delivered"]
        try:
            current_idx = stages.index(current_status)
        except ValueError:
            current_idx = 0

        bar_frame = tk.Frame(parent, bg=COLORS["bg_card"])
        bar_frame.pack(fill="x", pady=(8, 0))

        for i, stage in enumerate(stages):
            col = tk.Frame(bar_frame, bg=COLORS["bg_card"])
            col.pack(side="left", expand=True)

            dot_color = (COLORS["red"] if i <= current_idx
                         else COLORS["border"])
            dot = tk.Frame(col, bg=dot_color, width=10, height=10)
            dot.pack()

            tk.Label(col, text=stage,
                     font=("Helvetica", 7),
                     bg=COLORS["bg_card"],
                     fg=COLORS["white"] if i <= current_idx
                     else COLORS["muted"]).pack()

            if i < len(stages) - 1:
                line_color = (COLORS["red"] if i < current_idx
                              else COLORS["border"])
                tk.Frame(bar_frame, bg=line_color,
                         height=2, width=20).pack(side="left",
                                                   pady=5)