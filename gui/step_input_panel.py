import tkinter as tk
from tkinter import ttk


class StepInputPanel(tk.LabelFrame):
    """
    One of the 4 green panels.  Uses a 4-row grid so every checkbox
    occupies grid-row 3, putting all check-boxes on the same line.
    """
    def __init__(self, master, title, *, with_checkbox=False, with_dropdown=False):
        super().__init__(master, text=title, padx=8, pady=8)

        self.with_checkbox  = with_checkbox
        self.with_dropdown  = with_dropdown
        self.var            = tk.BooleanVar() if with_checkbox else None
        self.language_var   = tk.StringVar(value="Python") if with_dropdown else None

        # ── grid layout inside this LabelFrame ─────────────────────────
        # row-0 : Text area (stretchy)
        # row-1 : optional dropdown
        # row-2 : nothing   (acts as flexible spacer)
        # row-3 : optional checkbox (anchor south)
        self.grid_columnconfigure(0, weight=1)   # full width
        self.grid_rowconfigure(0, weight=1)      # text stretches
        self.grid_rowconfigure(2, weight=1)      # spacer takes leftovers

        # 0️⃣  multi-line text
        self.text = tk.Text(self, height=10)
        self.text.grid(row=0, column=0, sticky="nsew")

        # after creating the dropdown
        if self.with_dropdown:
            self.dropdown = ttk.OptionMenu(
                self, self.language_var,
                "Python", "Python", "Java", "C#", "C/C++", "Ruby"
            )
            self.dropdown.grid(row=1, column=0, sticky="w", pady=(6, 0))

        # 3️⃣  checkbox
        if self.with_checkbox:
            self.var_button = tk.Checkbutton(
                self, text="Sử dụng phương pháp này",
                variable=self.var, command=self.toggle_state
            )
            self.var_button.grid(row=3, column=0, sticky="w", pady=(6, 0))

        self.toggle_state()          # start disabled if unchecked

    # ──────────────────────────────────────────────────────────────── helpers
    def toggle_state(self):
        state = "normal" if (not self.with_checkbox or self.var.get()) else "disabled"
        self.text.config(state=state)

    # ------------------- called by controller ----------------------
    def set_data(self, lines, *, use_flag=None, language=None):
        if self.with_checkbox and use_flag is not None:
            self.var.set(use_flag == "yes")
        if self.with_dropdown and language:
            self.language_var.set(language)

        self.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        self.text.insert(tk.END, "\n".join(lines))
        self.toggle_state()

    def get_data(self) -> str:
        """Always return a string so caller can .splitlines() safely."""
        if self.with_checkbox and not self.var.get():
            return ""
        return self.text.get("1.0", tk.END).rstrip("\n")
