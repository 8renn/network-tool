import tkinter as tk
from tkinter import ttk
import threading
import subprocess

# ---------------- SHARED DATA ---------------- #
LAST_MTR = ""
mtr_running = False
mtr_process = None


def build_mtr_tab(tabs):

    tab_mtr = ttk.Frame(tabs)
    tabs.add(tab_mtr, text="MTR")

    # ---------------- MAIN / RESULT FRAMES ---------------- #
    mtr_main_frame = tk.Frame(tab_mtr)
    mtr_main_frame.pack(fill="both", expand=True)

    mtr_result_frame = tk.Frame(tab_mtr)

    # ---------------- HEADER ---------------- #
    tk.Label(
        mtr_main_frame,
        text="MTR Tool",
        font=("Segoe UI", 18, "bold")
    ).pack(pady=10)

    instructions = (
        "1. Input customer server URL in the following format, XXXXX.prismpbx.com.\n"
        "2. Select Run.\n"
        "3. Review real-time path analysis results."
    )

    tk.Label(
        mtr_main_frame,
        text=instructions,
        justify="left",
        font=("Segoe UI", 10)
    ).pack(anchor="w", padx=20, pady=10)

    # ---------------- INPUT ---------------- #
    entry_frame = tk.Frame(mtr_main_frame)
    entry_frame.pack(pady=10)

    mtr_entry = tk.Entry(entry_frame, width=30, font=("Segoe UI", 12))
    mtr_entry.pack(side="left")

    tk.Label(entry_frame, text=".prismpbx.com", font=("Segoe UI", 12)).pack(side="left")

    # ---------------- OUTPUT ---------------- #
    mtr_output = tk.Text(
        mtr_result_frame,
        font=("Consolas", 10),
        bg="black",
        fg="white"
    )

    # ---------------- FUNCTIONS ---------------- #

    def start_mtr():
        global mtr_running, mtr_process, LAST_MTR

        mtr_running = True
        output_lines = []

        host = mtr_entry.get().strip()
        if not host:
            return

        full_host = f"{host}.prismpbx.com"

        # Switch screens
        mtr_main_frame.pack_forget()
        mtr_result_frame.pack(fill="both", expand=True)

        mtr_output.pack(fill="both", expand=True, padx=10, pady=10)
        mtr_output.delete("1.0", tk.END)
        mtr_output.insert(tk.END, f"Running MTR for {full_host}...\n\n")

        def run():
            global mtr_process, LAST_MTR

            try:
                mtr_process = subprocess.Popen(
                    ["tracert", full_host],  # Windows fallback
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                while True:
                    if not mtr_running:
                        try:
                            mtr_process.terminate()
                        except:
                            pass
                        break

                    line = mtr_process.stdout.readline()

                    if not line:
                        break

                    output_lines.append(line)

                    mtr_output.insert(tk.END, line)
                    mtr_output.see(tk.END)

                mtr_process = None

                # Save for Full Network Report
                LAST_MTR = "".join(output_lines)

            except Exception as e:
                mtr_output.insert(tk.END, f"\nError: {e}")

        threading.Thread(target=run, daemon=True).start()

    def stop_mtr():
        global mtr_running, mtr_process

        mtr_running = False

        if mtr_process:
            try:
                mtr_process.terminate()
            except:
                pass

    def go_back_to_mtr_main():
        global mtr_running
        mtr_running = False

        mtr_result_frame.pack_forget()
        mtr_main_frame.pack(fill="both", expand=True)

    def start_mtr_from_main():
        start_mtr()

    # ---------------- BUTTONS ---------------- #

    tk.Button(
        mtr_main_frame,
        text="Run",
        command=start_mtr_from_main,
        width=20,
        height=2
    ).pack(pady=5)

    mtr_entry.bind("<Return>", lambda e: start_mtr_from_main())

    mtr_top_bar = tk.Frame(mtr_result_frame)
    mtr_top_bar.pack(fill="x", pady=10)

    tk.Button(
        mtr_top_bar,
        text="Back",
        width=10,
        command=go_back_to_mtr_main
    ).pack(side="left", padx=5)

    tk.Button(
        mtr_top_bar,
        text="Start MTR",
        width=15,
        command=start_mtr
    ).pack(side="left", padx=5)

    tk.Button(
        mtr_top_bar,
        text="Stop MTR",
        width=15,
        command=stop_mtr
    ).pack(side="left", padx=5)