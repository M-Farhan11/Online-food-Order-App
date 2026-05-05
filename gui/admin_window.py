# gui/admin_window.py
import tkinter as tk
from tkinter import messagebox, filedialog
import shutil, os
from gui.theme import COLORS, FONTS, STATUS_COLORS
from modules.menu import (
    load_menu_from_db, menu, categories,
    add_item_to_db, remove_item_from_db,
    update_item_image, set_item_availability
)
from modules.tracking import (
    get_orders_by_status, confirm_order, cancel_order,
    _get_order
)
from db import db_conn

IMG_DIR = "images"


class AdminWindow:
    def __init__(self, on_logout):
        self.on_logout      = on_logout
        self.selected_image = None   # path chosen for new item

        self.root = tk.Tk()
        self.root.title("QuickBite — Admin Panel")
        self.root.geometry("1050x680")
        self.root.configure(bg=COLORS["bg"])
        self.root.minsize(900, 580)
        self._center(1050, 680)

        load_menu_from_db()
        self._build_ui()
        self.root.mainloop()

    def _center(self, w, h):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # ── layout ────────────────────────────────────────────

    def _build_ui(self):
        # Navbar
        nav = tk.Frame(self.root, bg="#1A0008", pady=0)
        nav.pack(fill="x")
        tk.Label(nav, text="🍗 QuickBite  ·  Admin Panel",
                 font=FONTS["logo"], bg="#1A0008",
                 fg=COLORS["red"]).pack(side="left", padx=20, pady=12)
        tk.Button(nav, text="Logout",
                  command=self._logout,
                  bg=COLORS["red_dark"], fg=COLORS["white"],
                  font=FONTS["btn_sm"], bd=0, cursor="hand2",
                  padx=16, pady=8,
                  activebackground=COLORS["red"],
                  activeforeground=COLORS["white"]).pack(
                      side="right", padx=20, pady=10)

        # Two-column body
        body = tk.Frame(self.root, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)

        left  = tk.Frame(body, bg=COLORS["bg"], width=540)
        right = tk.Frame(body, bg=COLORS["bg_sidebar"], width=480)
        left.pack(side="left", fill="both", expand=True)
        right.pack(side="right", fill="both", expand=True)

        self._build_menu_panel(left)
        self._build_tracking_panel(right)

    # ══════════════════════════════════════════════════════
    # LEFT — MENU MANAGEMENT
    # ══════════════════════════════════════════════════════

    def _build_menu_panel(self, parent):
        hdr = tk.Frame(parent, bg=COLORS["red"], pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="MENU MANAGEMENT",
                 font=FONTS["heading"], bg=COLORS["red"],
                 fg=COLORS["white"]).pack()

        # Add item form
        form = tk.Frame(parent, bg=COLORS["bg_card"], padx=16, pady=14)
        form.pack(fill="x", padx=16, pady=12)
        tk.Label(form, text="ADD NEW ITEM",
                 font=FONTS["btn_sm"], bg=COLORS["bg_card"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 10))

        self.new_name     = self._form_entry(form, "Item name")
        self.new_category = self._form_entry(form, "Category (e.g. Burgers)")
        self.new_price    = self._form_entry(form, "Price in PKR")

        # Image picker
        img_row = tk.Frame(form, bg=COLORS["bg_card"])
        img_row.pack(fill="x", pady=6)
        self.img_label = tk.Label(img_row,
                                   text="No image selected",
                                   font=FONTS["body_sm"],
                                   bg=COLORS["bg_card"],
                                   fg=COLORS["muted"])
        self.img_label.pack(side="left", fill="x", expand=True)
        tk.Button(img_row, text="📷 Browse",
                  command=self._pick_image,
                  bg=COLORS["bg_input"], fg=COLORS["white"],
                  font=FONTS["btn_sm"], bd=0, cursor="hand2",
                  padx=12, pady=6,
                  activebackground=COLORS["border"],
                  activeforeground=COLORS["white"]).pack(side="right")

        tk.Button(form, text="+ ADD TO MENU",
                  command=self._add_item,
                  bg=COLORS["red"], fg=COLORS["white"],
                  font=FONTS["btn"], bd=0, cursor="hand2",
                  pady=10, activebackground=COLORS["red_hover"],
                  activeforeground=COLORS["white"]).pack(fill="x", pady=(10, 0))

        # Current menu list
        tk.Label(parent, text="CURRENT MENU",
                 font=FONTS["btn_sm"], bg=COLORS["bg"],
                 fg=COLORS["muted"]).pack(anchor="w", padx=16, pady=(4, 0))

        container = tk.Frame(parent, bg=COLORS["bg"])
        container.pack(fill="both", expand=True, padx=16, pady=(4, 16))

        canvas = tk.Canvas(container, bg=COLORS["bg"],
                           highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                  command=canvas.yview)
        self.menu_list_frame = tk.Frame(canvas, bg=COLORS["bg"])

        self.menu_list_frame.bind("<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.menu_list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._render_menu_list()

    def _form_entry(self, parent, placeholder):
        frame = tk.Frame(parent, bg=COLORS["bg_input"],
                         highlightbackground=COLORS["border"],
                         highlightthickness=1)
        frame.pack(fill="x", pady=4)
        e = tk.Entry(frame, bg=COLORS["bg_input"], fg=COLORS["muted"],
                     insertbackground=COLORS["white"],
                     font=FONTS["input"], bd=0, highlightthickness=0)
        e.insert(0, placeholder)
        e.pack(fill="x", padx=10, pady=8)

        def fi(ev):
            if e.get() == placeholder:
                e.delete(0, "end"); e.config(fg=COLORS["white"])
        def fo(ev):
            if not e.get():
                e.insert(0, placeholder); e.config(fg=COLORS["muted"])

        e.bind("<FocusIn>",  fi)
        e.bind("<FocusOut>", fo)
        return e, placeholder

    def _get_field(self, entry_tuple):
        val, ph = entry_tuple
        raw = val.get().strip()
        return "" if raw == ph else raw

    def _pick_image(self):
        path = filedialog.askopenfilename(
            title="Select item image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")]
        )
        if path:
            self.selected_image = path
            self.img_label.config(
                text=os.path.basename(path), fg=COLORS["white"])

    def _add_item(self):
        name     = self._get_field(self.new_name)
        category = self._get_field(self.new_category)
        price_s  = self._get_field(self.new_price)

        if not all([name, category, price_s]):
            messagebox.showwarning("Missing fields",
                                   "Fill in name, category, and price.",
                                   parent=self.root); return
        try:
            price = float(price_s)
            if price <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid price",
                                   "Enter a valid positive number.",
                                   parent=self.root); return

        # Copy image to images/ folder
        image_path = None
        if self.selected_image:
            os.makedirs(IMG_DIR, exist_ok=True)
            filename   = os.path.basename(self.selected_image)
            dest       = os.path.join(IMG_DIR, filename)
            shutil.copy2(self.selected_image, dest)
            image_path = dest

        # add_item_to_db needs image_path — update DB call
        item = _add_item_with_image(name, category, price, image_path)

        # reset form
        for entry, ph in [self.new_name, self.new_category, self.new_price]:
            entry.delete(0, "end"); entry.insert(0, ph); entry.config(fg=COLORS["muted"])
        self.selected_image = None
        self.img_label.config(text="No image selected", fg=COLORS["muted"])

        self._render_menu_list()
        messagebox.showinfo("Added",
                            f"'{item.name}' added to menu.",
                            parent=self.root)

    def _render_menu_list(self):
        for w in self.menu_list_frame.winfo_children():
            w.destroy()

        if not menu:
            tk.Label(self.menu_list_frame,
                     text="No menu items yet.",
                     font=FONTS["body_sm"],
                     bg=COLORS["bg"],
                     fg=COLORS["muted"]).pack(pady=20)
            return

        for item in menu.values():
            row = tk.Frame(self.menu_list_frame, bg=COLORS["bg_card"],
                           padx=12, pady=8)
            row.pack(fill="x", pady=2)

            left = tk.Frame(row, bg=COLORS["bg_card"])
            left.pack(side="left", fill="x", expand=True)
            tk.Label(left, text=item.name, font=FONTS["body"],
                     bg=COLORS["bg_card"], fg=COLORS["white"],
                     anchor="w").pack(anchor="w")
            status_text = "Available" if item.available else "Unavailable"
            status_color = COLORS["success"] if item.available else COLORS["warning"]
            tk.Label(left,
                     text=f"{item.category}  ·  Rs.{item.price:.0f}  ·  {status_text}",
                     font=FONTS["body_sm"], bg=COLORS["bg_card"],
                     fg=status_color).pack(anchor="w")

            btns = tk.Frame(row, bg=COLORS["bg_card"])
            btns.pack(side="right")

            tk.Button(btns, text="Upload Photo",
                      command=lambda i=item.item_id: self._upload_photo(i),
                      bg=COLORS["bg"], fg=COLORS["white"],
                      font=FONTS["body_sm"], bd=0, cursor="hand2",
                      activebackground=COLORS["bg"],
                      activeforeground=COLORS["red"]).pack(side="left", padx=(0, 4))

            if item.available:
                tk.Button(btns, text="Mark unavailable",
                          command=lambda i=item.item_id: self._mark_unavailable(i),
                          bg=COLORS["bg"], fg="#E74C3C",
                          font=FONTS["body_sm"], bd=0, cursor="hand2",
                          activebackground=COLORS["bg"],
                          activeforeground=COLORS["red"]).pack(side="left")
            else:
                tk.Label(btns, text="Unavailable",
                         font=FONTS["body_sm"], bg=COLORS["bg_card"],
                         fg=COLORS["warning"]).pack(side="left")

    def _remove_item(self, item_id):
        name = menu[item_id].name if item_id in menu else str(item_id)
        if messagebox.askyesno("Confirm",
                               f"Remove '{name}' from menu?",
                               parent=self.root):
            remove_item_from_db(item_id)
            self._render_menu_list()

    # ══════════════════════════════════════════════════════
    # RIGHT — ORDER TRACKING QUEUE
    # ══════════════════════════════════════════════════════

    def _build_tracking_panel(self, parent):
        hdr = tk.Frame(parent, bg="#1A0008", pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="ORDER MANAGEMENT",
                 font=FONTS["heading"], bg="#1A0008",
                 fg=COLORS["red"]).pack()

        control = tk.Frame(parent, bg=COLORS["bg_sidebar"], padx=14,
                           pady=12)
        control.pack(fill="x")
        tk.Label(control, text="Placed and confirmed orders",
                 font=FONTS["body_sm"], bg=COLORS["bg_sidebar"],
                 fg=COLORS["muted"]).pack(side="left")
        tk.Button(control, text="Refresh",
                  command=self._refresh_orders,
                  bg=COLORS["bg"], fg=COLORS["white"],
                  font=FONTS["body_sm"], bd=0, cursor="hand2",
                  padx=12, pady=8,
                  activebackground=COLORS["border"],
                  activeforeground=COLORS["white"]).pack(side="right")

        container = tk.Frame(parent, bg=COLORS["bg_sidebar"])
        container.pack(fill="both", expand=True, padx=14, pady=(6, 14))

        canvas = tk.Canvas(container, bg=COLORS["bg_sidebar"],
                           highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                  command=canvas.yview)
        self.orders_frame = tk.Frame(canvas, bg=COLORS["bg_sidebar"])

        self.orders_frame.bind("<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.orders_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._refresh_orders()

    def _refresh_orders(self):
        for w in self.orders_frame.winfo_children():
            w.destroy()

        placed_orders = get_orders_by_status("Placed")
        active_orders = [o for o in get_orders_by_status(None)
                         if o["status"] in ("Preparing", "Out for Delivery", "Delivered")]

        tk.Label(self.orders_frame, text="Placed Orders",
                 font=FONTS["btn_sm"], bg=COLORS["bg_sidebar"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 8))

        if not placed_orders:
            tk.Label(self.orders_frame,
                     text="No orders waiting for confirmation.",
                     font=FONTS["body_sm"], bg=COLORS["bg_sidebar"],
                     fg=COLORS["muted"]).pack(anchor="w", pady=(0, 12))
        else:
            for order in placed_orders:
                self._render_order_row(order, confirmable=True)

        tk.Frame(self.orders_frame, bg=COLORS["border"], height=1).pack(
            fill="x", pady=12)

        tk.Label(self.orders_frame, text="Confirmed Orders",
                 font=FONTS["btn_sm"], bg=COLORS["bg_sidebar"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 8))

        if not active_orders:
            tk.Label(self.orders_frame,
                     text="No confirmed or in-progress orders yet.",
                     font=FONTS["body_sm"], bg=COLORS["bg_sidebar"],
                     fg=COLORS["muted"]).pack(anchor="w", pady=(0, 12))
        else:
            for order in active_orders:
                self._render_order_row(order, confirmable=False)

    def _render_order_row(self, order, confirmable: bool):
        row = tk.Frame(self.orders_frame, bg=COLORS["bg_card"],
                       padx=12, pady=10)
        row.pack(fill="x", pady=4)

        top = tk.Frame(row, bg=COLORS["bg_card"])
        top.pack(fill="x")

        tk.Label(top, text=f"Order #{order['order_id']}  ·  User {order['user_id']}",
                 font=FONTS["subhead"], bg=COLORS["bg_card"],
                 fg=COLORS["white"]).pack(side="left")

        status_color = STATUS_COLORS.get(order["status"], COLORS["muted"])
        tk.Label(top, text=f"  {order['status']}  ",
                 font=FONTS["body_sm"], bg=status_color,
                 fg=COLORS["white"]).pack(side="right")

        tk.Label(row,
                 text=f"{order['payment_method']} · Rs.{order['total_amount']:.0f} · {order['created_at']}",
                 font=FONTS["body_sm"], bg=COLORS["bg_card"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(6, 0))

        actions = tk.Frame(row, bg=COLORS["bg_card"])
        actions.pack(fill="x", pady=(8, 0))

        if confirmable:
            tk.Button(actions, text="Confirm",
                      command=lambda i=order['order_id']: self._confirm_order(i),
                      bg=COLORS["red"], fg=COLORS["white"],
                      font=FONTS["body_sm"], bd=0, cursor="hand2",
                      padx=10, pady=6,
                      activebackground=COLORS["red_hover"],
                      activeforeground=COLORS["white"]).pack(side="left", padx=(0, 6))

        if order['status'] not in ("Delivered", "Cancelled"):
            tk.Button(actions, text="Cancel",
                      command=lambda i=order['order_id']: self._cancel_order(i),
                      bg=COLORS["bg"], fg="#E74C3C",
                      font=FONTS["body_sm"], bd=0, cursor="hand2",
                      padx=10, pady=6,
                      activebackground=COLORS["bg"],
                      activeforeground=COLORS["red"]).pack(side="left")

    def _confirm_order(self, order_id):
        msg = confirm_order(order_id)
        messagebox.showinfo("Order Update", msg, parent=self.root)
        self._refresh_orders()

    def _cancel_order(self, order_id):
        msg = cancel_order(order_id)
        messagebox.showinfo("Order Update", msg, parent=self.root)
        self._refresh_orders()

    def _upload_photo(self, item_id):
        path = filedialog.askopenfilename(
            title="Select item image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")]
        )
        if not path:
            return
        os.makedirs(IMG_DIR, exist_ok=True)
        dest = os.path.join(IMG_DIR, os.path.basename(path))
        shutil.copy2(path, dest)
        update_item_image(item_id, dest)
        self._render_menu_list()
        messagebox.showinfo("Updated", "Item image updated.",
                            parent=self.root)

    def _mark_unavailable(self, item_id):
        item = menu.get(item_id)
        if not item:
            return
        if messagebox.askyesno("Confirm",
                               f"Mark '{item.name}' as unavailable?",
                               parent=self.root):
            set_item_availability(item_id, False)
            item.available = False
            self._render_menu_list()
            messagebox.showinfo("Updated",
                                f"'{item.name}' is now unavailable.",
                                parent=self.root)

    def _logout(self):
        self.root.destroy()
        self.on_logout()


# ── helper: insert item with image_path ───────────────────

def _add_item_with_image(name, category, price, image_path=None):
    """Extends add_item_to_db to also store image_path."""
    from models.menu_item import MenuItem
    conn   = db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO menu_items (name, category, price, image_path) "
        "VALUES (%s, %s, %s, %s)",
        (name, category, price, image_path)
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close(); conn.close()

    from modules.menu import menu, categories
    item = MenuItem(new_id, name, category, price)
    item.image_path = image_path
    menu[new_id] = item
    categories.setdefault(category, []).append(new_id)
    return item