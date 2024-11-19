import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import date, timedelta
import os
import calendar

class CalendarView:
    def __init__(self, root):
        self.root = root
        # Ensure the correct path is always used for the database
        self.db_path = os.path.join(os.path.dirname(__file__), '../db/usage_data.db')
        self.current_date = date.today()
        self.min_date = self.get_earliest_date()
        self.tree = None

    def show_calendar(self):
        """Show the calendar with daily navigation and data."""
        self.calendar_window = tk.Toplevel(self.root)
        self.calendar_window.title("Calendar View")
        self.calendar_window.geometry("600x500")

        # Navigation Controls
        nav_frame = ttk.Frame(self.calendar_window)
        nav_frame.pack(pady=10)

        self.previous_button = ttk.Button(nav_frame, text="◀", command=self.previous_day)
        self.previous_button.pack(side=tk.LEFT, padx=10)
        
        self.date_label = ttk.Label(nav_frame, text=self.current_date.isoformat())
        self.date_label.pack(side=tk.LEFT, padx=10)
        
        self.next_button = ttk.Button(nav_frame, text="▶", command=self.next_day)
        self.next_button.pack(side=tk.LEFT, padx=10)

        # Disable "Next" if on the current day
        if self.current_date == date.today():
            self.next_button.state(["disabled"])

        # TreeView for daily data
        self.tree = ttk.Treeview(self.calendar_window, columns=('App', 'Time (s)'), show='headings')
        self.tree.heading('App', text='Application')
        self.tree.heading('Time (s)', text='Focus Time (s)')
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

        # Monthly View Button
        ttk.Button(self.calendar_window, text="Monthly View", command=self.show_monthly_view).pack(pady=5)

        self.update_data()

    def get_earliest_date(self):
        """Get the earliest saved date in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MIN(date) FROM usage_data")
        result = cursor.fetchone()[0]
        conn.close()
        return date.fromisoformat(result) if result else date.today()

    def previous_day(self):
        """Navigate to the previous day."""
        self.current_date -= timedelta(days=1)
        self.update_data()
        self.date_label.config(text=self.current_date.isoformat())
        if self.current_date < date.today():
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
        if self.current_date > self.min_date:
            self.previous_button.state(["!disabled"])

    def show_monthly_view(self):
        """Open a new window for selecting a date from a monthly calendar."""
        monthly_window = tk.Toplevel(self.calendar_window)
        monthly_window.title("Monthly View")
        monthly_window.geometry("400x300")

        month_label = ttk.Label(monthly_window, text=f"{calendar.month_name[self.current_date.month]} {self.current_date.year}")
        month_label.pack(pady=5)

        days_frame = ttk.Frame(monthly_window)
        days_frame.pack()

        cal = calendar.Calendar()
        days = cal.itermonthdays(self.current_date.year, self.current_date.month)
        for day in days:
            if day == 0:
                ttk.Label(days_frame, text=" ", width=5).grid()
            else:
                btn = ttk.Button(days_frame, text=str(day), command=lambda d=day: self.select_date(d))
                btn.grid()

    def select_date(self, day):
        """Select a date from the monthly view."""
        self.current_date = date(self.current_date.year, self.current_date.month, day)
        self.update_data()
        self.date_label.config(text=self.current_date.isoformat())

    def update_data(self):
        """Update data in the tree for the current day."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT app_name, focus_time FROM usage_data WHERE date = ?", (self.current_date.isoformat(),))
        records = cursor.fetchall()
        conn.close()

        self.tree.delete(*self.tree.get_children())
        for app, time in records:
            self.tree.insert('', 'end', values=(app, time))
