# gui/theme.py
# Shared theme constants — KFC-inspired dark red + black

COLORS = {
    "bg":           "#0A0A0A",
    "bg_card":      "#161616",
    "bg_input":     "#1E1E1E",
    "bg_sidebar":   "#111111",
    "red":          "#C8102E",
    "red_hover":    "#E8192E",
    "red_dark":     "#9B0B20",
    "white":        "#FFFFFF",
    "off_white":    "#F0EDE8",
    "muted":        "#888888",
    "border":       "#2A2A2A",
    "success":      "#2ECC71",
    "warning":      "#F39C12",
}

FONTS = {
    "title":    ("Georgia", 26, "bold"),
    "heading":  ("Georgia", 16, "bold"),
    "subhead":  ("Georgia", 12, "bold"),
    "body":     ("Helvetica", 11),
    "body_sm":  ("Helvetica", 9),
    "btn":      ("Helvetica", 11, "bold"),
    "btn_sm":   ("Helvetica", 9, "bold"),
    "price":    ("Georgia", 13, "bold"),
    "logo":     ("Georgia", 22, "bold"),
    "input":    ("Helvetica", 11),
}

PADDING = {
    "window":  16,
    "card":    12,
    "btn":     (10, 24),
    "btn_sm":  (6, 14),
}

STATUS_COLORS = {
    "Placed":            "#F39C12",   # amber
    "Payment Pending":   "#8E44AD",   # purple — online payment awaiting admin
    "Preparing":         "#3498DB",   # blue
    "Out for Delivery":  "#1ABC9C",   # teal
    "Delivered":         "#2ECC71",   # green
    "Cancelled":         "#E74C3C",   # red
}