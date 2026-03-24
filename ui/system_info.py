import tkinter as tk
from tkinter import ttk

# ---------------- SHARED DATA ---------------- #
LAST_SYSTEM_INFO = {
    "gateway": "",
    "ip": "",
    "public_ip": "",
    "isp": "",
    "cloudflare": "",
    "ookla": ""
}


# ---------------- SYSTEM INFO LOGIC ---------------- #
def system_info(sys_output, sys_progress, progress_label):
    import threading

    # Reset UI
    sys_output.delete("1.0", tk.END)
    sys_progress["value"] = 0
    progress_label.config(text="Starting...", fg="black")

    def update_progress(value, text):
        def _update():
            sys_progress["value"] = value
            progress_label.config(text=text)
        sys_output.after(0, _update)

    def append_output(text):
        def _append():
            sys_output.insert(tk.END, text + "\n")
            sys_output.see(tk.END)
        sys_output.after(0, _append)

    def run():
        from ui.system_info import (
            get_local_network_info,
            get_public_info,
            run_speed_tests
        )

        # --- STEP 1: LOCAL NETWORK --- #
        update_progress(20, "Getting Local Network Info...")
        ip, gateway = get_local_network_info()

        LAST_SYSTEM_INFO["gateway"] = gateway
        LAST_SYSTEM_INFO["ip"] = ip

        append_output("=== Local Network Info ===")
        append_output(f"Default Gateway: {gateway}")
        append_output(f"IPv4 Address: {ip}\n")

        # --- STEP 2: PUBLIC INFO --- #
        update_progress(50, "Getting Public Network Info...")
        public_ip, isp = get_public_info()

        LAST_SYSTEM_INFO["public_ip"] = public_ip
        LAST_SYSTEM_INFO["isp"] = isp

        append_output("=== Public Network Info ===")
        append_output(f"Public IP Address: {public_ip}")
        append_output(f"Internet Service Provider: {isp}\n")

        # --- STEP 3: SPEED TEST --- #
        update_progress(80, "Running Speed Tests...")
        speeds = run_speed_tests()

        LAST_SYSTEM_INFO["cloudflare"] = speeds["cloudflare"]
        LAST_SYSTEM_INFO["ookla"] = speeds["ookla"]

        append_output("=== Internet Speed Test ===")
        append_output(f"Cloudflare: {speeds['cloudflare']}")
        append_output(f"Ookla: {speeds['ookla']}\n")

        # --- COMPLETE --- #
        def finish():
            sys_progress["value"] = 100
            progress_label.config(text="Completed", fg="green")

        sys_output.after(0, finish)

    threading.Thread(target=run, daemon=True).start()


# ---------------- UI ---------------- #
def build_system_info_tab(tabs):
    tab = ttk.Frame(tabs)
    tabs.add(tab, text="System Info")

    # Main container
    main_frame = tk.Frame(tab)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # --- TOP CONTROL BAR (NEW POSITION) --- #
    top_bar = tk.Frame(main_frame)
    top_bar.pack(fill="x", pady=5)

    tk.Button(
        top_bar,
        text="Get Info",
        command=lambda: system_info(sys_output, sys_progress, progress_label),
        width=20,
        height=2
    ).pack(pady=5)

    # Output box (full size)
    sys_output = tk.Text(
        main_frame,
        font=("Consolas", 11),
        bg="black",
        fg="white"
    )
    sys_output.pack(fill="both", expand=True)

    # --- PROGRESS BAR SECTION --- #
    progress_frame = tk.Frame(main_frame)
    progress_frame.pack(fill="x", pady=5)

    sys_progress = ttk.Progressbar(
        progress_frame,
        orient="horizontal",
        mode="determinate",
        style="Green.Horizontal.TProgressbar"
    )
    sys_progress.pack(fill="x", padx=10)

    progress_label = tk.Label(
        progress_frame,
        text="",
        font=("Segoe UI", 10, "bold")
    )
    progress_label.pack(pady=2)


# ---------------- HELPERS ---------------- #
def get_local_network_info():
    import socket
    import subprocess

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()

    gateway = "Not Found"
    try:
        output = subprocess.check_output("ipconfig", text=True)
        for line in output.splitlines():
            if "Default Gateway" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    gw = parts[1].strip()
                    if gw:
                        gateway = gw
                        break
    except:
        pass

    return ip, gateway


def get_public_info():
    import requests

    try:
        ip_data = requests.get("https://ipinfo.io/json").json()
        public_ip = ip_data.get("ip", "Unknown")
        isp = ip_data.get("org", "Unknown")
    except:
        public_ip = "Error"
        isp = "Error"

    return public_ip, isp


def run_speed_tests():
    results = {}

    # --- OOKLA --- #
    try:
        import speedtest

        st = speedtest.Speedtest()
        st.get_best_server()

        download = round(st.download() / 1_000_000, 2)
        upload = round(st.upload() / 1_000_000, 2)
        ping = round(st.results.ping, 2)

        results["ookla"] = f"{download} Mbps ↓ / {upload} Mbps ↑ / {ping} ms ping"

    except:
        results["ookla"] = "Error"

    # --- CLOUDFLARE --- #
    try:
        import time
        import requests

        start = time.time()
        requests.get("https://speed.cloudflare.com/__down?bytes=10000000")
        download_time = time.time() - start
        download_speed = round((10 / download_time) * 8, 2)

        start = time.time()
        requests.post("https://speed.cloudflare.com/__up", data="0" * 1000000)
        upload_time = time.time() - start
        upload_speed = round((1 / upload_time) * 8, 2)

        start = time.time()
        requests.get("https://1.1.1.1")
        ping = round((time.time() - start) * 1000, 2)

        results["cloudflare"] = f"{download_speed} Mbps ↓ / {upload_speed} Mbps ↑ / {ping} ms ping"

    except:
        results["cloudflare"] = "Error"

    return results