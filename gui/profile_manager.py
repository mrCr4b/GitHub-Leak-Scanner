import os, re, json, string, tkinter as tk
from tkinter import messagebox

from common_helpers import base_dir
PROFILES_DIR = base_dir() / "profiles"
EMAIL_FILE   = base_dir() / "email.txt"
EMAIL_RE = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)
# ───────────────────────────────────────────────────────────────── helpers
def next_profile_filename() -> str:
    os.makedirs(PROFILES_DIR, exist_ok=True)
    existing = {f for f in os.listdir(PROFILES_DIR) if f.startswith("profile_") and f.endswith(".json")}
    for letter in string.ascii_uppercase:
        cand = f"profile_{letter}.json"
        if cand not in existing:
            return cand
    nums = [int(m.group(1)) for f in existing if (m := re.fullmatch(r"profile_(\d+)\.json", f))]
    return f"profile_{max(nums, default=0) + 1}.json"


# ───────────────────────────────────────────────────────────────── widget
class ProfileManager(tk.Frame):
    def __init__(self, master, *, on_profile_loaded=None):
        super().__init__(master)
        self.on_profile_loaded = on_profile_loaded
        self.profile_files: list[tuple[str, str]] = []
        self._create_widgets()
        self.load_profiles()
        self.load_emails()

    # ---------------------------------------------------------------- UI
    def _create_widgets(self):
        # ――― profile list ―――
        list_frame = tk.LabelFrame(self, text="Profiles", padx=10, pady=10)
        list_frame.pack(padx=10, pady=10, fill="x")

        self.listbox = tk.Listbox(list_frame, width=30, height=10, selectmode=tk.SINGLE, exportselection=False)
        self.listbox.pack()
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        btn_row = tk.Frame(self)
        btn_row.pack(padx=10, pady=(0, 10), fill="x")

        self.btn_add  = tk.Button(btn_row, text="➕", command=self.add_profile)
        self.btn_del  = tk.Button(btn_row, text="❌", command=self.delete_profile, state=tk.DISABLED)
        self.btn_save = tk.Button(btn_row, text="💾")           # wired from gui_start

        for b in (self.btn_add, self.btn_del, self.btn_save):
            b.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

        # ――― email list ―――
        email_frame = tk.LabelFrame(self, text="Emails", padx=10, pady=10)
        email_frame.pack(padx=10, fill="x")                    # same width as profile frame

        self.email_text = tk.Text(email_frame, width=30, height=6)
        self.email_text.pack()

        tk.Button(email_frame, text="💾", command=self.save_emails)\
          .pack(pady=(6, 0))

    # ---------------------------------------------------------------- list helpers
    def get_selected_filename(self) -> str | None:
        sel = self.listbox.curselection()
        return None if not sel else self.profile_files[sel[0]][0]

    get_selected_profile_filename = get_selected_filename  # backward compat

    def load_profiles(self):
        os.makedirs(PROFILES_DIR, exist_ok=True)
        self.profile_files.clear()
        self.listbox.delete(0, tk.END)

        for fname in sorted(os.listdir(PROFILES_DIR)):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(PROFILES_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    disp = json.load(f).get("profile_name", fname[:-5])
            except Exception:
                disp = fname[:-5]
            self.profile_files.append((fname, disp))
            self.listbox.insert(tk.END, disp)

    # ---------------------------------------------------------------- email helpers
    def load_emails(self):
        self.email_text.delete("1.0", tk.END)
        try:
            with open(EMAIL_FILE, "r", encoding="utf-8") as f:
                self.email_text.insert("1.0", f.read().rstrip("\n"))
        except FileNotFoundError:
            pass
        except Exception as exc:
            messagebox.showerror("Lỗi", f"Không thể đọc {EMAIL_FILE}:\n{exc}")

    def save_emails(self) -> None:
        """Kiểm tra & lưu danh sách e-mail."""
        raw_lines = self.email_text.get("1.0", tk.END).splitlines()
        emails = [ln.strip() for ln in raw_lines if ln.strip()]

        # 1️⃣  phải có ít nhất 1 email
        if not emails:
            messagebox.showwarning("Thiếu dữ liệu",
                                   "Bạn phải nhập ít nhất một địa chỉ e-mail.")
            return

        # 2️⃣  validate từng địa chỉ
        invalid = [e for e in emails if not EMAIL_RE.fullmatch(e)]
        if invalid:
            messagebox.showwarning(
                "Sai định dạng",
                "Các dòng sau không hợp lệ:\n• " + "\n• ".join(invalid)
            )
            return

        # 3️⃣  ghi file khi hợp lệ
        try:
            with open(EMAIL_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(emails) + "\n")
            messagebox.showinfo("Đã lưu", f"Đã cập nhật danh sách email.")
        except Exception as exc:
            messagebox.showerror("Lỗi", f"Không thể lưu:\n{exc}")

    # ---------------------------------------------------------------- callbacks
    def _on_select(self, _evt=None):
        self.btn_del.config(state=tk.NORMAL if self.listbox.curselection() else tk.DISABLED)
        if self.on_profile_loaded and (fname := self.get_selected_filename()):
            try:
                with open(os.path.join(PROFILES_DIR, fname), "r", encoding="utf-8") as f:
                    self.on_profile_loaded(json.load(f))
            except Exception as exc:
                messagebox.showerror("Lỗi", f"Không đọc được {fname}:\n{exc}")

    # ---------------------------------------------------------------- actions
    def add_profile(self):
        def _save():
            name, desc = e_name.get().strip(), e_desc.get().strip()
            if not (name and desc):
                messagebox.showwarning("Thiếu dữ liệu", "Nhập đủ tên & mô tả.")
                return
            path = os.path.join(PROFILES_DIR, next_profile_filename())
            data = {
                "profile_name": name, "profile_description": desc,
                "step_1_keywords": [],
                "step_2_method_1": {"use": "no", "strings": []},
                "step_2_method_2": {"use": "no", "language": "", "rules": []},
                "step_2_method_3": {"use": "no", "rules": []},
            }
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                popup.destroy()
                self.load_profiles()
            except Exception as exc:
                messagebox.showerror("Lỗi", exc)

        popup = tk.Toplevel(self)
        popup.title("Tạo profile mới")
        tk.Label(popup, text="Tên profile:").pack(padx=10, pady=(10, 0))
        e_name = tk.Entry(popup, width=30); e_name.pack(padx=10, pady=(0, 10)); e_name.focus_set()
        tk.Label(popup, text="Mô tả profile:").pack(padx=10, pady=(0, 0))
        e_desc = tk.Entry(popup, width=30); e_desc.pack(padx=10, pady=(0, 10))
        tk.Button(popup, text="Lưu", command=_save).pack(pady=(0, 10))

    def delete_profile(self):
        fname = self.get_selected_filename()
        if fname and messagebox.askyesno("Xác nhận", f"Xóa {fname}?"):
            try:
                os.remove(os.path.join(PROFILES_DIR, fname))
                self.load_profiles()
            except Exception as exc:
                messagebox.showerror("Lỗi", exc)
