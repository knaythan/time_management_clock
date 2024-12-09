import os
import tkinter as tk
from tkinter import ttk, messagebox
from dashboard import ProductivityDashboard
from focus_mode import FocusMode
from app_monitor import AppMonitor
from settings import Settings
from calendar_view import CalendarView
import sqlite3
import platform

class SmartClockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Time-Management Clock")
        self.root.geometry("800x600")

        # Initialize core components
        self.settings = Settings()
        self.app_monitor = AppMonitor()
        self.focus_mode = FocusMode(self.root)
        self.dashboard = ProductivityDashboard(self.root, self.app_monitor, self.rename_app)
        self.calendar_view = CalendarView(self.root, self.show_dashboard)

        if platform.system() == "Windows":
            self.db_path = os.path.join(os.path.dirname(__file__), '../db/usage_data.db')
        elif platform.system() == "Darwin":
            self.db_path = os.path.expanduser("~/Library/Application Support/SmartClock/db/usage_data.db")

        # Start monitoring
        self.app_monitor.start_monitoring()
        self._setup_database()

        # Display initial dashboard
        self.show_dashboard()

    def show_dashboard(self):
        """Display the Dashboard View and restart periodic updates."""
        # Clear any current widgets in the root window
        for widget in self.root.winfo_children():
            widget.destroy()

        ttk.Label(self.root, text="Dashboard", font=("Arial", 16)).pack(pady=10)
        self.dashboard.display(self.root)  # Render the Dashboard

        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Open Calendar", command=self.open_calendar).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Settings", command=self.open_settings).pack(side=tk.LEFT, padx=5)

    def open_calendar(self):
        """Navigate to the Calendar View and stop dashboard updates."""
        self.dashboard.stop_updates()  # Stop updates when leaving the dashboard
        self.calendar_view.show_calendar()  # Show the calendar inline

    def open_settings(self):
        """Navigate to the Settings View and stop dashboard updates."""
        self.dashboard.stop_updates()  # Stop updates for settings view
        for widget in self.root.winfo_children():
            widget.destroy()

        ttk.Label(self.root, text="Settings", font=("Arial", 16)).pack(pady=10)

        autosave_var = tk.BooleanVar(value=self.settings.get("autosave"))
        ttk.Checkbutton(self.root, text="Enable Autosave", variable=autosave_var).pack(pady=5)

        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Save", command=lambda: self.save_settings(autosave_var, save_only=True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save and Exit", command=lambda: self.save_settings(autosave_var, save_only=False)).pack(side=tk.LEFT, padx=5)

    def save_settings(self, autosave_var, save_only):
        """Save settings and optionally return to dashboard."""
        self.settings.update("autosave", autosave_var.get())
        if not save_only:
            self.show_dashboard()

    def rename_app(self, old_name, new_name):
        """Rename application in the database and merge data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE usage_data SET app_name = ? WHERE app_name = ?", (new_name, old_name))
        conn.commit()
        conn.close()
        self.dashboard.update_dashboard()

    def _setup_database(self):
        """Set up SQLite database for saving focus times."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_data (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                app_name TEXT NOT NULL,
                focus_time REAL NOT NULL,
                UNIQUE(date, app_name)
            )
        """)
        conn.commit()
        conn.close()

    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartClockApp(root)
    app.run()
