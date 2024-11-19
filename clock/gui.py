import os
import sqlite3
from datetime import date
from dashboard import ProductivityDashboard
from focus_mode import FocusMode
from app_monitor import AppMonitor
from settings import Settings
from calendar_view import CalendarView
import tkinter as tk
from tkinter import ttk, messagebox

class SmartClockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Time-Management Clock")
        self.root.geometry("800x600")

        # Initialize core components
        self.settings = Settings()
        self.app_monitor = AppMonitor()
        self.focus_mode = FocusMode(self.root)
        self.dashboard = ProductivityDashboard(self.root, self.app_monitor)
        self.calendar_view = CalendarView(self.root)

        # Determine the correct path for the database
        self.db_path = os.path.join(os.path.dirname(__file__), '../db/usage_data.db')

        # Start monitoring
        self.app_monitor.start_monitoring()
        self._setup_database()

        # Set up the UI
        self.create_main_interface()
        self.create_menu()

    def create_main_interface(self):
        """Create the main interface with the productivity dashboard."""
        frame = ttk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)

        # Display the Productivity Dashboard
        self.dashboard.display(frame)

        # Control Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Start Focus Mode", command=self.toggle_focus_mode).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Settings", command=self.open_settings).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Save to Calendar", command=self.save_to_calendar).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="View Calendar", command=self.view_calendar).pack(side=tk.LEFT, padx=10)

    def create_menu(self):
        """Create the menu bar."""
        menu_bar = tk.Menu(self.root)
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Focus Mode", command=self.toggle_focus_mode)
        settings_menu.add_separator()
        settings_menu.add_command(label="Exit", command=self.exit_app)
        menu_bar.add_cascade(label="Menu", menu=settings_menu)
        self.root.config(menu=menu_bar)

    def save_to_calendar(self):
        """Save the current session's focus times to the calendar."""
        today = date.today().isoformat()
        app_times = self.app_monitor.get_app_times()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for app, focus_time in app_times.items():
            cursor.execute("INSERT INTO usage_data (date, app_name, focus_time) VALUES (?, ?, ?)",
                           (today, app, focus_time))
        conn.commit()
        conn.close()
        messagebox.showinfo("Save to Calendar", "Today's focus times have been saved!")

    def view_calendar(self):
        """Open the calendar view to check saved focus times."""
        self.calendar_view.show_calendar()

    def open_settings(self):
        """Open the settings window."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")

        autosave_var = tk.BooleanVar(value=self.settings.get("autosave"))
        ttk.Checkbutton(settings_window, text="Enable Autosave", variable=autosave_var).pack(pady=5)

        ttk.Button(settings_window, text="Save", 
                   command=lambda: self.settings.update("autosave", autosave_var.get())).pack(pady=10)

    def toggle_focus_mode(self):
        """Toggle Focus Mode."""
        if not self.focus_mode.is_active:
            self.focus_mode.activate()
        else:
            self.focus_mode.deactivate()

    def exit_app(self):
        """Exit the application, saving data if autosave is enabled."""
        if self.settings.get("autosave"):
            self.save_to_calendar()
        self.root.quit()

    def _setup_database(self):
        """Set up the SQLite database for storing usage data."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_data (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                app_name TEXT NOT NULL,
                focus_time REAL NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartClockApp(root)
    app.run()
