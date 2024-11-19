# clock/dashboard.py
import tkinter as tk
from tkinter import ttk

class ProductivityDashboard:
    def __init__(self, root, app_monitor):
        self.root = root
        self.app_monitor = app_monitor
        self.tree = None

    def display(self, parent_frame):
        """Display a tree view of focused application times."""
        self.tree = ttk.Treeview(parent_frame, columns=('App', 'Time (s)'), show='headings')
        self.tree.heading('App', text='Application')
        self.tree.heading('Time (s)', text='Focus Time (s)')
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.update_dashboard()

    def update_dashboard(self):
        """Update the dashboard table with real-time app usage data."""
        self.tree.delete(*self.tree.get_children())  # Clear the tree view

        app_times = self.app_monitor.get_app_times()
        for app, time in app_times.items():
            self.tree.insert('', 'end', values=(app, time))

        # Schedule updates every second
        self.root.after(1000, self.update_dashboard)
