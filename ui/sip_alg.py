import tkinter as tk
from tkinter import ttk

# ---------------- SHARED DATA ---------------- #
LAST_SIP_RESULT = "Not Run"


def sip_alg_check(sip_result_label):
    import socket

    global LAST_SIP_RESULT

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(2)

        message = b"OPTIONS sip:test SIP/2.0\r\nVia: SIP/2.0/UDP test\r\n\r\n"
        s.sendto(message, ("8.8.8.8", 5060))

        try:
            s.recvfrom(1024)

            sip_result_label.config(
                text="SIP ALG Detected",
                bg="red"
            )
            LAST_SIP_RESULT = "SIP ALG Detected"

        except socket.timeout:
            sip_result_label.config(
                text="SIP ALG Not Detected",
                bg="green"
            )
            LAST_SIP_RESULT = "SIP ALG Not Detected"

    except Exception:
        sip_result_label.config(
            text="Server Error: Unable to Detect SIP ALG",
            bg="orange"
        )
        LAST_SIP_RESULT = "Error"

    finally:
        try:
            s.close()
        except:
            pass


def build_sip_tab(tabs):
    tab = ttk.Frame(tabs)
    tabs.add(tab, text="SIP ALG")

    # --- SIP HEADER --- #
    tk.Label(
        tab,
        text="SIP Detector",
        font=("Segoe UI", 18, "bold")
    ).pack(pady=10)

    # --- CENTER FRAME --- #
    center_frame = tk.Frame(tab)
    center_frame.pack(expand=True)

    sip_result_label = tk.Label(
        center_frame,
        text="Run SIP ALG Test",
        font=("Segoe UI", 14, "bold"),
        fg="white",
        bg="gray",
        width=40,
        height=5
    )
    sip_result_label.pack(pady=10)

    # --- RUN BUTTON --- #
    tk.Button(
        tab,
        text="Run Test",
        command=lambda: sip_alg_check(sip_result_label),
        width=20,
        height=2
    ).pack(pady=10)