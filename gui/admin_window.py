# gui/admin_window.py
import tkinter as tk
from tkinter import messagebox, filedialog
import shutil
import os
from gui.theme import COLORS, FONTS, STATUS_COLORS
from modules.menu import (
    load_menu_from_db, menu, categories,
    add_item_to_db, remove_item_from_db,
    update_item_image, set_item_availability, update_item_price
)
from modules.tracking import (
    get_orders_by_status, confirm_order, cancel_order, _get_order
)
from db import db_conn

IMG_DIR = "images"


class AdminWindow:
    def __init__(self, on_logout):
        self.on_logout      = on_logout
        self.selected_image = None

        self.root = tk.Tk()
        self.root.title("QuickBite — Admin Panel")
        self.root.geometry("1100x700")
        self.root.configure(bg=COLORS["bg"])
        self.root.minsize(950, 600)
        self._center(1100, 700)

        # Admin always loads ALL items including unavailable ones
        # so they can be re-enabled. include_unavailable=True
        load_menu_from_db(include_unavailable=True)

        self._build_ui()
        self.root.mainloop()

    def _center(self, w, h):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # ── top-level layout ──────────────────────────────────

    def _build_ui(self):
        nav = tk.Frame(self.root, bg="#1A0008")
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

        body = tk.Frame(self.root, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)

        left  = tk.Frame(body, bg=COLORS["bg"])
        right = tk.Frame(body, bg=COLORS["bg_sidebar"])
        left.pack(side="left",  fill="both", expand=True)
        right.pack(side="right", fill="both", expand=True)

        self._build_menu_panel(left)
        self._build_order_panel(right)

    # ══════════════════════════════════════════════════════
    # LEFT — MENU MANAGEMENT
    # ══════════════════════════════════════════════════════

    def _build_menu_panel(self, parent):
        hdr = tk.Frame(parent, bg=COLORS["red"], pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="MENU MANAGEMENT",
                 font=FONTS["heading"], bg=COLORS["red"],
                 fg=COLORS["white"]).pack()

        # ── Add item form ─────────────────────────────────
        form = tk.Frame(parent, bg=COLORS["bg_card"], padx=16, pady=14)
        form.pack(fill="x", padx=16, pady=12)

        tk.Label(form, text="ADD NEW ITEM",
                 font=FONTS["btn_sm"], bg=COLORS["bg_card"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 8))

        self.new_name     = self._form_entry(form, "Item name")
        self.new_category = self._form_entry(form, "Category  (e.g. Burgers)")
        self.new_price    = self._form_entry(form, "Price in PKR")

        img_row = tk.Frame(form, bg=COLORS["bg_card"])
        img_row.pack(fill="x", pady=6)
        self.img_label = tk.Label(img_row, text="No image selected",
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
                  pady=10,
                  activebackground=COLORS["red_hover"],
                  activeforeground=COLORS["white"]).pack(
                      fill="x", pady=(10, 0))

        # ── Current menu list ─────────────────────────────
        list_hdr = tk.Frame(parent, bg=COLORS["bg"], padx=16)
        list_hdr.pack(fill="x", pady=(4, 0))
        tk.Label(list_hdr, text="CURRENT MENU  (✓ available  ✗ hidden)",
                 font=FONTS["btn_sm"], bg=COLORS["bg"],
                 fg=COLORS["muted"]).pack(side="left")
        tk.Button(list_hdr, text="↻",
                  command=self._render_menu_list,
                  bg=COLORS["bg"], fg=COLORS["muted"],
                  font=FONTS["body_sm"], bd=0,
                  cursor="hand2").pack(side="right")

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
        canvas.create_window((0, 0), window=self.menu_list_frame,
                              anchor="nw")
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
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")])
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

        image_path = None
        if self.selected_image:
            os.makedirs(IMG_DIR, exist_ok=True)
            dest = os.path.join(IMG_DIR, os.path.basename(self.selected_image))
            shutil.copy2(self.selected_image, dest)
            image_path = dest

        item = add_item_to_db(name, category, price, image_path)

        # Reset form
        for entry, ph in [self.new_name, self.new_category, self.new_price]:
            entry.delete(0, "end")
            entry.insert(0, ph)
            entry.config(fg=COLORS["muted"])
        self.selected_image = None
        self.img_label.config(text="No image selected", fg=COLORS["muted"])

        self._render_menu_list()
        messagebox.showinfo("Added", f"'{item.name}' added to menu.",
                            parent=self.root)

    def _render_menu_list(self):
        """
        Renders ALL menu items — both available and unavailable.
        Unavailable items are shown with a ✗ badge and an Enable button
        so admin can re-activate them. They are NOT hidden.
        """
        for w in self.menu_list_frame.winfo_children():
            w.destroy()

        if not menu:
            tk.Label(self.menu_list_frame, text="No menu items yet.",
                     font=FONTS["body_sm"], bg=COLORS["bg"],
                     fg=COLORS["muted"]).pack(pady=20)
            return

        for item in menu.values():
            # Card background slightly different for unavailable items
            card_bg = COLORS["bg_card"] if item.available else "#1A0A0A"
            row = tk.Frame(self.menu_list_frame, bg=card_bg,
                           padx=12, pady=8)
            row.pack(fill="x", pady=2)

            # Left info
            left = tk.Frame(row, bg=card_bg)
            left.pack(side="left", fill="x", expand=True)

            name_color = COLORS["white"] if item.available else COLORS["muted"]
            tk.Label(left, text=item.name, font=FONTS["body"],
                     bg=card_bg, fg=name_color,
                     anchor="w").pack(anchor="w")

            status_text  = "✓ Available" if item.available else "✗ Hidden from customers"
            status_color = COLORS["success"] if item.available else "#E74C3C"
            tk.Label(left,
                     text=f"{item.category}  ·  Rs.{item.price:.0f}  ·  {status_text}",
                     font=FONTS["body_sm"], bg=card_bg,
                     fg=status_color).pack(anchor="w")

            # Right buttons
            btns = tk.Frame(row, bg=card_bg)
            btns.pack(side="right")

            # Photo update button
            tk.Button(btns, text="📷",
                      command=lambda i=item.item_id: self._upload_photo(i),
                      bg=card_bg, fg=COLORS["white"],
                      font=FONTS["body_sm"], bd=0, cursor="hand2",
                      padx=6, pady=4,
                      activebackground=card_bg,
                      activeforeground=COLORS["red"]).pack(
                          side="left", padx=2)

            # Price edit button
            tk.Button(btns, text="💰 Price",
                      command=lambda i=item.item_id: self._edit_price(i),
                      bg=card_bg, fg=COLORS["white"],
                      font=FONTS["body_sm"], bd=0, cursor="hand2",
                      padx=8, pady=4,
                      activebackground=card_bg,
                      activeforeground=COLORS["red"]).pack(
                          side="left", padx=2)

            # Enable / Disable toggle — both always shown, label changes
            if item.available:
                tk.Button(btns, text="Disable",
                          command=lambda i=item.item_id: self._toggle_availability(i),
                          bg=card_bg, fg="#E74C3C",
                          font=FONTS["body_sm"], bd=0, cursor="hand2",
                          padx=8, pady=4,
                          activebackground=card_bg,
                          activeforeground=COLORS["red"]).pack(
                              side="left", padx=2)
            else:
                tk.Button(btns, text="Enable",
                          command=lambda i=item.item_id: self._toggle_availability(i),
                          bg=card_bg, fg=COLORS["success"],
                          font=FONTS["body_sm"], bd=0, cursor="hand2",
                          padx=8, pady=4,
                          activebackground=card_bg,
                          activeforeground=COLORS["success"]).pack(
                              side="left", padx=2)

    def _toggle_availability(self, item_id):
        """
        Toggles is_available in DB and updates in-memory menu dict.
        The item stays in the dict regardless — admin list always shows all items.
        Customers only see items where is_available = 1.
        """
        item = menu.get(item_id)
        if not item:
            return

        new_state = not item.available
        action    = "available" if new_state else "unavailable"

        if not messagebox.askyesno(
                "Confirm",
                f"Mark '{item.name}' as {action}?",
                parent=self.root):
            return

        set_item_availability(item_id, new_state)   # updates DB + menu dict
        self._render_menu_list()                     # re-render with new state
        messagebox.showinfo("Updated",
                            f"'{item.name}' is now {action}.",
                            parent=self.root)

    def _upload_photo(self, item_id):
        path = filedialog.askopenfilename(
            title="Select item image",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")])
        if not path:
            return
        os.makedirs(IMG_DIR, exist_ok=True)
        dest = os.path.join(IMG_DIR, os.path.basename(path))
        shutil.copy2(path, dest)
        update_item_image(item_id, dest)
        self._render_menu_list()
        messagebox.showinfo("Updated", "Item image updated.",
                            parent=self.root)

    def _edit_price(self, item_id):
        """
        Opens a small dialog to update item price.
        Price change only affects future orders.
        Past orders are protected by the snapshot columns in order_items.
        """
        item = menu.get(item_id)
        if not item:
            return

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Price — {item.name}")
        dialog.geometry("320x160")
        dialog.resizable(False, False)
        dialog.configure(bg=COLORS["bg"])
        dialog.grab_set()

        tk.Label(dialog,
                 text=f"Current: Rs. {item.price:.0f}",
                 font=FONTS["body"], bg=COLORS["bg"],
                 fg=COLORS["muted"]).pack(pady=(14, 0))

        box = tk.Frame(dialog, bg=COLORS["bg_input"],
                       highlightbackground=COLORS["border"],
                       highlightthickness=1)
        box.pack(fill="x", padx=24, pady=10)
        price_entry = tk.Entry(box, bg=COLORS["bg_input"],
                               fg=COLORS["white"],
                               insertbackground=COLORS["white"],
                               font=FONTS["input"], bd=0,
                               highlightthickness=0)
        price_entry.insert(0, str(int(item.price)))
        price_entry.pack(fill="x", padx=10, pady=8)
        price_entry.focus_set()
        price_entry.select_range(0, "end")

        def save():
            try:
                new_price = float(price_entry.get().strip())
                if new_price <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Invalid",
                                       "Enter a valid positive price.",
                                       parent=dialog)
                return
            update_item_price(item_id, new_price)
            dialog.destroy()
            self._render_menu_list()
            messagebox.showinfo(
                "Price Updated",
                f"'{item.name}' price updated to Rs. {new_price:.0f}.\n"
                f"All past orders keep their original price.",
                parent=self.root)

        price_entry.bind("<Return>", lambda e: save())

        bf = tk.Frame(dialog, bg=COLORS["bg"])
        bf.pack(fill="x", padx=24, pady=(0, 12))
        tk.Button(bf, text="Save", command=save,
                  bg=COLORS["red"], fg=COLORS["white"],
                  font=FONTS["btn_sm"], bd=0, cursor="hand2",
                  padx=16, pady=8,
                  activebackground=COLORS["red_hover"],
                  activeforeground=COLORS["white"]).pack(side="left",
                                                         padx=(0, 8))
        tk.Button(bf, text="Cancel", command=dialog.destroy,
                  bg=COLORS["bg"], fg=COLORS["muted"],
                  font=FONTS["body_sm"], bd=0,
                  cursor="hand2").pack(side="left")

    # ══════════════════════════════════════════════════════
    # RIGHT — ORDER MANAGEMENT
    # ══════════════════════════════════════════════════════

    def _build_order_panel(self, parent):
        hdr = tk.Frame(parent, bg="#1A0008", pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="ORDER MANAGEMENT",
                 font=FONTS["heading"], bg="#1A0008",
                 fg=COLORS["red"]).pack()

        ctrl = tk.Frame(parent, bg=COLORS["bg_sidebar"], padx=14, pady=8)
        ctrl.pack(fill="x")
        tk.Label(ctrl,
                 text="Confirm or cancel incoming orders",
                 font=FONTS["body_sm"], bg=COLORS["bg_sidebar"],
                 fg=COLORS["muted"]).pack(side="left")
        tk.Button(ctrl, text="↻ Refresh",
                  command=self._refresh_orders,
                  bg=COLORS["bg"], fg=COLORS["white"],
                  font=FONTS["body_sm"], bd=0, cursor="hand2",
                  padx=12, pady=6,
                  activebackground=COLORS["border"],
                  activeforeground=COLORS["white"]).pack(side="right")

        container = tk.Frame(parent, bg=COLORS["bg_sidebar"])
        container.pack(fill="both", expand=True, padx=14, pady=(4, 14))

        canvas = tk.Canvas(container, bg=COLORS["bg_sidebar"],
                           highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                  command=canvas.yview)
        self.orders_frame = tk.Frame(canvas, bg=COLORS["bg_sidebar"])
        self.orders_frame.bind("<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.orders_frame,
                              anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._refresh_orders()

    def _refresh_orders(self):
        for w in self.orders_frame.winfo_children():
            w.destroy()

        # Orders that need admin action
        pending = (get_orders_by_status("Placed") +
                   get_orders_by_status("Payment Pending"))

        # Orders already in progress
        active = [o for o in get_orders_by_status(None)
                  if o["status"] in ("Preparing", "Out for Delivery",
                                     "Delivered", "Cancelled")]

        # ── Pending section ───────────────────────────────
        tk.Label(self.orders_frame,
                 text="AWAITING CONFIRMATION",
                 font=FONTS["btn_sm"], bg=COLORS["bg_sidebar"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 6))

        if not pending:
            tk.Label(self.orders_frame,
                     text="No orders waiting for confirmation.",
                     font=FONTS["body_sm"], bg=COLORS["bg_sidebar"],
                     fg=COLORS["muted"]).pack(anchor="w", pady=(0, 10))
        else:
            for order in pending:
                self._render_order_card(order, confirmable=True)

        tk.Frame(self.orders_frame, bg=COLORS["border"],
                 height=1).pack(fill="x", pady=10)

        # ── Active / history section ──────────────────────
        tk.Label(self.orders_frame,
                 text="ACTIVE & RECENT ORDERS",
                 font=FONTS["btn_sm"], bg=COLORS["bg_sidebar"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(0, 6))

        if not active:
            tk.Label(self.orders_frame,
                     text="No active orders.",
                     font=FONTS["body_sm"], bg=COLORS["bg_sidebar"],
                     fg=COLORS["muted"]).pack(anchor="w")
        else:
            for order in active:
                self._render_order_card(order, confirmable=False)

    def _render_order_card(self, order, confirmable: bool):
        status = order["status"]

        # Special label for Payment Pending
        is_online_pending = (status == "Payment Pending")

        card = tk.Frame(self.orders_frame, bg=COLORS["bg_card"],
                        padx=12, pady=10)
        card.pack(fill="x", pady=4)

        # Top row
        top = tk.Frame(card, bg=COLORS["bg_card"])
        top.pack(fill="x")
        tk.Label(top,
                 text=f"Order #{order['order_id']}  ·  User {order['user_id']}",
                 font=FONTS["subhead"], bg=COLORS["bg_card"],
                 fg=COLORS["white"]).pack(side="left")

        badge_color = STATUS_COLORS.get(status, COLORS["muted"])
        badge_text  = (f"  {status}  " if not is_online_pending
                       else "  💳 Payment Pending  ")
        tk.Label(top, text=badge_text,
                 font=FONTS["body_sm"], bg=badge_color,
                 fg=COLORS["white"]).pack(side="right")

        # Meta line
        meta = f"{order['payment_method']}  ·  Rs.{order['total_amount']:.0f}  ·  {order['created_at']}"
        tk.Label(card, text=meta,
                 font=FONTS["body_sm"], bg=COLORS["bg_card"],
                 fg=COLORS["muted"]).pack(anchor="w", pady=(6, 0))

        # Online-pending explanation
        if is_online_pending:
            tk.Label(card,
                     text="⚠ Customer paid online — verify details then confirm.",
                     font=FONTS["body_sm"], bg=COLORS["bg_card"],
                     fg=COLORS["warning"]).pack(anchor="w", pady=(4, 0))

        # Action buttons
        actions = tk.Frame(card, bg=COLORS["bg_card"])
        actions.pack(fill="x", pady=(8, 0))

        if confirmable:
            confirm_label = ("Confirm Order" if status == "Placed"
                             else "Confirm Payment & Start")
            tk.Button(actions, text=confirm_label,
                      command=lambda i=order["order_id"]: self._confirm(i),
                      bg=COLORS["red"], fg=COLORS["white"],
                      font=FONTS["body_sm"], bd=0, cursor="hand2",
                      padx=10, pady=6,
                      activebackground=COLORS["red_hover"],
                      activeforeground=COLORS["white"]).pack(
                          side="left", padx=(0, 6))

        if status not in ("Delivered", "Cancelled"):
            tk.Button(actions, text="Cancel Order",
                      command=lambda i=order["order_id"]: self._cancel(i),
                      bg=COLORS["bg"], fg="#E74C3C",
                      font=FONTS["body_sm"], bd=0, cursor="hand2",
                      padx=10, pady=6,
                      activebackground=COLORS["bg"],
                      activeforeground=COLORS["red"]).pack(side="left")

    def _confirm(self, order_id):
        msg = confirm_order(order_id)
        messagebox.showinfo("Order Updated", msg, parent=self.root)
        self._refresh_orders()

    def _cancel(self, order_id):
        if messagebox.askyesno("Confirm Cancel",
                               f"Cancel Order #{order_id}?",
                               parent=self.root):
            msg = cancel_order(order_id)
            messagebox.showinfo("Order Updated", msg, parent=self.root)
            self._refresh_orders()

    def _logout(self):
        self.root.destroy()
        self.on_logout()