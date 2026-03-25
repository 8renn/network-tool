import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import time
import win32gui
import win32con
import win32process  # ✅ ADDED

def build_mtr_tab(tabs):

    tab = ttk.Frame(tabs)
    tabs.add(tab, text="MTR")

    def on_tab_selected(event):
        nonlocal winmtr_hwnd

        selected_tab = event.widget.select()
        if event.widget.tab(selected_tab, "text") == "MTR":
            if winmtr_hwnd is None:
                launch_winmtr()

    tabs.bind("<<NotebookTabChanged>>", on_tab_selected)

    winmtr_hwnd = None
    winmtr_process = None

    def launch_winmtr():
        nonlocal winmtr_process, winmtr_hwnd

        winmtr_path = r"C:\Users\brend\Documents\Network\tools\WinMTR\WinMTR.exe"

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE

        winmtr_process = subprocess.Popen(
            winmtr_path,
            startupinfo=startupinfo
        )

        # -------- FIND WINMTR WINDOW (FIXED) -------- #
        def enum_windows_callback(hwnd, windows):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == winmtr_process.pid:
                windows.append(hwnd)

        windows = []
        for _ in range(50):  # ~0.5 seconds total
            win32gui.EnumWindows(enum_windows_callback, windows)
            if windows:
                break
            time.sleep(0.01)

        if windows:
            hwnd = windows[0]
            winmtr_hwnd = hwnd

            container_hwnd = mtr_container.winfo_id()

            win32gui.SetParent(winmtr_hwnd, container_hwnd)

            style = win32gui.GetWindowLong(winmtr_hwnd, win32con.GWL_STYLE)
            style = style & ~win32con.WS_CAPTION & ~win32con.WS_THICKFRAME
            win32gui.SetWindowLong(winmtr_hwnd, win32con.GWL_STYLE, style)

            win32gui.SetWindowPos(
                winmtr_hwnd,
                None,
                0, 0,
                mtr_container.winfo_width(),
                mtr_container.winfo_height(),
                win32con.SWP_NOZORDER
            )
        else:
            print("WinMTR window not found")

    # ---------------- MTR CONTAINER ---------------- #
    mtr_container = tk.Frame(tab, bg="black")
    mtr_container.pack(fill="both", expand=True, padx=10, pady=10)
    def resize_winmtr(event):
        if winmtr_hwnd:
            win32gui.SetWindowPos(
                winmtr_hwnd,
                None,
                0, 0,
                event.width,
                event.height,
                win32con.SWP_NOZORDER
            )

    mtr_container.bind("<Configure>", resize_winmtr)

    