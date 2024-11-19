import tkinter as tk
from tkinter import ttk, simpledialog

class ProductivityDashboard:
    def __init__(self, root, app_monitor, rename_callback):
        self.root = root
        self.app_monitor = app_monitor
        self.tree = None
        self.rename_callback = rename_callback
        self.update_job = None  # To track scheduled updates

    def display(self, parent_frame):
        """Display the dashboard with a tree view of focused app times."""
        self.tree = ttk.Treeview(parent_frame, columns=('App', 'Time (s)'), show='headings', selectmode="browse")
        self.tree.heading('App', text='Application')
        self.tree.heading('Time (s)', text='Focus Time (s)')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree.bind("<Double-1>", self.edit_name)
        self.update_dashboard()  # Start periodic updates

    def update_dashboard(self):
        """Update the dashboard tree view with current data."""
        if self.tree is None:
            return  # Prevent errors if tree is destroyed

        app_times = self.app_monitor.get_app_times()
        self.tree.delete(*self.tree.get_children())  # Clear existing data

        for app, time in app_times.items():
            self.tree.insert('', 'end', values=(app, time))

        # Schedule the next update
        self.update_job = self.root.after(1000, self.update_dashboard)

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
        new_name = simpledialog.askstring("Rename Application", f"Rename '{old_name}' to:")
        
        if new_name and new_name.strip():
            new_name = new_name.strip()
            self.rename_callback(old_name, new_name)
            self.update_dashboard()