import os
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from dashboard import ProductivityDashboard
from focus_mode import FocusMode
from app_monitor import AppMonitor
from settings import Settings
from calendar_view import CalendarView
import sqlite3
import platform
from stop_distract import StopDistract

class SmartClockApp:
    def __init__(self, root):
        self.root = root
        title = "Smart Time-Management Clock"
        self.root.title(title)
        self.root.geometry("1000x800")

        # Initialize core components
        if platform.system() == "Windows":
            self.db_path = os.path.join(os.path.dirname(__file__), '../db/usage_data.db')
        elif platform.system() == "Darwin":
            self.db_path = os.path.expanduser("~/Library/Application Support/SmartClock/db/usage_data.db")
        self.settings = Settings()
        self.app_monitor = AppMonitor(self.db_path, afk_threshold=self.settings.get("afk_threshold"))
        self.focus_mode = FocusMode(self.root)
        self.stop_distract = self.stop_distract = StopDistract(self.root, self.settings.get("reminder"), self.app_monitor)
        self.dashboard = ProductivityDashboard(self.root, self.app_monitor, self.rename_app, self.db_path, stop_distract=self.stop_distract)
        self.dashboard.settings = self.settings  # Pass settings to the dashboard
        self.calendar_view = CalendarView(self.root, self.show_dashboard)

        # Start monitoring
        self.app_monitor.start_monitoring()
        if self.settings.get("afk_detection"):
            self.app_monitor.start_afk_detection()
        # self.app_monitor.start_minimize()
        self._setup_database()

        # Bind the close event to save focus times if autosave is enabled
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Display initial dashboard
        self.show_dashboard()
        

    def show_dashboard(self):
        """Display the Dashboard View and restart periodic updates."""
        for widget in self.root.winfo_children():
            widget.destroy()

        self.dashboard.display()  # Render the Dashboard

        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(pady=10)

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(button_frame, text="Open Calendar", command=self.open_calendar).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(button_frame, text="Settings", command=self.open_settings).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(button_frame, text="Activate Focus Mode", command=self.activate_focus_mode).grid(row=0, column=2, padx=5, pady=5, sticky="ew")


    def activate_focus_mode(self):
        self.focus_mode.activate()

    def open_calendar(self):
        self.dashboard.stop_updates()
        self.calendar_view.show_calendar()

    def open_settings(self):
        """Navigate to the Settings View and stop dashboard updates."""
        self.dashboard.stop_updates()
        for widget in self.root.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.root, text="Settings", font=("Arial", 16)).pack(pady=10)

        # Autosave toggle
        autosave_var = ctk.BooleanVar(value=self.settings.get("autosave"))
        ctk.CTkCheckBox(self.root, text="Enable Autosave for Focus Times", variable=autosave_var).pack(pady=5)

        # Theme and mode selection dropdowns
        theme_var = ctk.StringVar(value=self.settings.get("theme"))  # Default theme
        mode_var = ctk.StringVar(value=self.settings.get("mode"))  # Default mode
        reminder_var = ctk.StringVar(value=self.settings.get("reminder"))  # Default reminder

        ctk.CTkLabel(self.root, text="Select Theme:").pack(pady=5)
        theme_dropdown = ctk.CTkOptionMenu(
            self.root,
            values=["blue", "green", "dark-blue"],
            variable=theme_var
        )
        theme_dropdown.pack(pady=5)

        ctk.CTkLabel(self.root, text="Select Mode:").pack(pady=5)
        mode_dropdown = ctk.CTkOptionMenu(
            self.root,
            values=["Light", "Dark"],
            variable=mode_var
        )
        mode_dropdown.pack(pady=5)
        
        ctk.CTkLabel(self.root, text="Select Reminder Severity:").pack(pady=5)
        reminder_dropdown = ctk.CTkOptionMenu(
            self.root,
            values=["low", "medium", "high"],
            variable=reminder_var
        )
        reminder_dropdown.pack(pady=5)

        # AFK detection toggle
        afk_detection_var = ctk.BooleanVar(value=self.settings.get("afk_detection"))
        ctk.CTkCheckBox(self.root, text="Enable AFK Detection", variable=afk_detection_var).pack(pady=5)

        # Initialize afk_timer_var with a default value
        afk_timer_var = ctk.StringVar(value=self.settings.get("afk_threshold") or "0")

        # AFK Timer threshold
        ctk.CTkLabel(self.root, text="AFK Timer Threshold (seconds):").pack(pady=5)
        afk_timer_entry = ctk.CTkEntry(self.root, textvariable=afk_timer_var, state="normal" if afk_detection_var.get() else "disabled")
        afk_timer_entry.pack(pady=5)

        def toggle_afk_timer_entry(*args):
            state = "normal" if afk_detection_var.get() else "disabled"
            if state == "disabled":
                afk_timer_entry.configure(fg_color="gray")
            else:
                afk_timer_entry.configure(fg_color=ctk.ThemeManager.theme["CTkEntry"]["fg_color"])
            afk_timer_entry.configure(state=state)

        afk_detection_var.trace_add("write", toggle_afk_timer_entry)
        
        # Dynamic scheduling options
        ctk.CTkLabel(self.root, text="Dynamic Scheduling:").pack(pady=5)
        dynamic_schedule_var = ctk.StringVar(value="pomodoro")  # Default technique
        ctk.CTkOptionMenu(
            self.root,
            values=["pomodoro", "eat the frog", "custom"],
            variable=dynamic_schedule_var
        ).pack(pady=5)

        # Save and exit buttons
        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(pady=10)

        ctk.CTkButton(
            button_frame,
            text="Save",
            command=lambda: self.save_settings_with_theme_and_schedule(autosave_var, theme_var, mode_var, afk_detection_var, reminder_var, dynamic_schedule_var, afk_timer_var, update_ui=True, reopen_settings=True)
        ).pack(side=ctk.LEFT, padx=5)

        ctk.CTkButton(
            button_frame,
            text="Exit",
            command=self.show_dashboard
        ).pack(side=ctk.LEFT, padx=5)

        # Add button to open classify app popup
        ctk.CTkButton(
            button_frame,
            text="Classify Apps",
            command=self.open_classify_apps_popup
        ).pack(side=ctk.LEFT, padx=5)


    def open_classify_apps_popup(self):
        """Open a popup window to classify applications."""
        
        popup = ctk.CTkToplevel(self.root)
        popup.title("Classify Applications")
        popup.geometry("400x300")

        ctk.CTkLabel(popup, text="Classify Applications", font=("Arial", 16)).pack(pady=10)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT app_name FROM usage_data GROUP BY app_name")
        usage_apps = cursor.fetchall()
        cursor.execute("SELECT app_name, category FROM classify_app")
        classified_apps = dict(cursor.fetchall())
        cursor.execute("SELECT original_name, custom_name FROM app_names")
        app_nicknames = dict(cursor.fetchall())
        conn.close()

        app_vars = {}
        tree_frame = ctk.CTkFrame(popup)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background="#333333",
                        foreground="white",
                        fieldbackground="#333333",
                        font=("Arial", 12),
                        borderwidth=0,
                        highlightthickness=0)
        style.configure("Treeview.Heading",
                        background="#444444",
                        foreground="white",
                        font=("Arial", 12, "bold"))
        style.map('Treeview', background=[('selected', '#555555')], foreground=[('selected', 'grey')])

        tree = ttk.Treeview(tree_frame, columns=('App', 'Category'), show='headings', selectmode="browse", style="Treeview")
        tree.heading('App', text='Application')
        tree.heading('Category', text='Category')
        tree.pack(fill="both", expand=True)

        for (app_name,) in usage_apps:
            display_name = app_nicknames.get(app_name, app_name)
            category = classified_apps.get(app_name, "NONE")
            app_vars[app_name] = ctk.StringVar(value=category)
            tree.insert('', 'end', values=(display_name, category))

        def on_tree_select(event):
            selected_item = tree.selection()[0]
            display_name, current_category = tree.item(selected_item, 'values')
            app_name = next(key for key, value in app_nicknames.items() if value == display_name) if display_name in app_nicknames.values() else display_name

            category_popup = ctk.CTkToplevel(popup)
            category_popup.title("Edit Category")
            category_popup.geometry("300x200")

            ctk.CTkLabel(category_popup, text=f"Application: {display_name}", font=("Arial", 14)).pack(pady=10)
            category_var = ctk.StringVar(value=current_category)
            ctk.CTkLabel(category_popup, text="Select Category:").pack(pady=5)
            category_dropdown = ctk.CTkOptionMenu(
                category_popup,
                values=["Productive", "Unproductive"],
                variable=category_var
            )
            category_dropdown.pack(pady=5)

            def save_category():
                new_category = category_var.get()
                tree.item(selected_item, values=(display_name, new_category))
                category_popup.destroy()

            ctk.CTkButton(category_popup, text="Save", command=save_category).pack(pady=10)
            category_popup.focus_force()
            category_popup.transient(popup)
            popup.wait_window(category_popup)

        tree.bind("<Double-1>", on_tree_select)

        def save_classifications():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            for item in tree.get_children():
                display_name, category = tree.item(item, 'values')
                app_name = next(key for key, value in app_nicknames.items() if value == display_name) if display_name in app_nicknames.values() else display_name
                cursor.execute(
                    "INSERT OR REPLACE INTO classify_app (app_name, category) VALUES (?, ?)",
                    (app_name, category)
                )
            conn.commit()
            conn.close()
            popup.destroy()

        ctk.CTkButton(popup, text="Save", command=save_classifications).pack(pady=10)
        popup.focus_force()
        popup.transient(self.root)
        self.root.wait_window(popup)


    def save_settings_with_theme_and_schedule(self, autosave_var, theme_var, mode_var, afk_detection_var, reminder_var, dynamic_schedule_var, afk_threshold_var, update_ui=False, reopen_settings=False):
        """Save settings, theme, and mode, and apply changes with a restart prompt."""
        self.settings.update("autosave", autosave_var.get())
        self.settings.update("afk_detection", afk_detection_var.get())
        self.settings.update("reminder", reminder_var.get())
        self.settings.update("dynamic_schedule", dynamic_schedule_var.get())
        # Apply AFK detection setting immediately
        if afk_detection_var.get():
            self.app_monitor.start_afk_detection()
        else:
            self.app_monitor.stop_afk_detection()
        
        if theme_var.get() != self.settings.get("theme") or mode_var.get() != self.settings.get("mode"):
            self.settings.update("theme", theme_var.get())
            self.settings.update("mode", mode_var.get())    
            self.settings.save()
            self.show_restart_popup(reopen_settings)
        self.settings.save()
        if afk_threshold_var.get().isdigit():
            self.settings.update("afk_threshold", int(afk_threshold_var.get()))  # Update AFK threshold in settings
            self.app_monitor.afk_threshold = self.settings.get("afk_threshold")  # Update AFK threshold in app monitor

        if update_ui:
            self.apply_settings()

    def apply_settings(self):
        """Apply settings without requiring a restart."""
        self.root.configure(bg=self.settings.get("theme"))
        # Apply other settings as needed
        self.show_dashboard()

    def show_restart_popup(self, reopen_settings):
        """Show a popup window indicating a restart is required."""
        popup = ctk.CTkToplevel(self.root)
        popup.title("Restart Required")
        popup.geometry("300x150")

        # Center the popup window over the main application window
        popup.transient(self.root)
        popup.grab_set()
        # Calculate position to center the popup
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (300 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (150 // 2)
        popup.geometry(f"+{x}+{y}")

        ctk.CTkLabel(popup, text="A restart is required to apply the changes.", font=("Arial", 14)).pack(pady=20)

        button_frame = ctk.CTkFrame(popup)
        button_frame.pack(pady=10)

        ctk.CTkButton(button_frame, text="Restart", command=lambda: [popup.destroy(), self.restart_program(reopen_settings)]).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=popup.destroy).pack(side=ctk.LEFT, padx=5)

        self.root.wait_window(popup)
    
    
    def restart_program(self, reopen_settings):
        """Restart the program."""
        self.root.destroy()
        from main import main
        main()
        if reopen_settings:
            self.open_settings()


    def rename_app(self, old_name, new_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE usage_data SET app_name = ? WHERE app_name = ?", (new_name, old_name))
        except sqlite3.IntegrityError:
            cursor.execute(
                """
                UPDATE usage_data
                SET focus_time = focus_time + (SELECT focus_time FROM usage_data WHERE app_name = ?)
                WHERE app_name = ? AND date IN (SELECT date FROM usage_data WHERE app_name = ?)
                """,
                (old_name, new_name, old_name)
            )
            cursor.execute("DELETE FROM usage_data WHERE app_name = ?", (old_name,))
        cursor.execute("INSERT OR REPLACE INTO app_names (original_name, custom_name) VALUES (?, ?)", (old_name, new_name))
        conn.commit()
        conn.close()
        self.dashboard.display_times()

    def _setup_database(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_data (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                app_name TEXT NOT NULL,
                focus_time REAL NOT NULL,
                UNIQUE(date, app_name)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_names (
                original_name TEXT PRIMARY KEY,
                custom_name TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS classify_app (
                app_name TEXT PRIMARY KEY,
                category TEXT
            )
            """
        )
        # cursor.execute(
        #     """DROP TABLE IF EXISTS schedule_times;"""
        # )
        # cursor.execute(
        #     """DROP TABLE IF EXISTS schedule;"""
        # )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schedule_times (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                next_id INTEGER,
                type TEXT NOT NULL,
                duration INTEGER NOT NULL,
                FOREIGN KEY(next_id) REFERENCES schedule(id)
          )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schedule (
                name TEXT PRIMARY KEY,
                id INTEGER,
                FOREIGN KEY(id) REFERENCES schedule_times(schedule_id)
            )
            """
        )
        conn.commit()
        conn.close()

    def on_close(self):
        if self.settings.get("autosave"):
            self.app_monitor.save_focus_times(self.db_path)
        self.root.destroy()

    def on_minimize(self):
        self.root.withdraw()

    def run(self):
        self.root.mainloop()
