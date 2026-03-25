import tkinter as tk
from tkinter import ttk

def build_welcome_tab(tabs):

    tab = ttk.Frame(tabs)
    tabs.add(tab, text="Welcome")

    label = tk.Label(
        tab,
        text="Welcome to Advanced Network Tool\n\n"
             "Use the tabs above to run network diagnostics.\n\n"
             "• IP Scanner\n"
             "• MTR\n"
             "• SIP ALG\n"
             "• System Info\n"
             "• Full Network Report",
        font=("Segoe UI", 14),
        justify="center"
    )

    label.place(relx=0.5, rely=0.5, anchor="center")