#Freq list scanner for Yeasu Radio via CAT. By Anthony Del Veccio and Dave Doler K3DFD

import tkinter as tk
import requests
import threading
from datetime import datetime
from tkinter import filedialog, ttk, messagebox
import threading
import time
import serial
import csv
import os
import subprocess
from tkinter import PhotoImage

CONFIG_FILE = "freqscanr.ini"
HELP_FILE = "freqscanr.txt"
ICON_ICO = "freqscanr_icon.ico"
ICON_PNG = "freqscanr_icon.png"

radio_name = "Unknown Radio"
com_port = "COM1"
baud_rate = 9600
poll_interval_ms = 500
post_delay_ms = 25
stop_bits = 1

class FreqScanrApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FreqScanR by ErnieTech")
        self.set_icon()

        self.freq_list = []
        self.current_index = 0
        self.scanning = False
        self.paused = False
        self.ser = None
        self.skipped = set()
        self.mode_map = {'LSB': '1', 'USB': '2', 'FM': '4', 'AM': '5'}

        self.setup_gui()
        self.load_ini()

        self.root.bind("<space>", self.toggle_pause)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

    def set_icon(self):
        try:
            self.root.iconbitmap(ICON_ICO)
        except:
            pass
        try:
            img = PhotoImage(file=ICON_PNG)
            self.root.iconphoto(True, img)
        except:
            pass

    def load_ini(self):
        global radio_name, com_port, baud_rate, poll_interval_ms, post_delay_ms, stop_bits
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    path = f.readline().strip()
                if os.path.exists(path):
                    with open(path, 'r') as rf:
                        lines = [l.strip() for l in rf if l.strip() and not l.strip().startswith("#")]
                    radio_name = lines[0]
                    config_map = dict()
                    for line in lines[1:]:
                        if "=" in line:
                            k, v = line.split("=", 1)
                            config_map[k.strip().upper()] = v.strip()
                    com_port = config_map.get("PORT", "COM1")
                    baud_rate = int(config_map.get("BAUD", 9600))
                    poll_interval_ms = int(config_map.get("POLLINTV", 500))
                    post_delay_ms = int(config_map.get("POSTDEL", 25))
                    stop_bits = int(config_map.get("STOPBITS", 1))
                    self.radio_label.config(text=f"Radio: {radio_name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load radio .cfg file:\n{e}")

    def setup_gui(self):
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        #filemenu.add_command(label="Load Radio Profile (.cfg)", command=self.browse_radio_cfg)
        filemenu.add_command(label="Quit", command=self.quit_app)
        menubar.add_cascade(label="File", menu=filemenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Open Help", command=self.open_help)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.root.config(menu=menubar)
        self.update_kp_index()

        top = tk.Frame(self.root)
        top.pack(pady=5)

        tk.Button(top, text="Load Radio Profile", command=self.browse_radio_cfg).pack(side=tk.LEFT, padx=5)
        tk.Button(top, text="Open CSV", command=self.load_csv).pack(side=tk.LEFT, padx=5)
        self.start_btn = tk.Button(top, text="Start", command=self.start_scan, state='disabled')
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = tk.Button(top, text="Stop", command=self.stop_scan, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        tk.Label(top, text="Delay:").pack(side=tk.LEFT, padx=(10, 0))
        self.delay_cb = ttk.Combobox(top, width=3, values=['1', '2', '3', '4', '5'])
        self.delay_cb.current(0)
        self.delay_cb.pack(side=tk.LEFT, padx=5)

        #
        # Treeview with vertical scrollbar
        tree_frame = tk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        self.tree = ttk.Treeview(tree_frame, columns=("Freq", "Desc", "Mode"),
                                 show="headings", height=20, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree.heading("Freq", text="Freq (MHz)")
        self.tree.heading("Desc", text="Description")
        self.tree.heading("Mode", text="Mode")
        self.tree.tag_configure('skipped', foreground='darkgray')
        self.tree.bind('<Double-1>', self.on_row_toggle)


        self.radio_label = tk.Label(self.root, text=f"Radio: {radio_name}", anchor='w')
        self.radio_label.pack(fill=tk.X, padx=10)
        self.kp_label = tk.Label(self.root, text="Kp: --", font=("Segoe UI", 9, "bold"), fg="black")
        self.kp_label.pack(anchor="w", padx=10, pady=(0, 5))
        self.utc_label = tk.Label(self.root, font=("Segoe UI", 9, "bold"), fg="gray30", text="UTC: 00:00:00", anchor='w')
        self.utc_label.pack(anchor='w', padx=10, pady=(0, 5))
        self.update_utc_time()
        self.status = tk.Label(self.root, font=("Segoe UI", 9, "bold"), fg="green", text="Load a CSV to begin.", anchor='w')
        self.status.pack(fill=tk.X, padx=10, pady=0)
        self.smeter_label = tk.Label(self.root, text="", anchor="w")
        self.smeter_label.pack(fill=tk.X, padx=10, pady=5)

    def browse_radio_cfg(self):
        path = filedialog.askopenfilename(filetypes=[("CFG files", "*.cfg")])
        if path:
            with open(CONFIG_FILE, 'w') as f:
                f.write(path)
            self.load_ini()

    def open_help(self):
        if os.path.exists(HELP_FILE):
            try:
                subprocess.Popen(["notepad.exe", HELP_FILE])
            except Exception as e:
                messagebox.showerror("Help Error", f"Could not open help file:\n{e}")
        else:
            messagebox.showwarning("Help", "Help file not found.")

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            with open(path, newline='') as f:
                reader = csv.reader(f)
                self.freq_list = []
                for row in reader:
                    if not row:
                        continue
                    hz = int(row[0])
                    mhz_str = f"{hz/1_000_000:.6f}"
                    desc = row[1].strip() if len(row) > 1 else ""
                    mode = row[2].strip().upper() if len(row) > 2 else ""
                    self.freq_list.append([hz, mhz_str, desc, mode])
        except Exception as e:
            self.status.config(text=f"CSV load error: {e}")
            return

        for i in self.tree.get_children():
            self.tree.delete(i)
        for item in self.freq_list:
            self.tree.insert("", "end", values=(item[1], item[2], item[3]))

        self.status.config(text="CSV loaded. Ready to scan.")
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')

    def start_scan(self):
        if not self.freq_list:
            self.status.config(text="No freqs loaded.")
            return
        try:
            self.ser = serial.Serial(com_port, baud_rate, timeout=1,
                                     stopbits=serial.STOPBITS_TWO if stop_bits == 2 else serial.STOPBITS_ONE)
        except Exception as e:
            self.status.config(text=f"COM error: {e}")
            return
        self.scanning = True
        self.paused = False
        self.current_index = 0
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        threading.Thread(target=self.scan_loop, daemon=True).start()

    def stop_scan(self):
        self.scanning = False
        self.status.config(text="Scan stopped.")
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        if self.ser and self.ser.is_open:
            self.ser.close()


    def update_utc_time(self):
        now = datetime.utcnow().strftime('%H:%M:%S')
        if self.utc_label:
            self.utc_label.config(text=f"UTC: {now}")
        #self.root.after(1000, self.update_utc_time)
        self.utc_after_id = self.root.after(1000, self.update_utc_time)

    def update_kp_index(self):
        def fetch_and_update():
            try:
                r = requests.get("https://services.swpc.noaa.gov/json/planetary_k_index_1m.json", timeout=5)
                data = r.json()
                if data:
                    latest = data[-1]
                    kp = latest.get("kp_index")
                    t = latest.get("time_tag")
                    sched = f"Kp: {kp:.1f}  [{t} UTC]"
                else:
                    sched = "Kp: — (no data)"
            except Exception:
                sched = "Kp: err"
            self.root.after(0, lambda: self.kp_label.config(
                text=sched,
                fg='red' if 'Kp:' in sched and float(sched.split()[1]) > 7 else 'black'))
            try:
                if self.root.winfo_exists():
                    self.root.after(300000, self.update_kp_index)
            except tk.TclError:
                pass
        threading.Thread(target=fetch_and_update, daemon=True).start()

    def toggle_pause(self, event=None):
        #pylint: disable=unused-argument
        if not self.scanning:
            return
        self.paused = not self.paused
        st = "PAUSED" if self.paused else "RUNNING"
        self.status.config(text=f"Scan {st}. Press Space.")

    def scan_loop(self):
        while self.scanning:
            if self.paused:
                time.sleep(0.1)
                continue

            if self.current_index in self.skipped:
                self.current_index = self.get_next_index(self.current_index)
                continue

            hz, mhz_str, desc, mode = self.freq_list[self.current_index]
            code = self.mode_map.get(mode)
            if code:
                try:
                    self.ser.write(f"MD0{code};".encode())
                    time.sleep(post_delay_ms / 1000.0)
                except:
                    pass

            try:
                self.ser.write(f"FA{hz:09d};".encode())
            except Exception as e:
                self.status.config(text=f"Write error: {e}")
                break

            self.status.config(text=f"Sent {mhz_str[:7]}MHz [{mode}] {desc}")
            self.highlight_row()

            time.sleep(post_delay_ms / 1000.0)

            delay = int(self.delay_cb.get())
            waited = 0.0
            while waited < delay:
                if not self.scanning:
                    break
                time.sleep(0.1)
                waited += 0.1

            self.current_index = self.get_next_index(self.current_index)

        if self.ser and self.ser.is_open:
            self.ser.close()

    def get_next_index(self, start):
        n = len(self.freq_list)
        idx = (start + 1) % n
        while idx in self.skipped:
            idx = (idx + 1) % n
        return idx

    def highlight_row(self):
        for sel in self.tree.selection():
            self.tree.selection_remove(sel)
        kids = self.tree.get_children()
        if kids:
            cur = kids[self.current_index]
            self.tree.selection_add(cur)
            self.tree.see(cur)

    def on_row_toggle(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        all_items = self.tree.get_children()
        idx = all_items.index(row_id)

        if idx in self.skipped:
            self.skipped.remove(idx)
            self.tree.item(row_id, tags=())
        else:
            self.skipped.add(idx)
            self.tree.item(row_id, tags=('skipped',))

    def quit_app(self):
        try:
            if self.utc_after_id:
                self.root.after_cancel(self.utc_after_id)
            if self.ser and self.ser.is_open:
                self.ser.close()
        except:
            pass
        
        
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry('850x550')
    app = FreqScanrApp(root)
    root.mainloop()
