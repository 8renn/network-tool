import tkinter as tk
from tkinter import ttk
import datetime

# IMPORT SHARED DATA
from ui.system_info import LAST_SYSTEM_INFO
from ui.traceroute import LAST_TRACEROUTE
from ui.sip_alg import LAST_SIP_RESULT


# ---------------- REPORT LOGIC ---------------- #
def generate_report(report_output, report_header):
    report_output.delete("1.0", tk.END)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_header.config(text=f"Full Network Report - {now}")

    # ---------------- SYSTEM INFO ---------------- #
    sys_data = f"""
Default Gateway: {LAST_SYSTEM_INFO.get('gateway', 'N/A')}
IPv4 Address: {LAST_SYSTEM_INFO.get('ip', 'N/A')}
Public IP: {LAST_SYSTEM_INFO.get('public_ip', 'N/A')}
ISP: {LAST_SYSTEM_INFO.get('isp', 'N/A')}
Cloudflare: {LAST_SYSTEM_INFO.get('cloudflare', 'N/A')}
Ookla: {LAST_SYSTEM_INFO.get('ookla', 'N/A')}
"""

    # ---------------- TRACEROUTE ---------------- #
    traceroute_data = LAST_TRACEROUTE if LAST_TRACEROUTE else "Not Run"

    # ---------------- MTR ---------------- #
    mtr_data = LAST_MTR if LAST_MTR else "Not Run"

    # ---------------- SIP ---------------- #
    sip_data = LAST_SIP_RESULT

    # ---------------- IP SCANNER ---------------- #
    if LAST_SCAN_RESULTS:
        scan_lines = []
        for device in LAST_SCAN_RESULTS:
            scan_lines.append(
                f"{device['ip']} | {device['host']} | {device['mac']}"
            )
        scan_data = "\n".join(scan_lines)
    else:
        scan_data = "No scan data available"

    # ---------------- FINAL REPORT ---------------- #
    report = f"""
================ FULL NETWORK REPORT ================

Date/Time: {now}

================ SYSTEM INFO ================
{sys_data}

================ SIP ALG ================
{sip_data}

================ TRACEROUTE ================
{traceroute_data}

================ MTR ================
{mtr_data}

================ IP SCANNER ================
{scan_data}

====================================================
"""

    report_output.insert(tk.END, report.strip())


# ---------------- UI ---------------- #
def build_network_report_tab(tabs):
    tab = ttk.Frame(tabs)
    tabs.add(tab, text="Full Network Report")

    main_frame = tk.Frame(tab)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    report_header = tk.Label(
        main_frame,
        text="Full Network Report",
        font=("Segoe UI", 14, "bold")
    )
    report_header.pack(pady=5)

    top_bar = tk.Frame(main_frame)
    top_bar.pack(fill="x", pady=5)

    tk.Button(
        top_bar,
        text="Generate Report",
        command=lambda: generate_report(report_output, report_header),
        width=20,
        height=2
    ).pack(side="left", padx=10)

    report_output = tk.Text(
        main_frame,
        font=("Consolas", 10),
        bg="black",
        fg="white"
    )
    report_output.pack(fill="both", expand=True, pady=10)