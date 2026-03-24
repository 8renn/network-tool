import tkinter as tk
from tkinter import ttk, filedialog
import threading
import subprocess
import socket
import concurrent.futures
from getmac import get_mac_address

# ---------------- SHARED DATA ---------------- #
LAST_SCAN_RESULTS = []

def debug_log(message):
    with open("scanner_debug.log", "a", encoding="utf-8") as f:
        f.write(f"{message}\n")

def get_default_gateway():
    try:
        output = subprocess.check_output("ipconfig", text=True)
        for line in output.splitlines():
            if "Default Gateway" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    gw = parts[1].strip()
                    if gw:
                        return gw
    except:
        pass
    return None

def get_arp_devices():
    devices = {}
    try:
        output = subprocess.check_output("arp -a", text=True)
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                devices[parts[0]] = parts[1]
    except:
        pass
    return devices

def format_mac(mac):
    if not mac:
        return "Unknown"

    mac = mac.replace("-", ":").replace(".", ":").upper()

    # Ensure proper format length
    parts = mac.split(":")
    if len(parts) == 6:
        return ":".join(part.zfill(2) for part in parts)

    return mac

def build_ip_scanner_tab(tabs):

    stop_flag = {"stop": False}

    tab1 = ttk.Frame(tabs)
    tabs.add(tab1, text="IP Scanner")

    # ---------------- STYLE ---------------- #
    style = ttk.Style()
    style.theme_use("default")

    style.configure(
        "Modern.Horizontal.TProgressbar",
        troughcolor="#2b2b2b",
        bordercolor="#2b2b2b",
        background="#4CAF50",
        lightcolor="#4CAF50",
        darkcolor="#4CAF50",
        thickness=12
    )

    # ---------------- TOP BAR ---------------- #
    top_frame = tk.Frame(tab1)
    top_frame.pack(fill="x", padx=10, pady=5)

    left_frame = tk.Frame(top_frame)
    left_frame.pack(side="left")

    center_frame = tk.Frame(top_frame)
    center_frame.pack(side="left", padx=20)

    scan_mode = tk.StringVar(value="Auto Detect")

    dropdown = ttk.Combobox(
    center_frame,
    values=[
            "Auto Detect",
            "Custom Ranges",
            "All Ranges",
            "192.168.1.x",
            "192.168.0.x",
            "10.0.0.x",
            "172.16.0.x"
        ],
        width=18,
        state="readonly"
    )
    dropdown.pack(side="left", padx=5)
    dropdown.current(0)
    scan_mode.set("Auto Detect")

    subnet_entry = tk.Entry(center_frame, width=35)
    subnet_entry.pack(side="left")

    def update_subnet_entry(event=None):
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            base = ".".join(local_ip.split(".")[:3])
        except:
            base = "192.168.1"

        subnet_entry.delete(0, tk.END)
        subnet_entry.insert(0, f"{base}.1-254")
        subnet_entry.config(fg="black")

    dropdown.bind("<<ComboboxSelected>>", update_subnet_entry)
    update_subnet_entry()

    right_frame = tk.Frame(top_frame)
    right_frame.pack(side="right")

    # ---------------- TABLE ---------------- #
    tree = ttk.Treeview(tab1, columns=("IP", "Host", "MAC"), show="headings")
    tree.heading("IP", text="IP Address")
    tree.heading("Host", text="Hostname")
    tree.heading("MAC", text="MAC Address")
    tree.pack(fill="both", expand=True)

    # ---------------- PROGRESS ---------------- #
    progress_frame = tk.Frame(tab1)
    progress_frame.pack(fill="x", pady=(2, 8))

    progress = ttk.Progressbar(
        progress_frame,
        orient="horizontal",
        mode="determinate",
        style="Modern.Horizontal.TProgressbar"
    )
    progress.pack(fill="x", padx=10)

    progress_label = tk.Label(progress_frame, text="Ready", font=("Segoe UI", 9))
    progress_label.pack()

    # ---------------- FUNCTIONS ---------------- #

    def network_scan():
        global LAST_SCAN_RESULTS

        stop_flag["stop"] = False
        LAST_SCAN_RESULTS = []

        progress["value"] = 0
        progress_label.config(text="Scanning...", fg="black")

        tree.delete(*tree.get_children())

        # -------- NETWORK BASE -------- #
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except:
            local_ip = "192.168.1.1"

        gateway = get_default_gateway()
        base = ".".join((gateway or local_ip).split(".")[:3])

        debug_log(f"Scanning subnet: {base}.x")

        # -------- CLEAR ARP CACHE -------- #
        subprocess.run("arp -d *", shell=True, stdout=subprocess.DEVNULL)

        ip_range = [f"{base}.{i}" for i in range(1, 255)]
        total = len(ip_range)

        active = []
        arp_cache = {}

        # -------- PING SWEEP -------- #
        def ping(ip):
            if stop_flag["stop"]:
                return None
            try:
                r = subprocess.run(
                    ["ping", "-n", "1", "-w", "50", "-l", "1", ip],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                if r.returncode == 0:
                    return ip
            except:
                pass
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=200) as ex:
            futures = [ex.submit(ping, ip) for ip in ip_range]

            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                if stop_flag["stop"]:
                    return

                ip = f.result()
                if ip:
                    active.append(ip)

                progress["value"] = (i / total) * 50
                tab1.update_idletasks()

        # -------- ARP MERGE -------- #
        arp_cache = get_arp_devices()

        for ip in arp_cache:
            if ip not in active:
                active.append(ip)

        debug_log(f"Devices after ARP merge: {len(active)}")

        # -------- RESOLVE DEVICES -------- #
        for i, ip in enumerate(active):

            if stop_flag["stop"]:
                return

            try:
                host = "Resolving..."
            except:
                host = "Unknown"

            try:
                raw_mac = arp_cache.get(ip) or get_mac_address(ip=ip)
                mac = format_mac(raw_mac)
            except:
                mac = "Unknown"

            item = tree.insert("", "end", values=(ip, host, mac))

            def resolve_host_async(ip, item):
                try:
                    name = socket.gethostbyaddr(ip)[0]
                except:
                    name = "Unknown"

                # Keep MAC the same, only update hostname
                current = tree.item(item)["values"]
                tree.item(item, values=(current[0], name, current[2]))

            threading.Thread(
                target=resolve_host_async,
                args=(ip, item),
                daemon=True
            ).start()

            LAST_SCAN_RESULTS.append({
                "ip": ip,
                "host": host,
                "mac": mac
            })

            progress["value"] = 50 + (i / len(active)) * 50
            tab1.update_idletasks()

        progress["value"] = 100
        progress_label.config(
            text=f"Completed ({len(LAST_SCAN_RESULTS)} devices)",
            fg="green"
        )

    def start_scan():
        threading.Thread(target=network_scan, daemon=True).start()

    def stop_scan():
        stop_flag["stop"] = True
        progress_label.config(text="Stopped", fg="red")

    def export_devices():
        file = filedialog.asksaveasfilename(defaultextension=".txt")
        if not file:
            return
        with open(file, "w") as f:
            for row in tree.get_children():
                f.write(" | ".join(map(str, tree.item(row)["values"])) + "\n")

    # ---------------- BUTTONS ---------------- #
    tk.Button(left_frame, text="Start Scan", command=start_scan).pack(side="left", padx=5)
    tk.Button(left_frame, text="Stop Scan", command=stop_scan).pack(side="left", padx=5)
    tk.Button(right_frame, text="Export", command=export_devices).pack(side="right", padx=5)