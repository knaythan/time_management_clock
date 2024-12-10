import customtkinter as ctk
from tkinter import ttk

class ProductivityDashboard:
    def __init__(self, root, app_monitor, rename_callback):
        self.root = root
        self.app_monitor = app_monitor
        self.tree = None
        self.rename_callback = rename_callback
        self.update_job = None  # To track scheduled updates

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
        new_name = ctk.CTkInputDialog(text=f"Rename '{old_name}' to:", title="Rename Application").get_input()
        
        if new_name and new_name.strip():
            new_name = new_name.strip()
            self.rename_callback(old_name, new_name)
            self.update_dashboard()