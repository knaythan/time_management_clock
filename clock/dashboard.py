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
        self.viewing_total_times = False  # Track if viewing total times
        self.scheduler_window = None  # Track the scheduler window

    def display(self, parent_frame):
        """Display the dashboard with a tree view of focused app times."""
        self._time_display(parent_frame)
        
        self.tree.bind("<Double-1>", self.edit_name)

        self.button_frame = ctk.CTkFrame(parent_frame)
        self.button_frame.pack(pady=10)

        ctk.CTkButton(self.button_frame, text="Save Times", command=self.save_focus_times).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="View Total Times", command=self.view_total_times).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="Scheduler", command=self.open_scheduler).pack(side=ctk.LEFT, padx=5)

        self.display_times()  # Start periodic updates

    def save_focus_times(self):
        """Save the focus times to the database."""
        self.app_monitor.save_focus_times(self.db_path)
        
    def _time_display(self, parent_frame):
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

    def display_times(self):
        """Update the dashboard tree view with current data."""
        if self.tree is None or not self.tree.winfo_exists():
            return  # Prevent errors if tree is destroyed or doesn't exist

        app_times = self.app_monitor.get_app_times()
        custom_names = self._get_custom_names()
        self.tree.delete(*self.tree.get_children())  # Clear existing data

        for app, time in app_times.items():
            display_name = custom_names.get(app, app)
            human_readable_time = format_time(time)
            self.tree.insert('', 'end', values=(display_name, human_readable_time))

        # Schedule the next update
        self.update_job = self.root.after(1000, self.display_times)

    def _get_custom_names(self):
        """Retrieve custom app names from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT original_name, custom_name FROM app_names")
        custom_names = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return custom_names

    def stop_updates(self):
        """Stop periodic updates when leaving the dashboard."""
        if self.update_job:
            self.root.after_cancel(self.update_job)
            self.update_job = None

    def edit_name(self, event=None):
        """Allow users to rename app names inline."""
        selected_item = self.tree.focus()
        if not selected_item:
            return

        old_name = self.tree.item(selected_item, 'values')[0]
        new_name = ctk.CTkInputDialog(text=f"Rename '{old_name}' to:", title="Rename Application").get_input()
        
        if new_name and new_name.strip():
            new_name = new_name.strip()
            try:
                self.rename_callback(old_name, new_name)
            except sqlite3.IntegrityError:
                self.merge_focus_times(old_name, new_name)
            self.display_times()

    def merge_focus_times(self, old_name, new_name):
        """Merge focus times for the old and new app names."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE usage_data
            SET focus_time = focus_time + (SELECT focus_time FROM usage_data WHERE app_name = ?)
            WHERE app_name = ? AND date IN (SELECT date FROM usage_data WHERE app_name = ?)
        """, (old_name, new_name, old_name))
        cursor.execute("DELETE FROM usage_data WHERE app_name = ?", (old_name,))
        cursor.execute("INSERT OR REPLACE INTO app_names (original_name, custom_name) VALUES (?, ?)", (old_name, new_name))
        conn.commit()
        conn.close()

    def view_total_times(self):
        """Display total time spent on each application in the same tree view."""
        self.stop_updates()  # Stop periodic updates
        self.viewing_total_times = True

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT app_name, SUM(focus_time) FROM usage_data GROUP BY app_name ORDER BY SUM(focus_time) DESC")
        records = cursor.fetchall()
        conn.close()

        self.tree.delete(*self.tree.get_children())  # Clear existing data
        
        for record in records:
            app = record[0]
            time = format_time(record[1])
            self.tree.insert('', 'end', values=(app, time))

        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        # Add new buttons for sorting and exiting
        ctk.CTkButton(self.button_frame, text="Sort Ascending", command=lambda: self.sort_treeview("asc", records)).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="Sort Descending", command=lambda: self.sort_treeview("desc", records)).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="Exit", command=self.exit_total_times_view).pack(side=ctk.LEFT, padx=5)

    def sort_treeview(self, order, records):
        """Sort the tree view based on the total focus time."""
        sorted_records = sorted(records, key=lambda x: x[1], reverse=(order == "desc"))

        self.tree.delete(*self.tree.get_children())  # Clear existing data

        for record in sorted_records:
            app = record[0]
            time = format_time(record[1])
            self.tree.insert('', 'end', values=(app, time))

    def exit_total_times_view(self):
        """Exit the total times view and return to the normal view."""
        self.viewing_total_times = False
        self.display_times()  # Resume periodic updates

        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        # Add original buttons
        ctk.CTkButton(self.button_frame, text="Save Times", command=self.save_focus_times).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="View Total Times", command=self.view_total_times).pack(side=ctk.LEFT, padx=5)

    def open_scheduler(self):
        """Open the scheduler window to manage tasks."""
        if self.scheduler_window is not None and self.scheduler_window.winfo_exists():
            self.scheduler_window.lift()
            return

        self.scheduler_window = ctk.CTkToplevel(self.root)
        self.scheduler_window.title("Task Scheduler")
        self.scheduler_window.geometry("600x400")

        ctk.CTkLabel(self.scheduler_window, text="Task Scheduler", font=("Arial", 16)).pack(pady=10)

        self.task_tree = ttk.Treeview(self.scheduler_window, columns=('Task', 'Expected Duration (min)'), show='headings', selectmode="browse", style="Treeview")
        self.task_tree.heading('Task', text='Task')
        self.task_tree.heading('Expected Duration (min)', text='Expected Duration (min)')
        self.task_tree.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        self.load_tasks()

        button_frame = ctk.CTkFrame(self.scheduler_window)
        button_frame.pack(pady=10)

        ctk.CTkButton(button_frame, text="Add Task", command=self.add_task).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(button_frame, text="Edit Task", command=self.edit_task).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(button_frame, text="Remove Task", command=self.remove_task).pack(side=ctk.LEFT, padx=5)

    def load_tasks(self):
        """Load tasks from the settings and display them in the tree view."""
        self.task_tree.delete(*self.task_tree.get_children())  # Clear existing data

        dynamic_schedule = self.app_monitor.settings.get_dynamic_schedule()
        tasks = dynamic_schedule.get('tasks', {})

        for task, settings in tasks.items():
            expected_duration = settings.get('expected_duration', 25)
            self.task_tree.insert('', 'end', values=(task, expected_duration))

    def add_task(self):
        """Add a new task to the scheduler."""
        task_name = ctk.CTkInputDialog(text="Enter task name:", title="Add Task").get_input()
        if task_name and task_name.strip():
            task_name = task_name.strip()
            expected_duration = ctk.CTkInputDialog(text="Enter expected duration (minutes):", title="Add Task").get_input()
            if expected_duration and expected_duration.isdigit():
                expected_duration = int(expected_duration)
                dynamic_schedule = self.app_monitor.settings.get_dynamic_schedule()
                if 'tasks' not in dynamic_schedule:
                    dynamic_schedule['tasks'] = {}
                dynamic_schedule['tasks'][task_name] = {'expected_duration': expected_duration}
                self.app_monitor.settings.update_dynamic_schedule('tasks', dynamic_schedule['tasks'])
                self.load_tasks()

    def edit_task(self):
        """Edit the selected task in the scheduler."""
        selected_item = self.task_tree.focus()
        if not selected_item:
            return

        task_name = self.task_tree.item(selected_item, 'values')[0]
        new_task_name = ctk.CTkInputDialog(text=f"Rename '{task_name}' to:", title="Edit Task").get_input()
        if new_task_name and new_task_name.strip():
            new_task_name = new_task_name.strip()
            expected_duration = ctk.CTkInputDialog(text="Enter expected duration (minutes):", title="Edit Task").get_input()
            if expected_duration and expected_duration.isdigit():
                expected_duration = int(expected_duration)
                dynamic_schedule = self.app_monitor.settings.get_dynamic_schedule()
                if 'tasks' in dynamic_schedule:
                    dynamic_schedule['tasks'].pop(task_name, None)
                    dynamic_schedule['tasks'][new_task_name] = {'expected_duration': expected_duration}
                    self.app_monitor.settings.update_dynamic_schedule('tasks', dynamic_schedule['tasks'])
                    self.load_tasks()

    def remove_task(self):
        """Remove the selected task from the scheduler."""
        selected_item = self.task_tree.focus()
        if not selected_item:
            return

        task_name = self.task_tree.item(selected_item, 'values')[0]
        dynamic_schedule = self.app_monitor.settings.get_dynamic_schedule()
        if 'tasks' in dynamic_schedule:
            dynamic_schedule['tasks'].pop(task_name, None)
            self.app_monitor.settings.update_dynamic_schedule('tasks', dynamic_schedule['tasks'])
            self.load_tasks()

def format_time(seconds):
    """Convert time in seconds to a human-readable format."""
    sec = int(seconds)
    if sec < 60:
        return f"{sec} s"
    elif sec < 3600:
        minutes = sec // 60
        return f"{minutes} min"
    elif sec < 86400:
        hours = sec // 3600
        return f"{hours} hrs"
    else:
        days = sec // 86400
        return f"{days} days"