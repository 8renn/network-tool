import datetime
import threading
import tkinter as tk
from tkinter import ttk, filedialog
import socket
import subprocess
import requests
import speedtest
from getmac import get_mac_address
import concurrent.futures
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont
from PIL import ImageGrab
tracert_running = False
tracert_process = None

stop_scan = False

# ---------------- LOGGING ---------------- #

def log(section, content):
    with open("network_log.txt", "a") as f:
        f.write(f"\n===== {section} =====\n")
        f.write(f"{datetime.datetime.now()}\n")
        f.write(content + "\n")

# ---------------- UTIL ---------------- #

def format_mac(mac):
    if not mac:
        return "Unknown"
    mac = mac.replace("-", ":").upper()
    parts = mac.split(":")
    if len(parts) == 6:
        return ":".join(p.zfill(2) for p in parts)
    return mac

def get_local_network_info():
    import socket
    import subprocess

    # Get local IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()

    # Get default gateway
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
    try:
        ip_data = requests.get("https://ipinfo.io/json").json()
        public_ip = ip_data.get("ip", "Unknown")
        isp = ip_data.get("org", "Unknown")
    except:
        public_ip = "Error"
        isp = "Error"

    return public_ip, isp

def get_public_info():
    try:
        ip_data = requests.get("https://ipinfo.io/json").json()
        public_ip = ip_data.get("ip", "Unknown")
        isp = ip_data.get("org", "Unknown")
    except:
        public_ip = "Error"
        isp = "Error"

    return public_ip, isp

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

def update_subnet_field(event=None):
    mode = subnet_mode.get()

    if mode == "Auto":
        subnet_entry.delete(0, tk.END)
        subnet_entry.insert(0, get_local_network_info()[1])

    elif mode == "Custom":
        subnet_entry.delete(0, tk.END)

    else:
        subnet_entry.delete(0, tk.END)
        subnet_entry.insert(0, mode.replace(".x", ".0/24"))

def sip_alg_check():
    import socket

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

        except socket.timeout:
            sip_result_label.config(
                text="SIP ALG Not Detected",
                bg="green"
            )

    except Exception:
        sip_result_label.config(
            text="Server Error: Unable to Detect SIP ALG",
            bg="orange"
        )

    finally:
        s.close()

# ---------------- NETWORK SCAN ---------------- #

def network_scan(subnet, tree, progress):
    global stop_scan
    stop_scan = False

    tree.delete(*tree.get_children())
    progress["value"] = 0

    arp = get_arp_devices()
    active = []

    def ping(ip):
        if stop_scan:
            return None
        try:
            r = subprocess.run(["ping","-n","1","-w","200",ip],
                               capture_output=True,text=True)
            if "TTL=" in r.stdout:
                return ip
        except:
            return None

    # Scan phase
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as ex:
        futures = [ex.submit(ping, f"{subnet}.{i}") for i in range(1,255)]
        done = 0
        for f in concurrent.futures.as_completed(futures):
            if stop_scan:
                return
            done += 1
            progress["value"] = (done/254)*50
            app.update_idletasks()
            ip = f.result()
            if ip:
                active.append(ip)

    # Merge ARP
    for ip in arp:
        if ip not in active:
            active.append(ip)

    # Resolve phase
    total = len(active)
    done = 0

    for ip in active:
        if stop_scan:
            return
        try:
            host = socket.getfqdn(ip)
        except:
            host = "Unknown"

        try:
            mac = format_mac(arp.get(ip) or get_mac_address(ip=ip))
        except:
            mac = "Unknown"

        tree.insert("", "end", values=(ip, host, mac))

        done += 1
        progress["value"] = 50 + (done/total)*50
        app.update_idletasks()

    log("SCAN", f"{len(active)} devices")
    app.after(0, finish_scan_ui)

def finish_scan_ui():
    progress.stop()

    # Get exact position of progress bar BEFORE hiding it
    progress.update_idletasks()
    x = progress.winfo_x()
    y = progress.winfo_y()
    width = progress.winfo_width()
    height = progress.winfo_height()

    # Hide progress bar
    progress.pack_forget()

    # Place COMPLETED text EXACTLY where bar was
    scan_complete_label.config(
        text="COMPLETED",
        bg="black",
        fg="lime"
    )

    scan_complete_label.place(
        x=x + (width // 2),
        y=y + (height // 2),
        anchor="center"
    )

def start_scan():
    global stop_scan
    stop_scan = False

    scan_complete_label.place_forget()
    progress.pack(fill="x", padx=10, pady=5)

    progress.configure(style="Green.Horizontal.TProgressbar")
    progress["value"] = 0
    app.update_idletasks()

    subnet = subnet_entry.get().replace(".0/24", "")
    threading.Thread(target=network_scan,
                     args=(subnet, tree, progress),
                     daemon=True).start()

def stop_scan_func():
    global stop_scan
    stop_scan = True

    progress["value"] = 100
    progress.configure(style="Red.Horizontal.TProgressbar")

    app.update_idletasks()

def export_devices():
    file = filedialog.asksaveasfilename(defaultextension=".txt")
    if not file:
        return
    with open(file,"w") as f:
        for row in tree.get_children():
            f.write(" | ".join(map(str,tree.item(row)["values"]))+"\n")

# ---------------- SIP ALG ---------------- #

def sip_alg():
    result = "Checked ports 5060 / 5061 (basic test)"
    sip_var.set(result)
    log("SIP ALG", result)

# ---------------- TRACEROUTE ---------------- #

def start_tracert_from_main():
    url = trace_entry.get().strip()

    if not url:
        return

    # Put value into result screen input
    trace_entry_result.delete(0, tk.END)
    trace_entry_result.insert(0, url)

    # Switch UI screens
    trace_main_frame.pack_forget()
    trace_result_frame.pack(fill="both", expand=True)

    # Focus input
    trace_entry_result.focus()

    # Start tracert
    start_tracert() 

def start_tracert():
    global tracert_running, tracert_process

    print("Start button pressed")

    # Stop previous process
    tracert_running = False
    if tracert_process:
        try:
            tracert_process.terminate()
        except:
            pass

    tracert_running = True
    trace_output.delete("1.0", tk.END)

    url = trace_entry_result.get().strip()

    if not url:
        trace_output.insert(tk.END, "Error: No server name provided\n")
        return

    target = f"{url}.prismpbx.com"

    def run():
        global tracert_process

        try:
            tracert_process = subprocess.Popen(
                ["tracert", target],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in tracert_process.stdout:
                if not tracert_running:
                    try:
                        tracert_process.terminate()
                    except:
                        pass
                    break

                trace_output.insert(tk.END, line)
                trace_output.see(tk.END)

            tracert_process = None

        except Exception as e:
            trace_output.insert(tk.END, f"\nError: {e}\n")

    threading.Thread(target=run, daemon=True).start()

def generate_report():
    report_output.delete("1.0", tk.END)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report_header.config(text=f"Network Report - {now}")

    report = f"""
================ NETWORK REPORT ================

Date/Time: {now}

---------- SYSTEM INFO ----------
{sys_output.get("1.0", tk.END)}

---------- TRACEROUTE ----------
{trace_output.get("1.0", tk.END)}

---------- SIP ALG ----------
{sip_result_label.cget("text")}

---------- NETWORK SCAN ----------
(Scan results will be added next)

================================================
"""

    report_output.insert(tk.END, report)

def stop_tracert():
    global tracert_running, tracert_process

    tracert_running = False

    if tracert_process:
        try:
            tracert_process.terminate()
        except:
            pass

# ---------------- SYSTEM INFO ---------------- #

def run_speed_tests():
    results = {}

    # ---------------- OOKLA SPEEDTEST ---------------- #
    try:
        import speedtest

        st = speedtest.Speedtest()
        st.get_best_server()

        download = round(st.download() / 1_000_000, 2)  # Mbps
        upload = round(st.upload() / 1_000_000, 2)      # Mbps
        ping = round(st.results.ping, 2)

        results["ookla"] = f"{download} Mbps ↓ / {upload} Mbps ↑ / {ping} ms ping"

    except Exception as e:
        results["ookla"] = f"Error"

    # ---------------- CLOUDFLARE TEST ---------------- #
    try:
        import time
        import requests

        # DOWNLOAD TEST (10MB)
        start = time.time()
        requests.get("https://speed.cloudflare.com/__down?bytes=10000000")
        download_time = time.time() - start
        download_speed = round((10 / download_time) * 8, 2)  # Mbps

        # UPLOAD TEST (1MB)
        start = time.time()
        requests.post("https://speed.cloudflare.com/__up", data="0" * 1000000)
        upload_time = time.time() - start
        upload_speed = round((1 / upload_time) * 8, 2)  # Mbps

        # PING TEST
        start = time.time()
        requests.get("https://1.1.1.1")
        ping = round((time.time() - start) * 1000, 2)

        results["cloudflare"] = f"{download_speed} Mbps ↓ / {upload_speed} Mbps ↑ / {ping} ms ping"

    except Exception as e:
        results["cloudflare"] = "Error"

    return results

def system_info():
    sys_output.delete("1.0", tk.END)
    sys_output.insert(tk.END, "Gathering system info...\n")
    sys_progress.start()

    def run():
        # Local
        ip, gateway = get_local_network_info()

        # Public
        public_ip, isp = get_public_info()

        # Speed
        speeds = run_speed_tests()

        text = f"""
Local Network Info:
Default Gateway: {gateway}
IPv4 Address: {ip}

Public Network Info:
Public IP Address: {public_ip}
Internet Service Provider: {isp}

Internet Speed Test:
Cloudflare: {speeds['cloudflare']}
Ookla: {speeds['ookla']}
"""

        def finish():
            sys_progress.stop()
            update_output(text)

        sys_output.after(0, finish)

    threading.Thread(target=run, daemon=True).start()

def update_output(text):
    sys_output.delete("1.0", tk.END)
    sys_output.insert(tk.END, text.strip())

# ---------------- SPEED TEST ---------------- #

def speed_test():
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        d = st.download()/1_000_000
        u = st.upload()/1_000_000
        p = st.results.ping
        result = f"Download: {d:.2f} Mbps\nUpload: {u:.2f} Mbps\nPing: {p:.2f} ms"
    except Exception as e:
        result = str(e)
    speed_var.set(result)
    log("SPEED", result)

# ---------------- UI ---------------- #

app = tk.Tk()
style = ttk.Style()
style.theme_use("default")

style.configure(
    "Green.Horizontal.TProgressbar",
    background="green",
    troughcolor="white",
    thickness=12
)

style.configure(
    "Red.Horizontal.TProgressbar",
    background="red",
    troughcolor="white",
    thickness=12
)
app.title("Network Tool")
app.geometry("1000x600")

tabs = ttk.Notebook(app)
tabs.pack(fill="both", expand=True)

# --- Network Tab ---
tab1 = ttk.Frame(tabs)
tabs.add(tab1, text="IP Scanner")

# ---------------- TOP CONTROL BAR ---------------- #

top = tk.Frame(tab1)
top.pack(fill="x", padx=10, pady=5)

# LEFT SIDE
left = tk.Frame(top)
left.pack(side="left")

tk.Button(left, text="Start Scan", width=12,
          command=start_scan).pack(side="left", padx=3)

tk.Button(left, text="Stop Scan", width=12,
          command=stop_scan_func).pack(side="left", padx=3)

subnet_mode = tk.StringVar(value="Auto")

dropdown = ttk.Combobox(left,
                        textvariable=subnet_mode,
                        width=15,
                        state="readonly")

dropdown["values"] = ["Auto", "Custom", "192.168.1.x", "192.168.0.x", "10.0.0.x"]
dropdown.pack(side="left", padx=3)
dropdown.bind("<<ComboboxSelected>>", update_subnet_field)

subnet_entry = tk.Entry(left, width=20)
subnet_entry.pack(side="left", padx=3)
update_subnet_field()

# RIGHT SIDE
right = tk.Frame(top)
right.pack(side="right")

tk.Button(right, text="Export", width=12,
          command=lambda: export_devices(tree)).pack(side="right", padx=5)

# ---------------- PROGRESS BAR ---------------- #

progress = ttk.Progressbar(
    tab1,
    orient="horizontal",
    mode="indeterminate",
    length=600,
    style="Green.Horizontal.TProgressbar"
)
progress.pack(fill="x", padx=10, pady=5)

scan_complete_label = tk.Label(
    tab1,
    text="",
    font=("Segoe UI", 14, "bold"),
    fg="lime",
    bg="black"
)

# ---------------- DEVICE TABLE ---------------- #

tree = ttk.Treeview(
    tab1,
    columns=("IP", "Host", "MAC"),
    show="headings"
)

tree.heading("IP", text="IP Address")
tree.heading("Host", text="Hostname")
tree.heading("MAC", text="MAC Address")

tree.column("IP", width=200)
tree.column("Host", width=300)
tree.column("MAC", width=200)

tree.pack(fill="both", expand=True, padx=10, pady=5)

# --- HOVER HIGHLIGHT --- #

def on_row_hover(event):
    row_id = tree.identify_row(event.y)

    # Remove highlight from all rows
    for item in tree.get_children():
        tree.item(item, tags=())

    # Highlight current row
    if row_id:
        tree.item(row_id, tags=("hover",))

# Configure highlight color
tree.tag_configure("hover", background="#d3d3d3")

# Bind mouse movement
tree.bind("<Motion>", on_row_hover)

# --- RIGHT CLICK MENU --- #

menu = tk.Menu(app, tearoff=0)

def copy_ip():
    selected = tree.selection()
    if selected:
        ip = tree.item(selected[0])["values"][0]
        app.clipboard_clear()
        app.clipboard_append(ip)

def copy_mac():
    selected = tree.selection()
    if selected:
        mac = tree.item(selected[0])["values"][2]
        app.clipboard_clear()
        app.clipboard_append(mac)

def open_http():
    import webbrowser
    selected = tree.selection()
    if selected:
        ip = tree.item(selected[0])["values"][0]
        webbrowser.open(f"http://{ip}")

def open_https():
    import webbrowser
    selected = tree.selection()
    if selected:
        ip = tree.item(selected[0])["values"][0]
        webbrowser.open(f"https://{ip}")

menu.add_command(label="Copy IP", command=copy_ip)
menu.add_command(label="Copy MAC", command=copy_mac)
menu.add_separator()
menu.add_command(label="Open HTTP", command=open_http)
menu.add_command(label="Open HTTPS", command=open_https)

def save_tracert_screenshot():
    from tkinter import filedialog
    from PIL import Image, ImageDraw, ImageFont

    # Get ONLY the tracert text
    content = trace_output.get("1.0", tk.END).strip()

    if not content:
        return

    # Ask where to save
    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        initialfile="tracert_lightspeed.png",
        filetypes=[("PNG files", "*.png")]
    )

    if not file_path:
        return

    # Split into lines
    lines = content.split("\n")

    # Font settings
    font = ImageFont.load_default()

    # Calculate image size
    max_width = max(font.getlength(line) for line in lines) + 20
    line_height = 18
    height = (len(lines) * line_height) + 20

    # Create black image
    img = Image.new("RGB", (int(max_width), height), "black")
    draw = ImageDraw.Draw(img)

    # Draw text
    y = 10
    for line in lines:
        draw.text((10, y), line, fill="white", font=font)
        y += line_height

    # Save image
    img.save(file_path)

def go_back_to_trace_main():
    global tracert_running
    tracert_running = False

    trace_output.delete("1.0", tk.END)  # clear results

    trace_result_frame.pack_forget()
    trace_main_frame.pack(fill="both", expand=True)

# --- SIP ---
tab2 = ttk.Frame(tabs)
tabs.add(tab2, text="SIP ALG")

# --- SIP HEADER --- #
tk.Label(
    tab2,
    text="SIP Detector",
    font=("Segoe UI", 18, "bold")
).pack(pady=10)

# --- RUN BUTTON (BIGGER) --- #
tk.Button(
    tab2,
    text="Run Test",
    command=sip_alg_check,
    width=20,
    height=2
).pack(pady=10)

# --- CENTER FRAME (FOR RESULT BANNER) --- #
center_frame = tk.Frame(tab2)
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

sip_result_label.pack()

# --- Traceroute ---
tab3 = ttk.Frame(tabs)
tabs.add(tab3, text="Traceroute")

trace_main_frame = tk.Frame(tab3)
trace_main_frame.pack(fill="both", expand=True)

trace_result_frame = tk.Frame(tab3)

trace_var = tk.StringVar()

# --- HEADER --- #
tk.Label(
    trace_main_frame,
    text="Traceroute Tool",
    font=("Segoe UI", 18, "bold")
).pack(pady=10)

# --- INSTRUCTIONS --- #
instructions = (
    "1. Input customer server URL in the following format, XXXXX.prismpbx.com.\n"
    "2. Select \"Run\" Once Server URL is input.\n"
    "3. Wait until traceroute is completed and click \"Screen Shot\" button to get a copy of results."
)

tk.Label(
    trace_main_frame,
    text=instructions,
    justify="left",
    font=("Segoe UI", 10)
).pack(anchor="w", padx=20, pady=10)

# --- CENTER FRAME --- #
center_frame_trace = tk.Frame(trace_main_frame)
center_frame_trace.pack(expand=True)

# --- INPUT FIELD (BIGGER) --- #
entry_frame = tk.Frame(center_frame_trace)
entry_frame.pack(pady=10)

trace_entry = tk.Entry(
    entry_frame,
    width=30,
    font=("Segoe UI", 12)
)
trace_entry.pack(side="left")

trace_entry.bind("<Return>", lambda event: start_tracert_from_main())

tk.Label(
    entry_frame,
    text=".prismpbx.com",
    font=("Segoe UI", 12)
).pack(side="left")

# --- RUN BUTTON (BIGGER) --- #
tk.Button(
    center_frame_trace,
    text="Run",
    command=lambda: start_tracert_from_main(),
    width=20,
    height=2
).pack(pady=5)

tk.Label(
    trace_main_frame,
    textvariable=trace_var,
    justify="left",
    anchor="w",
    font=("Consolas", 10)
).pack(fill="both", expand=True, padx=10, pady=10)

# --- RESULT TOP BAR --- #
top_bar = tk.Frame(trace_result_frame)
top_bar.pack(fill="x", pady=10)

tk.Button(
    top_bar,
    text="Back",
    width=10,
    command=go_back_to_trace_main
).pack(side="left", padx=5)

tk.Button(top_bar, text="Start Tracert", width=15,
          command=start_tracert).pack(side="left", padx=5)

tk.Button(top_bar, text="Stop Tracert", width=15,
          command=stop_tracert).pack(side="left", padx=5)

result_entry_frame = tk.Frame(top_bar)
result_entry_frame.pack(side="left", padx=10)

trace_entry_result = tk.Entry(
    result_entry_frame,
    width=30,
    font=("Segoe UI", 10)
)
trace_entry_result.pack(side="left")

tk.Label(
    result_entry_frame,
    text=".prismpbx.com",
    font=("Segoe UI", 10)
).pack(side="left")

trace_entry_result.bind("<Return>", lambda event: start_tracert())

tk.Button(
    top_bar,
    text="Screenshot",
    width=15,
    command=save_tracert_screenshot
).pack(side="left", padx=10)


# --- OUTPUT AREA --- #
trace_output = tk.Text(
    trace_result_frame,
    font=("Consolas", 10),
    bg="black",
    fg="white"
)
trace_output.pack(fill="both", expand=True, padx=10, pady=10)

# --- System ---
tab4 = ttk.Frame(tabs)
tabs.add(tab4, text="System Info")

center_frame_sys = tk.Frame(tab4)
center_frame_sys.pack(expand=True)

sys_progress = ttk.Progressbar(
    center_frame_sys,
    orient="horizontal",
    length=300,
    mode="indeterminate"
)
sys_progress.pack(pady=5)

sys_output = tk.Text(
    center_frame_sys,
    width=80,
    height=20,
    font=("Consolas", 11)
)
sys_output.pack()

tk.Button(
    center_frame_sys,
    text="Get Info",
    command=system_info,
    width=20,
    height=2
).pack(pady=10)

# --- Network Report ---
tab5 = ttk.Frame(tabs)
tabs.add(tab5, text="Network Report")

import datetime

report_header = tk.Label(
    tab5,
    text="",
    font=("Segoe UI", 14, "bold")
)
report_header.pack(pady=10)

top_report = tk.Frame(tab5)
top_report.pack(fill="x", pady=5)

tk.Button(
    top_report,
    text="Generate Report",
    command=generate_report,
    width=20,
    height=2
).pack(side="left", padx=10)

report_output = tk.Text(
    tab5,
    width=100,
    height=30,
    font=("Consolas", 10)
)
report_output.pack(padx=10, pady=10, fill="both", expand=True)

app.mainloop()