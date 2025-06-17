# gui_start.py  –  only the imports + the scan-button callback are new/changed
# top: import Event
import threading
from threading import Event
import os, json, threading, tkinter as tk
from tkinter import messagebox, ttk
from gui.profile_manager   import ProfileManager, PROFILES_DIR
from gui.step_input_panel  import StepInputPanel
from main import run_pipeline          # <-- import your existing function



root = tk.Tk()
root.title("Công cụ dò quét trên GitHub")
root.geometry("1400x650")

# ───────────────────────────────────── LEFT : profile list
def on_profile_loaded(data: dict):
    step1.set_data(data.get("step_1_keywords", []))

    m1 = data.get("step_2_method_1", {})
    method1.set_data(m1.get("strings", []), use_flag=m1.get("use"))

    m2 = data.get("step_2_method_2", {})
    method2.set_data(
        m2.get("rules", []),
        use_flag=m2.get("use"),
        language=m2.get("language", "Python"),
    )

    m3 = data.get("step_2_method_3", {})
    method3.set_data(m3.get("rules", []), use_flag=m3.get("use"))

def set_interactive(enabled: bool):
    state = tk.NORMAL if enabled else tk.DISABLED
    # profile list + add/del/save buttons
    profile_panel.listbox.configure(state=state)
    for btn in (profile_panel.btn_add,
                profile_panel.btn_del,
                profile_panel.btn_save):
        btn.configure(state=state)
    # step-panel widgets
    for pnl in (step1, method1, method2, method3):
        pnl.text.configure(state=state if not pnl.with_checkbox or pnl.var.get() else tk.DISABLED)
        if pnl.with_checkbox:
            pnl.var_button.configure(state=state) if hasattr(pnl, 'var_button') else None
        if pnl.with_dropdown:
            pnl.dropdown.configure(state="readonly" if enabled else "disabled")
    # email text + save
    email_text = profile_panel.email_text
    email_text.configure(state=state)


profile_panel = ProfileManager(root, on_profile_loaded=on_profile_loaded)
profile_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

# ───────────────────────────────────── RIGHT : 5-column grid
right = tk.Frame(root)
right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# We reserve column-0 for the pink/brown controls,
# columns 1-4 for the four green panels + the wide yellow panel.
cols = 5
right.grid_rowconfigure(0, weight=0)      # green panels: natural height
right.grid_rowconfigure(1, weight=1)      # yellow panel: stretches
right.grid_columnconfigure(0, weight=0)   # control bar: fixed width
for c in range(1, cols):
    right.grid_columnconfigure(c, weight=1)

# ---------- row-0 : four green panels (columns 1-4) ----------
step1   = StepInputPanel(right, "B1")
method1 = StepInputPanel(right, "B2 - Quét chuỗi chuyên sâu", with_checkbox=True)
method2 = StepInputPanel(
    right, "B2 - Từ khóa trong tên hàm và tham số",
    with_checkbox=True, with_dropdown=True
)
method3 = StepInputPanel(right, "B2 - Từ khóa trong tên thư mục và tệp/thư mục con", with_checkbox=True)

for col, pnl in enumerate((step1, method1, method2, method3), start=1):
    pnl.grid(row=0, column=col, sticky="nsew", padx=5)

# ------------- row-1 : pink/brown control bar (col-0) ----------
controls = tk.Frame(right)
controls.grid(row=1, column=0, sticky="n", padx=(0, 6), pady=(12, 0))

scan_mode = tk.StringVar(value="Quét 1 lần")
ttk.OptionMenu(
    controls, scan_mode,
    "Quét 1 lần", "Quét 1 lần", "Quét liên tục"
).pack(pady=(0, 6))

# -------------- NEW: callback that runs the pipeline -------------
stop_event = Event()

def on_scan_click():
    if not stop_event.is_set() and btn_scan["text"] == "🔍":        # START
        btn_scan.config(text="⏹", state=tk.NORMAL)                 # show Stop icon
        set_interactive(False)

        stop_event.clear()

        results_text.delete("1.0", tk.END)
        results_text.insert(tk.END, "⏳ Đang quét...\n")

        def gui_append(text):
            def _insert():
                if results_text.get("1.0", "2.0").startswith("⏳ Đang quét"):
                    results_text.delete("1.0", "2.0")
                results_text.insert(tk.END, text + "\n")
                results_text.see(tk.END)
            results_text.after(0, _insert)

        def worker():
            try:
                while True:
                    run_pipeline(
                        display_callback=gui_append,
                        stop_event=stop_event
                    )

                    # exit if user pressed Stop during the last batch
                    if stop_event.is_set():
                        break

                    # exit if scan mode was switched back to “Quét 1 lần”
                    if scan_mode.get() != "Quét liên tục":
                        break

                    

            finally:
                results_text.after(0, scan_finished)


        threading.Thread(target=worker, daemon=True).start()

    else:                                                         # STOP
        stop_event.set()          # let the pipeline break out
        btn_scan.config(state=tk.DISABLED)   # will re-enable in scan_finished()

def scan_finished():
    # remove ⏳ line if it survived a cancel
    if results_text.get("1.0", "2.0").startswith("⏳ Đang quét"):
        results_text.delete("1.0", "2.0")
    btn_scan.config(text="🔍", state=tk.NORMAL)
    set_interactive(True)

    stop_event.clear()    # <── reset the flag




btn_scan = tk.Button(controls, text="🔍", command=on_scan_click)
btn_scan.pack()


# ---------- row-1 : wide yellow “Kết quả” panel (cols 1-4) ----------
results = tk.LabelFrame(right, text="Kết quả")
results.grid(row=1, column=1, columnspan=4, sticky="nsew", padx=5, pady=(12, 0))

results_text = tk.Text(results)
results_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

# ───────────────────────────────────── save-button wiring
# ───────────────────────────────────── save-button wiring
# ──────────────────────────────── save profile (kèm validation)
def save_current_profile() -> None:
    """Thu thập dữ liệu từ giao diện, kiểm tra hợp lệ, rồi ghi vào file JSON."""
    fname = profile_panel.get_selected_filename()
    if not fname:
        messagebox.showinfo("Chọn profile", "Hãy chọn profile để lưu.")
        return
    path = PROFILES_DIR / fname

    # --------- 1. Lấy dữ liệu thô từ các panel -----------------------
    step1_lines = [ln for ln in step1.get_data().splitlines() if ln.strip()]

    m1_use   = "yes" if method1.var and method1.var.get() else "no"
    m1_lines = [ln for ln in method1.get_data().splitlines() if ln.strip()]

    m2_use   = "yes" if method2.var and method2.var.get() else "no"
    m2_lines = [ln for ln in method2.get_data().splitlines() if ln.strip()]
    m2_lang  = method2.language_var.get().strip()

    m3_use   = "yes" if method3.var and method3.var.get() else "no"
    m3_lines = [ln for ln in method3.get_data().splitlines() if ln.strip()]

    # --------- 2. Hàm kiểm tra hợp lệ --------------------------------
    def validate() -> bool:
        if not step1_lines:
            messagebox.showwarning("Thiếu dữ liệu",
                                   "Bước 1 cần ít nhất 1 chuỗi khóa.")
            return False

        if m1_use == "yes" and not m1_lines:
            messagebox.showwarning("Thiếu dữ liệu",
                                   "Phương pháp 1 được chọn nhưng chưa có chuỗi.")
            return False

        def colon_ok(lines, label):
            for ln in lines:
                if ln.count(":") != 1:
                    messagebox.showwarning(
                        "Sai định dạng",
                        f"Mỗi dòng ở {label} phải có dạng keyword:param.\n"
                        f"Lỗi: “{ln}”")
                    return False
            return True

        if m2_use == "yes":
            if not m2_lines:
                messagebox.showwarning("Thiếu dữ liệu",
                                       "Phương pháp 2 được chọn nhưng danh sách rỗng.")
                return False
            if not colon_ok(m2_lines, "phương pháp 2"):
                return False
            if not m2_lang:
                messagebox.showwarning("Thiếu dữ liệu",
                                       "Chưa chọn ngôn ngữ cho phương pháp 2.")
                return False

        if m3_use == "yes":
            if not m3_lines:
                messagebox.showwarning("Thiếu dữ liệu",
                                       "Phương pháp 3 được chọn nhưng danh sách rỗng.")
                return False
            if not colon_ok(m3_lines, "phương pháp 3"):
                return False
        return True

    # Hủy lưu nếu không đạt
    if not validate():
        return

    # --------- 3. Đọc file cũ (nếu có) và ghi đè ---------------------
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    data["step_1_keywords"] = step1_lines

    data["step_2_method_1"] = {
        "use": m1_use,
        "strings": m1_lines,
    }
    data["step_2_method_2"] = {
        "use": m2_use,
        "language": m2_lang,
        "rules": m2_lines,
    }
    data["step_2_method_3"] = {
        "use": m3_use,
        "rules": m3_lines,
    }

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Đã lưu", f"Đã cập nhật {fname}.")
    except Exception as exc:
        messagebox.showerror("Lỗi", f"Không thể lưu:\n{exc}")



profile_panel.btn_save.config(command=save_current_profile)

root.mainloop()
