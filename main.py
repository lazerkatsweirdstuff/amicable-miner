import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import math
from collections import defaultdict
from queue import Queue
from tkinter import font as tkfont
import requests
from io import BytesIO
from PIL import Image, ImageTk
import tempfile
import os

# ===== GLOBALS =====
amicables = []
number_checks = 0
sum_cache = defaultdict(int)
running = False
update_queue = Queue()
current_n = 2  # Track where we left off

# ===== COLOR THEME =====
BG_COLOR = "#f0f0f0"
PRIMARY_COLOR = "#4a6fa5"
SECONDARY_COLOR = "#166088"
ACCENT_COLOR = "#4fc3f7"
DANGER_COLOR = "#ff5252"
SUCCESS_COLOR = "#4caf50"
TEXT_COLOR = "#333333"

# ===== MATH CORE =====
def sum_proper_divisors(n):
    if n in sum_cache:
        return sum_cache[n]
    if n == 1:
        return 0
    
    total = 1
    sqrt_n = int(math.isqrt(n))
    
    for i in range(2, sqrt_n + 1):
        if n % i == 0:
            total += i
            counterpart = n // i
            if counterpart != i:
                total += counterpart
    
    sum_cache[n] = total
    return total

def is_amicable(a, b):
    return sum_proper_divisors(a) == b and sum_proper_divisors(b) == a and a != b

# ===== SEARCH THREAD =====
def amicable_search():
    global amicables, number_checks, running, current_n
    checked = set(amicables)  # Keep track of already found pairs
    
    while running:
        if f"[{current_n}," not in checked:  # Skip if already found
            m = sum_proper_divisors(current_n)
            number_checks += 1
            
            if m > current_n and is_amicable(current_n, m):
                pair = f"[{current_n}, {m}]"
                amicables.append(pair)
                update_queue.put(f"Found: {pair} (Checks: {number_checks:,})")
                checked.add(pair)
        
        current_n += 1

# ===== FILE OPERATIONS =====
def export_amicables():
    if not amicables:
        messagebox.showwarning("No Pairs", "No amicable pairs found yet!")
        return
    
    data = {
        "pairs": amicables,
        "checks": number_checks,
        "current_n": current_n,
        "version": "1.0"
    }
    
    try:
        filepath = filedialog.asksaveasfilename(
            defaultextension=".amcb",
            filetypes=[("Amicable-miner files", "*.amcb"), ("All Files", "*.*")],
            title="Export Amicable Miner File"
        )
        
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Success", f"Exported {len(amicables)} pairs to:\n{filepath}")
    except Exception as e:
        messagebox.showerror("Export Failed", f"Error during export:\n{str(e)}")

def import_amicables():
    global amicables, number_checks, current_n, sum_cache
    
    try:
        filepath = filedialog.askopenfilename(
            filetypes=[("Amicable-miner files", "*.amcb"), ("All Files", "*.*")],
            title="Import Amicable-miner file"
        )
        
        if not filepath:
            return
            
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Validate imported data
        if not all(key in data for key in ["pairs", "checks", "current_n"]):
            raise ValueError("Invalid file format - missing required data")
            
        # Update global variables
        amicables = data["pairs"]
        number_checks = data["checks"]
        current_n = data["current_n"]
        sum_cache.clear()  # Clear cache as we'll need to rebuild it
        
        # Update UI
        app.log.delete(1.0, tk.END)
        for pair in amicables:
            app.log.insert(tk.END, f"Found: {pair}\n")
        
        app.update_stats()
        
        messagebox.showinfo("Import Successful", 
                          f"Successfully imported:\n"
                          f"- Pairs: {len(amicables)}\n"
                          f"- Checks: {number_checks:,}\n"
                          f"- Current number: {current_n}")
        
    except Exception as e:
        messagebox.showerror("Import Failed", f"Error importing file:\n{str(e)}")

# ===== GUI =====
class AmicableApp:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.create_widgets()
        self.check_queue()
    
    def setup_window(self):
        self.root.title("Amicable-Miner")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        self.root.configure(bg=BG_COLOR)
        
        # Set window icon
        self.set_window_icon()
        
        # Custom font
        self.custom_font = tkfont.Font(family="Segoe UI", size=10)
        self.title_font = tkfont.Font(family="Segoe UI", size=12, weight="bold")
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background=BG_COLOR)
        self.style.configure('TButton', font=self.custom_font, padding=6)
        self.style.configure('TLabel', background=BG_COLOR, foreground=TEXT_COLOR)
        self.style.map('TButton',
                      foreground=[('active', 'white'), ('pressed', 'white')],
                      background=[('active', SECONDARY_COLOR), ('pressed', PRIMARY_COLOR)])
    
    def set_window_icon(self):
        """Set the window icon from the GitHub URL"""
        icon_url = "https://raw.githubusercontent.com/lazerkatsweirdstuff/amicable-miner/refs/heads/main/Lo.ico"
        try:
            # First try Windows-specific method
            response = requests.get(icon_url, timeout=5)
            response.raise_for_status()
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix='.ico', delete=False) as tmp_file:
                tmp_file.write(response.content)
                tmp_file_path = tmp_file.name
            
            # Set the icon and clean up
            self.root.iconbitmap(tmp_file_path)
            os.unlink(tmp_file_path)
            
        except Exception as e:
            print(f"Could not set window icon: {e}")
            # Fallback for non-Windows systems
            try:
                icon_data = BytesIO(response.content)
                img = Image.open(icon_data)
                photo = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, photo)
            except Exception as e:
                print(f"Could not set fallback icon: {e}")
    
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(header_frame, 
                              text="Amicable-Miner", 
                              font=self.title_font,
                              foreground=PRIMARY_COLOR)
        title_label.pack(side=tk.LEFT)
        
        # Control panel
        control_frame = ttk.Frame(main_frame, style='TFrame')
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Buttons
        btn_style = {'style': 'TButton', 'padding': 8}
        self.start_button = ttk.Button(control_frame, text="▶ Start Search", 
                                      command=self.start_resume, **btn_style)
        self.stop_button = ttk.Button(control_frame, text="⏹ Stop", 
                                    command=self.stop, state=tk.DISABLED, **btn_style)
        self.reset_button = ttk.Button(control_frame, text="♻ Reset", 
                                     command=self.reset, **btn_style)
        self.export_button = ttk.Button(control_frame, text="💾 Export A-M File", 
                                      command=export_amicables, **btn_style)
        self.import_button = ttk.Button(control_frame, text="📂 Import A-M File", 
                                      command=import_amicables, **btn_style)
        
        # Grid layout for buttons
        buttons = [self.start_button, self.stop_button, self.reset_button, 
                  self.export_button, self.import_button]
        for i, btn in enumerate(buttons):
            btn.grid(row=0, column=i, padx=5, sticky='ew')
            control_frame.columnconfigure(i, weight=1)
        
        # Stats frame
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.pairs_label = ttk.Label(stats_frame, text="Pairs Found: 0")
        self.checks_label = ttk.Label(stats_frame, text="Numbers Checked: 0")
        self.current_label = ttk.Label(stats_frame, text="Current Number: 2")
        
        self.pairs_label.pack(side=tk.LEFT, padx=10)
        self.checks_label.pack(side=tk.LEFT, padx=10)
        self.current_label.pack(side=tk.LEFT, padx=10)
        
        # Log area
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log = tk.Text(log_frame, wrap=tk.WORD, font=self.custom_font,
                          bg='white', fg=TEXT_COLOR, padx=10, pady=10,
                          insertbackground=PRIMARY_COLOR)
        
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.config(yscrollcommand=scroll.set)
        
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status bar
        self.status_bar = ttk.Frame(main_frame, height=25)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(self.status_bar, text="🟢 Ready", 
                                    foreground=SUCCESS_COLOR)
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Configure weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
    
    def update_stats(self):
        self.pairs_label.config(text=f"Pairs Found: {len(amicables)}")
        self.checks_label.config(text=f"Numbers Checked: {number_checks:,}")
        self.current_label.config(text=f"Current Number: {current_n:,}")
    
    def start_resume(self):
        global running
        if not running:
            running = True
            threading.Thread(target=amicable_search, daemon=True).start()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="🔍 Searching...", foreground=PRIMARY_COLOR)
            self.update_stats()
    
    def stop(self):
        global running
        running = False
        self.start_button.config(text="⏯ Resume Search", state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="⏸ Paused", foreground=SECONDARY_COLOR)
        self.update_stats()
    
    def reset(self):
        global amicables, number_checks, current_n, running
        if running:
            self.stop()
        
        if amicables or number_checks > 0:
            if not messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all progress?"):
                return
        
        # Clear all data
        amicables.clear()
        number_checks = 0
        current_n = 2
        sum_cache.clear()
        self.log.delete(1.0, tk.END)
        self.start_button.config(text="▶ Start Search")
        self.status_label.config(text="🟢 Ready", foreground=SUCCESS_COLOR)
        self.update_stats()
    
    def check_queue(self):
        while not update_queue.empty():
            msg = update_queue.get()
            self.log.insert(tk.END, msg + "\n")
            self.log.see(tk.END)
            self.update_stats()
        self.root.after(100, self.check_queue)

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = AmicableApp(root)
    root.mainloop()
