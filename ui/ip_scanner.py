import tkinter as tk
from tkinter import ttk
import subprocess
import time
import win32gui
import win32con
import win32process


def build_ip_scanner_tab(tabs):

    tab = ttk.Frame(tabs)
    tabs.add(tab, text="IP Scanner")

    ipscan_hwnd = None
    ipscan_process = None
    ipscan_started = False

    # ---------------- LAUNCH ANGRY IP ---------------- #
    def launch_ipscan():
        nonlocal ipscan_process, ipscan_hwnd

        path = r"C:\Users\brend\Documents\Network\tools\AngryIP\ipscan.exe"

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0

        ipscan_process = subprocess.Popen(
            path,
            startupinfo=startupinfo
        )

        def enum_windows_callback(hwnd, windows):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == ipscan_process.pid:
                windows.append(hwnd)

        windows = []
        for _ in range(50):
            win32gui.EnumWindows(enum_windows_callback, windows)
            if windows:
                break
            time.sleep(0.01)

        if windows:
            hwnd = windows[0]
            ipscan_hwnd = hwnd

            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)

            container_hwnd = ipscan_container.winfo_id()

            win32gui.SetParent(ipscan_hwnd, container_hwnd)

            style = win32gui.GetWindowLong(ipscan_hwnd, win32con.GWL_STYLE)
            style = style & ~win32con.WS_CAPTION & ~win32con.WS_THICKFRAME
            win32gui.SetWindowLong(ipscan_hwnd, win32con.GWL_STYLE, style)

            win32gui.SetWindowPos(
                ipscan_hwnd,
                None,
                0, 0,
                ipscan_container.winfo_width(),
                ipscan_container.winfo_height(),
                win32con.SWP_NOZORDER
            )
        else:
            print("Angry IP Scanner window not found")

    # ---------------- AUTO LOAD CHECK ---------------- #
    def check_and_launch():

        nonlocal ipscan_hwnd, ipscan_started

        current_tab = tabs.tab(tabs.select(), "text")

        if current_tab == "IP Scanner" and not ipscan_started:
            ipscan_started = True
            launch_ipscan()

        tab.after(500, check_and_launch)

    # ---------------- CONTAINER ---------------- #
    ipscan_container = tk.Frame(tab, bg="black")
    ipscan_container.pack(fill="both", expand=True, padx=10, pady=10)

    # ---------------- RESIZE ---------------- #
    def resize_ipscan(event):
        if ipscan_hwnd:
            win32gui.SetWindowPos(
                ipscan_hwnd,
                None,
                0, 0,
                ipscan_container.winfo_width(),
                ipscan_container.winfo_height(),
                win32con.SWP_NOZORDER
            )

    ipscan_container.bind("<Configure>", resize_ipscan)

    # ---------------- START LOOP ---------------- #
    tab.after(500, check_and_launch)