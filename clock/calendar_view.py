import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import date, timedelta
import os
import calendar

class CalendarView:
    def __init__(self, root, back_callback):
        self.root = root
        self.db_path = os.path.join(os.path.dirname(__file__), '../db/usage_data.db')
        self.current_date = date.today()
        self.min_date = self.get_earliest_date()
        self.tree = None
        self.back_callback = back_callback  # Callback to return to the previous view

    def show_calendar(self):
        """Override the current window with the Calendar View."""
        for widget in self.root.winfo_children():
            widget.destroy()

        ttk.Label(self.root, text="Calendar View", font=("Arial", 14)).pack(pady=10)

        # Navigation Controls
        nav_frame = ttk.Frame(self.root)
        nav_frame.pack(pady=10)

        self.previous_button = ttk.Button(nav_frame, text="◀", command=self.previous_day)
        self.previous_button.pack(side=tk.LEFT, padx=10)
        
        self.date_label = ttk.Label(nav_frame, text=self.current_date.isoformat())
        self.date_label.pack(side=tk.LEFT, padx=10)
        
        self.next_button = ttk.Button(nav_frame, text="▶", command=self.next_day)
        self.next_button.pack(side=tk.LEFT, padx=10)

        if self.current_date == date.today():
            self.next_button.state(["disabled"])

        # TreeView for daily data
        self.tree = ttk.Treeview(self.root, columns=('App', 'Time (s)'), show='headings')
        self.tree.heading('App', text='Application')
        self.tree.heading('Time (s)', text='Focus Time (s)')
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Monthly View", command=self.show_monthly_view).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Back to Dashboard", command=self.back_callback).pack(side=tk.LEFT, padx=5)

        self.update_data()

    def show_monthly_view(self):
        """Override with Monthly View."""
        for widget in self.root.winfo_children():
            widget.destroy()

        ttk.Label(self.root, text="Monthly View", font=("Arial", 14)).pack(pady=10)

        nav_frame = ttk.Frame(self.root)
        nav_frame.pack(pady=10)

        ttk.Button(nav_frame, text="◀", command=self.previous_month).pack(side=tk.LEFT, padx=10)
        self.month_label = ttk.Label(nav_frame, text=f"{calendar.month_name[self.current_date.month]} {self.current_date.year}")
        self.month_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(nav_frame, text="▶", command=self.next_month).pack(side=tk.LEFT, padx=10)

        self.days_frame = ttk.Frame(self.root)
        self.days_frame.pack(expand=True, fill=tk.BOTH)

        self.display_month_calendar()

        ttk.Button(self.root, text="Back to Calendar", command=self.show_calendar).pack(pady=10)

    def display_month_calendar(self):
        """Display a month calendar inline with color-coded days based on data availability."""
        for widget in self.days_frame.winfo_children():
            widget.destroy()

        # Create day-of-week headers
        for col, day in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
            ttk.Label(self.days_frame, text=day, anchor='center', width=10).grid(row=0, column=col, padx=5, pady=5)

        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdayscalendar(self.current_date.year, self.current_date.month)

        for row, week in enumerate(month_days, start=1):
            for col, day in enumerate(week):
                if day == 0:
                    continue

                day_date = date(self.current_date.year, self.current_date.month, day)
                has_data = self.check_day_has_data(day_date)

                # Color-code days based on whether they have data
                bg_color = "#A9A9A9" if has_data else "#FFFFFF"

                day_button = tk.Button(
                    self.days_frame,
                    text=str(day),
                    bg=bg_color,
                    command=lambda d=day: self.select_date(d)
                )
                day_button.grid(row=row, column=col, padx=5, pady=5)

    def select_date(self, day):
        """Handle date selection in monthly view."""
        self.current_date = date(self.current_date.year, self.current_date.month, day)
        self.show_calendar()

    def update_data(self):
        """Fetch and display daily data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT app_name, focus_time FROM usage_data WHERE date = ?", (self.current_date.isoformat(),))
        records = cursor.fetchall()
        conn.close()

        self.tree.delete(*self.tree.get_children())
        for app, time in records:
            self.tree.insert('', 'end', values=(app, time))

    def previous_day(self):
        """Navigate to the previous day."""
        self.current_date -= timedelta(days=1)
        self.update_data()
        self.date_label.config(text=self.current_date.isoformat())
        self.next_button.state(["!disabled"])
        if self.current_date == self.min_date:
            self.previous_button.state(["disabled"])

    def next_day(self):
        """Navigate to the next day."""
        self.current_date += timedelta(days=1)
        self.update_data()
        self.date_label.config(text=self.current_date.isoformat())
        if self.current_date == date.today():
            self.next_button.state(["disabled"])

    def previous_month(self):
        """Navigate to the previous month."""
        self.current_date = self.current_date.replace(day=1) - timedelta(days=1)
        self.show_monthly_view()

    def next_month(self):
        """Navigate to the next month."""
        self.current_date = self.current_date.replace(day=28) + timedelta(days=4)
        self.current_date = self.current_date.replace(day=1)
        self.show_monthly_view()

    def get_earliest_date(self):
        """Get the earliest saved date."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MIN(date) FROM usage_data")
        result = cursor.fetchone()[0]
        conn.close()
        return date.fromisoformat(result) if result else date.today()

    def check_day_has_data(self, day_date):
        """Check if the given day has stored data in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usage_data WHERE date = ?", (day_date.isoformat(),))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0