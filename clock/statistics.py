import customtkinter as ctk
import sqlite3
from datetime import timedelta, date
from utils import format_time

class Statistics:
    def __init__(self, root):
        self.root = root
        self.db_path = 'db/usage_data.db'

    def show_statistics(self):
        stats_window = ctk.CTkToplevel(self.root)
        stats_window.title("Statistics")
        stats_window.geometry("600x500")

        ctk.CTkLabel(stats_window, text="Statistics Options").pack()

        frame = ctk.CTkFrame(stats_window)
        frame.pack(pady=10)
        label = ctk.CTkLabel(stats_window)
        label.pack()

        self.period = ctk.CTkComboBox(frame, values=["last day", "week", "month", "year", "custom"])
        self.period.pack(side=ctk.LEFT)
        button = ctk.CTkButton(frame, text="Load Stats")
        button.pack(side=ctk.LEFT)

        button.configure(command=lambda: self.show(label))

    def show(self, label):
        conn = sqlite3.connect(self.db_path)
        period = self.period.get()
        today = date.today()
        if period == "last day":
            start_date = today - timedelta(days=1)
        elif period == "week":
            start_date = today - timedelta(weeks=1)
        elif period == "month":
            start_date = today - timedelta(days=30)
        elif period == "year":
            start_date = today - timedelta(days=365)
        else:
            start_date = today - timedelta(days=7)  # Default to last week

        cursor = conn.cursor()
        cursor.execute("""
            SELECT app_name, SUM(focus_time) 
            FROM usage_data 
            WHERE date >= ? 
            GROUP BY app_name
        """, (start_date.isoformat(),))
        data = cursor.fetchall()
        conn.close()

        stats_text = "\n".join([f"{app}: {format_time(time)}" for app, time in data])
        label.configure(text=stats_text)

