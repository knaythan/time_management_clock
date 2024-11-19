import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import timedelta, date

class Statistics:
    def __init__(self, root):
        self.root = root
        self.db_path = 'db/usage_data.db'

    def show_statistics(self):
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Statistics")
        stats_window.geometry("600x500")

        ttk.Label(stats_window, text="Statistics Options").pack()

        frame = ttk.Frame(stats_window)
        frame.pack(pady=10)
        label = ttk.Label(stats_window)
        label.pack()

        self.period = ttk.Combobox(frame, values=["last day", "week", "month", "year", "custom"])
        self.period.pack(side=tk.LEFT)
        button = ttk.Button(frame, text="Load Stats")
        button.pack(side=tk.LEFT)

        button.config(command=lambda: self.show(label))

    def show(self, label):
        conn = sqlite3.connect(self.db_path)
        period = self.period.get()
        if period == "last day":
            duration = timedelta(1)
        else:
            duration = timedelta(7)

        data = conn.execute("SQL Query")  # Get custom data
        conn.close()
        label.config(text=str(data))
