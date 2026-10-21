import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import pandas as pd

from api import Calendar
from exact_hours import Exact_hour
from worked_hours import Worked_hour
from leave import Leave_manager
from calendar_cache import Calendar_cache
from paths import app_dir


# نام فایل اثرانگشت؛ اگر کنار برنامه باشد خودکار خوانده می‌شود
FINGERPRINT_NAME = "fingerprints.TXT"

ALL = "همه"


class WorkedHoursGUI:

    def __init__(self, root):
        self.root = root

        self.root.title("سیستم محاسبه ساعات کاری")
        self.root.geometry("950x620")
        self.root.resizable(False, False)

        # -----------------------------
        # Data
        # -----------------------------

        self.years = [1404, 1405]

        self.months = [
            "فروردین", "اردیبهشت", "خرداد",
            "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر",
            "دی", "بهمن", "اسفند"
        ]

        self.month_dict = {
            month: number
            for number, month in enumerate(self.months, start=1)
        }

        self.leave_manager = Leave_manager()
        self.calendar_cache = Calendar_cache()

        # cache: calendar and worked hours are loaded only once
        self.df_cale = None
        self.total_worked = None

        self.create_widgets()

        # show the window first, then load all the data
        self.root.after(200, self.initial_load)

    # ==========================================================
    # UI
    # ==========================================================

    def create_widgets(self):

        title = tk.Label(
            self.root,
            text="محاسبه ساعات کاری کارمند",
            font=("Tahoma", 18, "bold")
        )

        title.pack(pady=15)

        # -----------------------------
        # Search frame
        # -----------------------------

        search_frame = tk.Frame(self.root)
        search_frame.pack(pady=5)

        # Employee ID

        tk.Label(
            search_frame,
            text="شناسه کارمند:",
            font=("Tahoma", 11)
        ).grid(row=0, column=0, padx=8, pady=8)

        self.id_entry = tk.Entry(
            search_frame,
            width=14,
            font=("Tahoma", 11)
        )

        self.id_entry.grid(row=0, column=1, padx=8)

        # Month

        tk.Label(
            search_frame,
            text="ماه:",
            font=("Tahoma", 11)
        ).grid(row=0, column=2, padx=8)

        self.month_combo = ttk.Combobox(
            search_frame,
            values=[ALL] + self.months,
            state="readonly",
            width=12,
            font=("Tahoma", 11)
        )

        self.month_combo.set(ALL)
        self.month_combo.grid(row=0, column=3, padx=8)

        # Year

        tk.Label(
            search_frame,
            text="سال:",
            font=("Tahoma", 11)
        ).grid(row=0, column=4, padx=8)

        self.year_combo = ttk.Combobox(
            search_frame,
            values=[ALL] + [str(y) for y in self.years],
            state="readonly",
            width=8,
            font=("Tahoma", 11)
        )

        self.year_combo.set(ALL)
        self.year_combo.grid(row=0, column=5, padx=8)

        # Buttons

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)

        tk.Button(
            button_frame,
            text="محاسبه",
            font=("Tahoma", 11, "bold"),
            width=12,
            command=self.search
        ).grid(row=0, column=0, padx=8)

        tk.Button(
            button_frame,
            text="نمایش همه",
            font=("Tahoma", 11, "bold"),
            width=12,
            command=self.show_all
        ).grid(row=0, column=1, padx=8)

        tk.Button(
            button_frame,
            text="ثبت مرخصی",
            font=("Tahoma", 11, "bold"),
            width=12,
            command=self.open_leave_window
        ).grid(row=0, column=2, padx=8)

        # Status label

        self.status_label = tk.Label(
            self.root,
            text="",
            font=("Tahoma", 10)
        )

        self.status_label.pack()

        # -----------------------------
        # Result table
        # -----------------------------

        result_frame = tk.LabelFrame(
            self.root,
            text="نتیجه",
            font=("Tahoma", 11, "bold"),
            padx=10,
            pady=10
        )

        result_frame.pack(
            padx=30,
            pady=10,
            fill="both",
            expand=True
        )

        columns = (
            "year",
            "month",
            "employee",
            "required",
            "leave",
            "worked",
            "overtime",
            "shortage"
        )

        self.tree = ttk.Treeview(
            result_frame,
            columns=columns,
            show="headings",
            height=12
        )

        headings = {
            "year": ("سال", 70),
            "month": ("ماه", 100),
            "employee": ("شناسه کارمند", 110),
            "required": ("ساعات موظفی", 120),
            "leave": ("مرخصی", 100),
            "worked": ("ساعات کارکرد", 120),
            "overtime": ("اضافه‌کاری", 120),
            "shortage": ("کسری کار", 120),
        }

        for key, (text, width) in headings.items():
            self.tree.heading(key, text=text)
            self.tree.column(key, width=width, anchor="center")

        # Scrollbar

        scrollbar = ttk.Scrollbar(
            result_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

    # ==========================================================
    # Load data (once)
    # ==========================================================

    def initial_load(self):
        """Load everything once and show all employees."""

        self.status_label.config(text="در حال بارگذاری اطلاعات ...")
        self.root.update_idletasks()

        if self.load_all():
            self.show_all()
        else:
            self.status_label.config(text="بارگذاری اطلاعات ناموفق بود.")

    def find_fingerprint_file(self):
        """
        Uses fingerprints.TXT next to the program if it exists,
        otherwise asks the user to choose the file.
        """

        path = os.path.join(app_dir(), FINGERPRINT_NAME)

        if os.path.exists(path):
            return path

        path = filedialog.askopenfilename(
            title="انتخاب فایل اثرانگشت",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if not path:
            raise RuntimeError("فایل اثرانگشت انتخاب نشد.")

        return path

    def load_all(self):
        """
        Reads the fingerprint file and fetches the calendar only for
        the (year, month) pairs that exist in the file.
        """

        try:

            # -----------------------------
            # Worked hours
            # -----------------------------

            worked = Worked_hour(self.find_fingerprint_file())

            total_worked = worked.calculate()

            # -----------------------------
            # Calendar (only months present in data)
            # -----------------------------

            pairs = (
                total_worked[["سال", "ماه_شمسی"]]
                .drop_duplicates()
                .sort_values(["سال", "ماه_شمسی"])
            )

            frames = []
            failed = []

            for _, p in pairs.iterrows():

                year = int(p["سال"])
                month = int(p["ماه_شمسی"])

                # use the local copy if this month was fetched before
                cached = self.calendar_cache.get(year, month)

                if cached is not None:
                    frames.append(cached)
                    continue

                try:
                    df = Calendar([year]).calender_date(month)
                    self.calendar_cache.put(year, month, df)
                    frames.append(df)
                except Exception:
                    failed.append(f"{year}/{month:02d}")

            if not frames:
                raise RuntimeError(
                    "دریافت اطلاعات تقویم ناموفق بود. اتصال اینترنت را بررسی کنید."
                )

            self.df_cale = pd.concat(frames, ignore_index=True)
            self.total_worked = total_worked

            if failed:
                messagebox.showwarning(
                    "هشدار",
                    "دریافت تقویم این ماه‌ها ناموفق بود و نمایش داده نمی‌شوند:\n"
                    + "، ".join(failed)
                )

            return True

        except Exception as e:

            messagebox.showerror(
                "خطا",
                f"خطا در پردازش اطلاعات:\n\n{e}"
            )

            return False

    def compute(self):
        """Calculates the result from cached data + current leaves."""

        leaves = self.leave_manager.to_dataframe()

        exact = Exact_hour(
            self.df_cale.copy(),
            self.total_worked,
            leaves
        )

        return exact.calculate()

    # ==========================================================
    # Search
    # ==========================================================

    def show_all(self):

        self.id_entry.delete(0, tk.END)
        self.month_combo.set(ALL)
        self.year_combo.set(ALL)

        self.search()

    def search(self):

        if self.df_cale is None or self.total_worked is None:

            messagebox.showwarning(
                "هشدار",
                "اطلاعات هنوز بارگذاری نشده است."
            )

            return

        # -----------------------------
        # Read filters (all optional)
        # -----------------------------

        table = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

        employee_id = self.id_entry.get().strip().translate(table)

        month_name = self.month_combo.get()

        year_text = self.year_combo.get()

        if employee_id:

            try:

                employee_id = int(employee_id)

            except ValueError:

                messagebox.showwarning(
                    "هشدار",
                    "شناسه کارمند باید عدد باشد."
                )

                return

        # -----------------------------
        # Calculate
        # -----------------------------

        try:

            result = self.compute()

        except Exception as e:

            messagebox.showerror(
                "خطا",
                f"خطا در پردازش اطلاعات:\n\n{e}"
            )

            return

        # -----------------------------
        # Apply filters
        # -----------------------------

        if employee_id != "":
            result = result[result["id"] == employee_id]

        if month_name != ALL:
            result = result[result["ماه_شمسی"] == self.month_dict[month_name]]

        if year_text != ALL:
            result = result[result["سال"] == int(year_text)]

        result = result.sort_values(["سال", "ماه_شمسی", "id"])

        # -----------------------------
        # Clear previous results
        # -----------------------------

        for item in self.tree.get_children():
            self.tree.delete(item)

        if result.empty:

            self.status_label.config(text="0 رکورد")

            messagebox.showinfo(
                "نتیجه",
                "اطلاعاتی با این مشخصات پیدا نشد."
            )

            return

        # -----------------------------
        # Fill table
        # -----------------------------

        for _, row in result.iterrows():

            self.tree.insert(
                "",
                "end",
                values=(
                    int(row["سال"]),
                    self.months[int(row["ماه_شمسی"]) - 1],
                    row["id"],
                    self.format_hours(row["certain_h"]),
                    self.format_hours(row["leave_hours"]),
                    self.format_hours(row["worked_hours"]),
                    self.format_hours(row["overtime"]),
                    self.format_hours(row["shortage"])
                )
            )

        self.status_label.config(text=f"{len(result)} رکورد")

    # ==========================================================
    # Leave window
    # ==========================================================

    def open_leave_window(self):

        win = tk.Toplevel(self.root)
        win.title("ثبت مرخصی")
        win.geometry("380x280")
        win.resizable(False, False)
        win.grab_set()

        font = ("Tahoma", 11)

        # Employee ID

        tk.Label(
            win,
            text="شناسه کارمند:",
            font=font
        ).grid(row=0, column=0, padx=10, pady=12)

        id_entry = tk.Entry(win, font=font, width=18)
        id_entry.grid(row=0, column=1)

        # Date

        tk.Label(
            win,
            text="تاریخ (1405/07/12):",
            font=font
        ).grid(row=1, column=0, padx=10, pady=12)

        date_entry = tk.Entry(win, font=font, width=18)
        date_entry.grid(row=1, column=1)

        # Leave type

        tk.Label(
            win,
            text="نوع مرخصی:",
            font=font
        ).grid(row=2, column=0, padx=10, pady=12)

        type_combo = ttk.Combobox(
            win,
            values=list(self.leave_manager.TYPES.keys()),
            state="readonly",
            font=font,
            width=16
        )
        type_combo.grid(row=2, column=1)

        # Amount (days or hours)

        amount_label = tk.Label(win, text="مقدار:", font=font)
        amount_label.grid(row=3, column=0, padx=10, pady=12)

        amount_var = tk.StringVar()

        amount_entry = tk.Entry(
            win,
            font=font,
            width=18,
            textvariable=amount_var
        )
        amount_entry.grid(row=3, column=1)

        # Persian digits -> English digits
        digits_table = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

        def is_zero(text):
            try:
                return float(text.strip().translate(digits_table)) == 0
            except ValueError:
                return False

        # if the amount is 0, the date and the leave type are meaningless -> disable them
        def on_amount_change(*args):

            if is_zero(amount_var.get()):
                date_entry.delete(0, tk.END)
                date_entry.config(state="disabled")
                type_combo.set("")
                type_combo.config(state="disabled")
            else:
                date_entry.config(state="normal")
                type_combo.config(state="readonly")

        amount_var.trace_add("write", on_amount_change)

        # Change label based on leave type

        def on_type_change(event=None):

            if self.leave_manager.TYPES[type_combo.get()] == "days":
                amount_label.config(text="تعداد روز:")
            else:
                amount_label.config(text="تعداد ساعت:")

        type_combo.bind("<<ComboboxSelected>>", on_type_change)

        # Save

        def save():

            # Persian digits -> English digits
            table = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

            emp = id_entry.get().strip().translate(table)
            date = date_entry.get().strip().translate(table)
            amount = amount_entry.get().strip().translate(table)
            leave_type = type_combo.get()

            zero = is_zero(amount)

            if not (emp and amount) or (not zero and not (date and leave_type)):

                messagebox.showwarning(
                    "هشدار",
                    "همه فیلدها را پر کنید.",
                    parent=win
                )

                return

            try:
                emp = int(emp)
            except ValueError:

                messagebox.showwarning(
                    "هشدار",
                    "شناسه کارمند باید عدد باشد.",
                    parent=win
                )

                return

            try:
                amount = float(amount)
                assert amount >= 0
            except Exception:

                messagebox.showwarning(
                    "هشدار",
                    "مقدار باید یک عدد (صفر یا بیشتر) باشد.",
                    parent=win
                )

                return

            # zero leave: nothing to subtract, so no date and nothing to save
            if amount == 0:

                messagebox.showinfo(
                    "ثبت شد",
                    "برای این کارمند مرخصی‌ای ثبت نشد (مقدار صفر).",
                    parent=win
                )

                win.destroy()

                return

            try:
                y, m, d = [int(x) for x in date.split("/")]
                assert 1 <= m <= 12 and 1 <= d <= 31
            except Exception:

                messagebox.showwarning(
                    "هشدار",
                    "تاریخ باید به شکل 1405/07/12 باشد.",
                    parent=win
                )

                return

            self.leave_manager.add(emp, date, leave_type, amount)

            messagebox.showinfo(
                "ثبت شد",
                "مرخصی ثبت شد.",
                parent=win
            )

            win.destroy()

            # refresh the table with the current filters
            self.search()

        tk.Button(
            win,
            text="ثبت",
            font=("Tahoma", 11, "bold"),
            width=12,
            command=save
        ).grid(row=4, column=0, columnspan=2, pady=20)

    # ==========================================================
    # Format hours
    # ==========================================================

    def format_hours(self, hours):

        if hours is None or pd.isna(hours):
            return "-"

        hours = float(hours)

        whole_hours = int(hours)

        minutes = round(
            (hours - whole_hours) * 60
        )

        if minutes == 60:

            whole_hours += 1
            minutes = 0

        return f"{whole_hours}:{minutes:02d}"

    # ==========================================================
    # Run
    # ==========================================================


if __name__ == "__main__":

    root = tk.Tk()

    app = WorkedHoursGUI(root)

    root.mainloop()