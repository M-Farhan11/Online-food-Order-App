import tkinter as tk

root = tk.Tk()

root.title("Online Food App")
root.geometry("600x600")
root.resizable(False, False)

lable = tk.Label(root, text="Welcome to our Application")
lable.pack()
root.mainloop()

#python -m gui.login_window