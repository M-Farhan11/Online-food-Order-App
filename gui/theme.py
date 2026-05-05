# gui/theme.py
# Shared theme constants — KFC-inspired dark red + black

COLORS = {
    "bg":           "#0A0A0A",   # near-black background
    "bg_card":      "#161616",   # card / panel background
    "bg_input":     "#1E1E1E",   # input field background
    "bg_sidebar":   "#111111",   # sidebar / cart panel
    "red":          "#C8102E",   # KFC red — primary accent
    "red_hover":    "#E8192E",   # lighter red on hover
    "red_dark":     "#9B0B20",   # darker red for pressed
    "white":        "#FFFFFF",
    "off_white":    "#F0EDE8",   # warm off-white for body text
    "muted":        "#888888",   # muted/secondary text
    "border":       "#2A2A2A",   # subtle borders
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
    "Placed":            "#F39C12",
    "Preparing":         "#3498DB",
    "Out for Delivery":  "#9B59B6",
    "Delivered":         "#2ECC71",
}