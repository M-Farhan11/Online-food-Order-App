# gui/menu_window.py
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
from gui.theme import COLORS, FONTS
from gui.payment_window import PaymentWindow
from modules.menu import (
    load_menu_from_db, menu, categories,
    add_to_cart, remove_from_cart, undo_last_action,
    get_cart_total, cart, undo_stack, search_item
)

IMG_DIR      = "images"
IMG_W, IMG_H = 160, 120   # card image size
PLACEHOLDER  = None        # set after root created


def _load_image(path, w=IMG_W, h=IMG_H):
    """Load + resize image; return PhotoImage or placeholder."""
    try:
        if path and os.path.exists(path):
            img = Image.open(path).resize((w, h), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
    except Exception:
        pass
    return PLACEHOLDER


class MenuWindow:
    def __init__(self, user, on_logout):
        self.user      = user
        self.on_logout = on_logout
        self.cart_items = {}        # item_id → qty (mirrors modules.menu.cart)
        self._photo_refs = []       # keep PhotoImage refs alive

        self.root = tk.Tk()
        self.root.title(f"QuickBite — {user.name}")
        self.root.geometry("1100x700")
        self.root.configure(bg=COLORS["bg"])
        self.root.minsize(900, 600)
        self._center(1100, 700)

        self._make_placeholder()
        load_menu_from_db()
        self._build_ui()
        self.root.mainloop()

    def _center(self, w, h):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _make_placeholder(self):
        global PLACEHOLDER
        img = Image.new("RGB", (IMG_W, IMG_H), color="#2A2A2A")
        PLACEHOLDER = ImageTk.PhotoImage(img)

    # ── layout ────────────────────────────────────────────

    def _build_ui(self):
        # Top navbar
        self._build_navbar()

        # Main body: left menu area + right cart sidebar
        body = tk.Frame(self.root, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)

        # Menu area
        menu_area = tk.Frame(body, bg=COLORS["bg"])
        menu_area.pack(side="left", fill="both", expand=True)

        self._build_search_bar(menu_area)
        self._build_category_tabs(menu_area)
        self._build_menu_grid(menu_area)

        # Cart sidebar
        self._build_cart_sidebar(body)

    # ── navbar ────────────────────────────────────────────

    def _build_navbar(self):
        nav = tk.Frame(self.root, bg=COLORS["red"], pady=0)
        nav.pack(fill="x")

        left = tk.Frame(nav, bg=COLORS["red"])
        left.pack(side="left", padx=20, pady=10)
        tk.Label(left, text="🍗 QuickBite", font=FONTS["logo"],
                 bg=COLORS["red"], fg=COLORS["white"]).pack(side="left")

        right = tk.Frame(nav, bg=COLORS["red"])
        right.pack(side="right", padx=20)

        self.track_btn = tk.Button(right, text="📦 My Orders",
                                   command=self._open_tracking,
                                   bg=COLORS["red_dark"], fg=COLORS["white"],
                                   font=FONTS["btn_sm"], bd=0,
                                   cursor="hand2", padx=14, pady=8,
                                   activebackground=COLORS["red"],
                                   activeforeground=COLORS["white"])
        self.track_btn.pack(side="left", padx=(0, 8))

        tk.Button(right, text=f"👤 {self.user.name}  |  Logout",
                  command=self._logout,
                  bg=COLORS["red_dark"], fg=COLORS["off_white"],
                  font=FONTS["btn_sm"], bd=0, cursor="hand2",
                  padx=14, pady=8,
                  activebackground=COLORS["red"],
                  activeforeground=COLORS["white"]).pack(side="left")

    # ── search ────────────────────────────────────────────

    def _build_search_bar(self, parent):
        frame = tk.Frame(parent, bg=COLORS["bg"], padx=20, pady=14)
        frame.pack(fill="x")

        search_box = tk.Frame(frame, bg=COLORS["bg_input"],
                              highlightbackground=COLORS["border"],
                              highlightthickness=1)
        search_box.pack(fill="x")

        tk.Label(search_box, text="🔍", font=("Helvetica", 12),
                 bg=COLORS["bg_input"], fg=COLORS["muted"]).pack(
                     side="left", padx=(12, 0))

        self.search_var = tk.StringVar()
        e = tk.Entry(search_box, textvariable=self.search_var,
                     bg=COLORS["bg_input"], fg=COLORS["white"],
                     insertbackground=COLORS["white"],
                     font=FONTS["input"], bd=0, highlightthickness=0)
        e.insert(0, "Search for food...")
        e.config(fg=COLORS["muted"])
        e.pack(fill="x", padx=8, pady=10)

        def sf_in(ev):
            if e.get() == "Search for food...":
                e.delete(0, "end"); e.config(fg=COLORS["white"])
        def sf_out(ev):
            if not e.get():
                e.insert(0, "Search for food..."); e.config(fg=COLORS["muted"])

        e.bind("<FocusIn>",  sf_in)
        e.bind("<FocusOut>", sf_out)
        self.search_entry = e

    def _on_search(self):
        query = self.search_var.get()
        if query == "Search for food...":
            query = ""
        self._render_grid(search_query=query.strip())

    # ── category tabs ─────────────────────────────────────

    def _build_category_tabs(self, parent):
        self.tab_frame = tk.Frame(parent, bg=COLORS["bg"], padx=20)
        self.tab_frame.pack(fill="x", pady=(0, 8))
        self.active_cat = "All"
        self._render_category_tabs()

    def _render_category_tabs(self):
        for w in self.tab_frame.winfo_children():
            w.destroy()

        cats = ["All"] + list(categories.keys())
        for cat in cats:
            active = cat == self.active_cat
            btn = tk.Button(self.tab_frame, text=cat,
                            bg=COLORS["red"] if active else COLORS["bg_card"],
                            fg=COLORS["white"],
                            font=FONTS["btn_sm"], bd=0, cursor="hand2",
                            padx=16, pady=7,
                            activebackground=COLORS["red_hover"],
                            activeforeground=COLORS["white"],
                            command=lambda c=cat: self._select_category(c))
            btn.pack(side="left", padx=(0, 6))

    def _select_category(self, cat):
        self.active_cat = cat
        self.search_var.set("")
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, "Search for food...")
        self.search_entry.config(fg=COLORS["muted"])
        self._render_category_tabs()
        self._render_grid()

    # ── menu grid ─────────────────────────────────────────

    def _build_menu_grid(self, parent):
        container = tk.Frame(parent, bg=COLORS["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        self.canvas = tk.Canvas(container, bg=COLORS["bg"],
                                highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                 command=self.canvas.yview)
        self.grid_frame = tk.Frame(self.canvas, bg=COLORS["bg"])

        self.grid_frame.bind("<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<MouseWheel>",
            lambda e: self.canvas.yview_scroll(-1*(e.delta//120), "units"))

        # Enable search tracing after grid_frame is built
        self.search_var.trace("w", lambda *a: self._on_search())
        self._render_grid()

    def _render_grid(self, search_query=""):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self._photo_refs.clear()

        # filter items
        if search_query:
            items = search_item(search_query)
        elif self.active_cat == "All":
            items = list(menu.values())
        else:
            ids   = categories.get(self.active_cat, [])
            items = [menu[i] for i in ids if i in menu]

        if not items:
            tk.Label(self.grid_frame, text="No items found.",
                     font=FONTS["body"], bg=COLORS["bg"],
                     fg=COLORS["muted"]).grid(row=0, column=0, pady=40)
            return

        cols = 3
        for idx, item in enumerate(items):
            card = self._make_card(item)
            card.grid(row=idx // cols, column=idx % cols,
                      padx=8, pady=8, sticky="nsew")

        for c in range(cols):
            self.grid_frame.columnconfigure(c, weight=1)

    def _make_card(self, item):
        card = tk.Frame(self.grid_frame, bg=COLORS["bg_card"],
                        cursor="hand2")

        # Image
        photo = _load_image(item.image_path if hasattr(item, "image_path")
                            else None)
        self._photo_refs.append(photo)
        img_label = tk.Label(card, image=photo, bg=COLORS["bg_card"])
        img_label.pack(fill="x")

        # Info
        info = tk.Frame(card, bg=COLORS["bg_card"], padx=12, pady=10)
        info.pack(fill="x")

        tk.Label(info, text=item.name, font=FONTS["subhead"],
                 bg=COLORS["bg_card"], fg=COLORS["white"],
                 anchor="w", wraplength=150).pack(fill="x")
        tk.Label(info, text=item.category, font=FONTS["body_sm"],
                 bg=COLORS["bg_card"], fg=COLORS["muted"],
                 anchor="w").pack(fill="x", pady=(2, 6))

        bottom = tk.Frame(info, bg=COLORS["bg_card"])
        bottom.pack(fill="x")

        tk.Label(bottom, text=f"Rs. {item.price:.0f}",
                 font=FONTS["price"], bg=COLORS["bg_card"],
                 fg=COLORS["red"]).pack(side="left")

        tk.Button(bottom, text="+ Add",
                  command=lambda i=item: self._add_item(i),
                  bg=COLORS["red"], fg=COLORS["white"],
                  font=FONTS["btn_sm"], bd=0, cursor="hand2",
                  padx=10, pady=4,
                  activebackground=COLORS["red_hover"],
                  activeforeground=COLORS["white"]).pack(side="right")

        # hover effect
        def on_enter(e, c=card):
            c.config(highlightbackground=COLORS["red"],
                     highlightthickness=1)
        def on_leave(e, c=card):
            c.config(highlightthickness=0)

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

        return card

    def _add_item(self, item):
        add_to_cart(item.item_id, 1)
        self._refresh_cart()

    # ── cart sidebar ──────────────────────────────────────

    def _build_cart_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=COLORS["bg_sidebar"], width=280)
        sidebar.pack(side="right", fill="y")
        sidebar.pack_propagate(False)

        # Header
        hdr = tk.Frame(sidebar, bg=COLORS["red"], pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🛒  YOUR ORDER",
                 font=FONTS["heading"], bg=COLORS["red"],
                 fg=COLORS["white"]).pack()

        # Items container (scrollable)
        cart_container = tk.Frame(sidebar, bg=COLORS["bg_sidebar"])
        cart_container.pack(fill="both", expand=True, padx=14, pady=10)

        self.cart_canvas = tk.Canvas(cart_container,
                                     bg=COLORS["bg_sidebar"],
                                     highlightthickness=0)
        cart_scroll = tk.Scrollbar(cart_container, orient="vertical",
                                   command=self.cart_canvas.yview)
        self.cart_inner = tk.Frame(self.cart_canvas,
                                   bg=COLORS["bg_sidebar"])

        self.cart_inner.bind("<Configure>",
            lambda e: self.cart_canvas.configure(
                scrollregion=self.cart_canvas.bbox("all")))
        self.cart_canvas.create_window((0, 0), window=self.cart_inner,
                                       anchor="nw")
        self.cart_canvas.configure(yscrollcommand=cart_scroll.set)
        self.cart_canvas.pack(side="left", fill="both", expand=True)
        cart_scroll.pack(side="right", fill="y")

        # Divider
        tk.Frame(sidebar, bg=COLORS["border"], height=1).pack(fill="x")

        # Total + buttons
        footer = tk.Frame(sidebar, bg=COLORS["bg_sidebar"], padx=14, pady=12)
        footer.pack(fill="x")

        total_row = tk.Frame(footer, bg=COLORS["bg_sidebar"])
        total_row.pack(fill="x", pady=(0, 12))
        tk.Label(total_row, text="TOTAL",
                 font=FONTS["btn"], bg=COLORS["bg_sidebar"],
                 fg=COLORS["white"]).pack(side="left")
        self.total_label = tk.Label(total_row, text="Rs. 0",
                                    font=("Georgia", 15, "bold"),
                                    bg=COLORS["bg_sidebar"],
                                    fg=COLORS["red"])
        self.total_label.pack(side="right")

        tk.Button(footer, text="CHECKOUT →",
                  command=self._open_checkout,
                  bg=COLORS["red"], fg=COLORS["white"],
                  font=FONTS["btn"], bd=0, cursor="hand2",
                  pady=12, activebackground=COLORS["red_hover"],
                  activeforeground=COLORS["white"]).pack(fill="x")

        tk.Button(footer, text="↩ Undo last action",
                  command=self._undo,
                  bg=COLORS["bg_sidebar"], fg=COLORS["muted"],
                  font=FONTS["body_sm"], bd=0, cursor="hand2",
                  pady=4).pack(fill="x", pady=(6, 0))

        self._refresh_cart()

    def _refresh_cart(self):
        for w in self.cart_inner.winfo_children():
            w.destroy()

        if not cart:
            tk.Label(self.cart_inner, text="Your cart is empty",
                     font=FONTS["body_sm"], bg=COLORS["bg_sidebar"],
                     fg=COLORS["muted"]).pack(pady=20)
        else:
            for item, qty in cart:
                row = tk.Frame(self.cart_inner, bg=COLORS["bg_card"],
                               padx=10, pady=8)
                row.pack(fill="x", pady=3)

                left = tk.Frame(row, bg=COLORS["bg_card"])
                left.pack(side="left", fill="x", expand=True)
                tk.Label(left, text=item.name, font=FONTS["body_sm"],
                         bg=COLORS["bg_card"], fg=COLORS["white"],
                         anchor="w", wraplength=140).pack(anchor="w")
                tk.Label(left, text=f"Rs.{item.price:.0f} × {qty}",
                         font=FONTS["body_sm"], bg=COLORS["bg_card"],
                         fg=COLORS["muted"]).pack(anchor="w")

                tk.Button(row, text="✕",
                          command=lambda i=item.item_id: self._remove_item(i),
                          bg=COLORS["bg_card"], fg=COLORS["muted"],
                          font=FONTS["body_sm"], bd=0, cursor="hand2",
                          activebackground=COLORS["bg_card"],
                          activeforeground=COLORS["red"]).pack(
                              side="right", anchor="n")

        total = get_cart_total()
        self.total_label.config(text=f"Rs. {total:.0f}")

    def _remove_item(self, item_id):
        remove_from_cart(item_id)
        self._refresh_cart()

    def _undo(self):
        undo_last_action()
        self._refresh_cart()

    # ── checkout + tracking ───────────────────────────────

    def _open_checkout(self):
        if not cart:
            messagebox.showinfo("Empty cart",
                                "Add some items before checking out.",
                                parent=self.root); return

        PaymentWindow(
            parent=self.root,
            cart=list(cart),
            user=self.user,
            on_success=self._on_order_placed
        )

    def _on_order_placed(self, order_id):
        self._refresh_cart()
        messagebox.showinfo("Order Placed! 🎉",
                            f"Your order #{order_id} has been placed.\n"
                            "Track it from 'My Orders'.",
                            parent=self.root)

    def _open_tracking(self):
        from gui.tracking_window import TrackingWindow
        TrackingWindow(self.root, self.user)

    def _logout(self):
        self.root.destroy()
        self.on_logout()