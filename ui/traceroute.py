import tkinter as tk
from tkinter import ttk

# ---------------- SHARED DATA ---------------- #
LAST_TRACEROUTE = ""
tracert_running = False
tracert_process = None


# ---------------- NAVIGATION ---------------- #
def start_tracert_from_main(
    trace_entry,
    trace_entry_result,
    trace_main_frame,
    trace_result_frame,
    trace_output
):
    url = trace_entry.get().strip()

    if not url:
        return

    trace_entry_result.delete(0, tk.END)
    trace_entry_result.insert(0, url)

    trace_main_frame.pack_forget()
    trace_result_frame.pack(fill="both", expand=True)

    trace_entry_result.focus()

    trace_output.delete("1.0", tk.END)
    trace_output.insert(tk.END, f"Running traceroute for {url}.prismpbx.com...\n")

    start_tracert(trace_entry_result, trace_output)


def go_back_to_trace_main(trace_main_frame, trace_result_frame, trace_output):
    trace_output.delete("1.0", tk.END)

    trace_result_frame.pack_forget()
    trace_main_frame.pack(fill="both", expand=True)


# ---------------- TRACEROUTE ---------------- #
def start_tracert(trace_entry_result, trace_output):
    import subprocess
    import threading

    global tracert_running, tracert_process, LAST_TRACEROUTE

    tracert_running = True
    output_lines = []

    url = trace_entry_result.get().strip()

    if not url:
        trace_output.insert(tk.END, "Error: No server name provided\n")
        return

    trace_output.insert(tk.END, "\n--- Starting Traceroute ---\n\n")

    target = f"{url}.prismpbx.com"

    def run():
        global tracert_process, LAST_TRACEROUTE

        try:
            tracert_process = subprocess.Popen(
                ["tracert", target],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            while True:
                if not tracert_running:
                    try:
                        tracert_process.terminate()
                    except:
                        pass
                    break

                line = tracert_process.stdout.readline()

                if not line:
                    break

                output_lines.append(line)

                trace_output.insert(tk.END, line)
                trace_output.see(tk.END)

            tracert_process = None

            # Save for Full Network Report
            LAST_TRACEROUTE = "".join(output_lines)

        except Exception as e:
            trace_output.insert(tk.END, f"\nError: {e}\n")

    threading.Thread(target=run, daemon=True).start()


def stop_tracert():
    global tracert_running, tracert_process

    tracert_running = False

    if tracert_process:
        try:
            tracert_process.terminate()
        except:
            pass


# ---------------- SCREENSHOT ---------------- #
def save_tracert_screenshot(trace_output):
    from tkinter import filedialog
    from PIL import Image, ImageDraw, ImageFont

    content = trace_output.get("1.0", tk.END).strip()
    if not content:
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        initialfile="tracert_lightspeed.png",
        filetypes=[("PNG files", "*.png")]
    )

    if not file_path:
        return

    lines = content.split("\n")

    font = ImageFont.load_default()
    max_width = max(font.getlength(line) for line in lines) + 20
    line_height = 18
    height = (len(lines) * line_height) + 20

    img = Image.new("RGB", (int(max_width), height), "black")
    draw = ImageDraw.Draw(img)

    y = 10
    for line in lines:
        draw.text((10, y), line, fill="white", font=font)
        y += line_height

    img.save(file_path)


# ---------------- UI ---------------- #
def build_traceroute_tab(tabs):
    tab = ttk.Frame(tabs)
    tabs.add(tab, text="Traceroute")

    trace_main_frame = tk.Frame(tab)
    trace_main_frame.pack(fill="both", expand=True)

    trace_result_frame = tk.Frame(tab)

    # --- HEADER --- #
    tk.Label(
        trace_main_frame,
        text="Traceroute Tool",
        font=("Segoe UI", 18, "bold")
    ).pack(pady=10)

    # --- INSTRUCTIONS --- #
    instructions = (
        "1. Input customer server URL in the following format, XXXXX.prismpbx.com.\n"
        "2. Select Run.\n"
        "3. Click Start Tracert to begin."
    )

    tk.Label(
        trace_main_frame,
        text=instructions,
        justify="left",
        font=("Segoe UI", 10)
    ).pack(anchor="w", padx=20, pady=10)

    # --- INPUT --- #
    entry_frame = tk.Frame(trace_main_frame)
    entry_frame.pack(pady=10)

    trace_entry = tk.Entry(entry_frame, width=30, font=("Segoe UI", 12))
    trace_entry.pack(side="left")

    tk.Label(entry_frame, text=".prismpbx.com").pack(side="left")

    # --- RUN BUTTON --- #
    tk.Button(
        trace_main_frame,
        text="Run",
        command=lambda: start_tracert_from_main(
            trace_entry,
            trace_entry_result,
            trace_main_frame,
            trace_result_frame,
            trace_output
        ),
        width=20,
        height=2
    ).pack(pady=5)

    # --- RESULT SCREEN --- #
    top_bar = tk.Frame(trace_result_frame)
    top_bar.pack(fill="x", pady=10)

    tk.Button(
        top_bar,
        text="Back",
        command=lambda: go_back_to_trace_main(
            trace_main_frame,
            trace_result_frame,
            trace_output
        )
    ).pack(side="left")

    tk.Button(
        top_bar,
        text="Start Tracert",
        command=lambda: start_tracert(trace_entry_result, trace_output)
    ).pack(side="left")

    tk.Button(
        top_bar,
        text="Stop Tracert",
        command=stop_tracert
    ).pack(side="left")

    trace_entry_result = tk.Entry(top_bar, width=30)
    trace_entry_result.pack(side="left")

    tk.Button(
        top_bar,
        text="Screenshot",
        command=lambda: save_tracert_screenshot(trace_output)
    ).pack(side="left")

    trace_output = tk.Text(
        trace_result_frame,
        bg="black",
        fg="white"
    )
    trace_output.pack(fill="both", expand=True)

    trace_entry.bind(
        "<Return>",
        lambda e: start_tracert_from_main(
            trace_entry,
            trace_entry_result,
            trace_main_frame,
            trace_result_frame,
            trace_output
        )
    )