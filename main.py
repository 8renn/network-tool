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
from ui.mtr import build_mtr_tab
from ui.ip_scanner import build_ip_scanner_tab


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
        ip, gateway = get_local_network_info()
        base = ".".join(ip.split(".")[:3])
        subnet_entry.delete(0, tk.END)
        subnet_entry.insert(0, f"{base}.1-254")

    elif mode == "Custom":
        subnet_entry.delete(0, tk.END)

    else:
        base = mode.replace(".x", "")
        subnet_entry.delete(0, tk.END)
        subnet_entry.insert(0, f"{base}.1-254")

# ---------------- NETWORK SCAN ---------------- #

# ---------------- SIP ALG ---------------- #

def sip_alg():
    result = "Checked ports 5060 / 5061 (basic test)"
    sip_var.set(result)
    log("SIP ALG", result)

# ---------------- TRACEROUTE ---------------- #

def start_mtr_from_main():
    url = mtr_entry.get().strip()

    if not url:
        return

    mtr_output.delete("1.0", tk.END)

    mtr_main_frame.pack_forget()
    mtr_result_frame.pack(fill="both", expand=True)

    start_mtr()

def go_back_to_mtr_main():
    global mtr_running
    mtr_running = False

    mtr_output.delete("1.0", tk.END)

    mtr_result_frame.pack_forget()
    mtr_main_frame.pack(fill="both", expand=True)

def start_mtr():
    global mtr_running, mtr_process

    mtr_running = True
    mtr_output.delete("1.0", tk.END)

    url = mtr_entry.get().strip()
    if not url:
        return

    target = f"{url}.prismpbx.com"

    def run():
        global mtr_process

        try:
            mtr_process = subprocess.Popen(
                ["tracert", target],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in mtr_process.stdout:
                if not mtr_running:
                    try:
                        mtr_process.terminate()
                    except:
                        pass
                    break

                mtr_output.insert(tk.END, line)
                mtr_output.see(tk.END)

            mtr_process = None

        except Exception as e:
            mtr_output.insert(tk.END, f"\nError: {e}\n")

    threading.Thread(target=run, daemon=True).start()

mtr_running = False
mtr_process = None

def stop_mtr():
    global mtr_running, mtr_process

    mtr_running = False

    if mtr_process:
        try:
            mtr_process.terminate()
        except:
            pass

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

# ---------------- SYSTEM INFO ---------------- #

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

# --- IP Scanner ---
build_ip_scanner_tab(tabs)

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

# --- SIP ALG ---
from ui.sip_alg import build_sip_tab
build_sip_tab(tabs)

# --- Traceroute ---
from ui.traceroute import build_traceroute_tab
build_traceroute_tab(tabs)

# --- MTR --- #
build_mtr_tab(tabs)

# --- System ---
from ui.system_info import build_system_info_tab
build_system_info_tab(tabs)

# --- Network Report ---
from ui.full_network_report import build_network_report_tab
build_network_report_tab(tabs)

app.mainloop()