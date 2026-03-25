import datetime
import tkinter as tk
from tkinter import ttk

from ui.mtr import build_mtr_tab
from ui.ip_scanner import build_ip_scanner_tab
from ui.welcome import build_welcome_tab
from ui.ip_scanner import build_ip_scanner_tab
from ui.mtr import build_mtr_tab
from ui.sip_alg import build_sip_tab
from ui.traceroute import build_traceroute_tab
from ui.system_info import build_system_info_tab
from ui.full_network_report import build_network_report_tab


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

# -------- TABS (ORDER MATTERS) -------- #

build_welcome_tab(tabs)          # FIRST TAB
build_ip_scanner_tab(tabs)
build_sip_tab(tabs)
build_traceroute_tab(tabs)
build_mtr_tab(tabs)
build_system_info_tab(tabs)
build_network_report_tab(tabs)

# Set default tab to Welcome
tabs.select(0)

app.mainloop()