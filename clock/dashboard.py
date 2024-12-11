import customtkinter as ctk
from tkinter import ttk
import sqlite3

class ProductivityDashboard:
    def __init__(self, root, app_monitor, rename_callback, db_path):
        self.root = root
        self.app_monitor = app_monitor
        self.tree = None
        self.rename_callback = rename_callback
        self.update_job = None  # To track scheduled updates
        self.db_path = db_path  # Add db_path attribute

    def display(self, parent_frame):
        """Display the dashboard with a tree view of focused app times."""
        style = ttk.Style()
        style.theme_use("clam")  # Use a theme that allows customization
        style.configure("Treeview", 
                        background="#333333", 
                        foreground="white", 
                        fieldbackground="#333333", 
                        font=("Arial", 12),
                        borderwidth=0,  # Remove border
                        highlightthickness=0)  # Remove highlight border
        style.configure("Treeview.Heading", 
                        background="#444444", 
                        foreground="white", 
                        font=("Arial", 12, "bold"))
        style.map('Treeview', background=[('selected', '#555555')], foreground=[('selected', 'grey')])

        parent_frame.configure(bg="#222222")  # Set background color of parent frame

        self.tree = ttk.Treeview(parent_frame, columns=('App', 'Time (s)'), show='headings', selectmode="browse", style="Treeview")
        self.tree.heading('App', text='Application')
        self.tree.heading('Time (s)', text='Focus Time (s)')
        self.tree.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        self.tree.bind("<Double-1>", self.edit_name)

        button_frame = ctk.CTkFrame(parent_frame)
        button_frame.pack(pady=10)

        ctk.CTkButton(button_frame, text="Save Times", command=self.save_focus_times).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(button_frame, text="View Past Times", command=self.view_past_times).pack(side=ctk.LEFT, padx=5)

        self.update_dashboard()  # Start periodic updates

    def save_focus_times(self):
        """Save the focus times to the database."""
        self.app_monitor.save_focus_times(self.db_path)

    def update_dashboard(self):
        """Update the dashboard tree view with current data."""
        if self.tree is None:
            return  # Prevent errors if tree is destroyed

        app_times = self.app_monitor.get_app_times()
        self.tree.delete(*self.tree.get_children())  # Clear existing data

        for app, time in app_times.items():
            human_readable_time = self._format_time(time)
            self.tree.insert('', 'end', values=(app, human_readable_time))

        # Schedule the next update
        self.update_job = self.root.after(1000, self.update_dashboard)

    def _format_time(self, seconds):
        """Convert time in seconds to a human-readable format."""
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minutes"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hours"
        else:
            days = seconds // 86400
            return f"{days} days"

    def stop_updates(self):
        """Stop periodic updates when leaving the dashboard."""
        if self.update_job:
            self.root.after_cancel(self.update_job)
            self.update_job = None

    def edit_name(self, event):
        """Allow users to rename app names inline."""
        selected_item = self.tree.focus()
        if not selected_item:
            return

        old_name = self.tree.item(selected_item, 'values')[0]
        new_name = ctk.CTkInputDialog(text=f"Rename '{old_name}' to:", title="Rename Application").get_input()
        
        if new_name and new_name.strip():
            new_name = new_name.strip()
            self.rename_callback(old_name, new_name)
            self.update_dashboard()

    def view_past_times(self):
        """Display past application times."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT date, app_name, focus_time FROM usage_data ORDER BY date DESC")
        records = cursor.fetchall()
        conn.close()

        past_times_window = ctk.CTkToplevel(self.root)
        past_times_window.title("Past Application Times")
        past_times_window.geometry("600x400")

        tree = ttk.Treeview(past_times_window, columns=('Date', 'App', 'Time (s)'), show='headings')
        tree.heading('Date', text='Date')
        tree.heading('App', text='Application')
        tree.heading('Time (s)', text='Focus Time (s)')
        tree.pack(fill=ctk.BOTH, expand=True)

        for record in records:
            tree.insert('', 'end', values=record)