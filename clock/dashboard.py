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
        self.schedule_name = None

    def display(self):
        """Display the dashboard with a tree view of focused app times."""
        ctk.CTkLabel(self.root, text="Dashboard", font=("Arial", 16)).pack(pady=10)
        self._time_display()
        
        self.tree.bind("<Double-1>", self.edit_name)

        self.button_frame = ctk.CTkFrame(self.root)
        self.button_frame.pack(pady=10)

        ctk.CTkButton(self.button_frame, text="Save Times", command=self.save_focus_times).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="View Total Times", command=self.view_total_times).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="Scheduler", command=self.open_scheduler).pack(side=ctk.LEFT, padx=5)

        self.display_times()  # Start periodic updates

    def save_focus_times(self):
        """Save the focus times to the database."""
        self.app_monitor.save_focus_times(self.db_path)
        
    def _time_display(self):
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

        self.root.configure(bg="#222222")  # Set background color of parent frame

        self.tree = ttk.Treeview(self.root, columns=('App', 'Time (s)'), show='headings', selectmode="browse", style="Treeview")
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

        # Change the label to "Total Times"
        for widget in self.root.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "Dashboard":
                widget.configure(text="Total Times")
                break

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

        # Change the label back to "Dashboard"
        for widget in self.root.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "Total Times":
                widget.configure(text="Dashboard")
                break

        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        # Add original buttons
        ctk.CTkButton(self.button_frame, text="Save Times", command=self.save_focus_times).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="View Total Times", command=self.view_total_times).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="Scheduler", command=self.open_scheduler).pack(side=ctk.LEFT, padx=5)

    def open_scheduler(self):
        """Open the scheduler window to manage tasks."""
        self.stop_updates()  # Stop periodic updates

        # Change the label to "Scheduler"
        for widget in self.root.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "Dashboard":
                widget.configure(text="Scheduler")
                break

        self.tree.delete(*self.tree.get_children())  # Clear existing data

        # Retrieve all schedules from the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM schedule")
        schedules = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        """Add a new task to the scheduler."""
        # Create a new window for task input
        input_window = ctk.CTkToplevel(self.root)
        input_window.geometry("300x200")

        # Center the window on the screen
        input_window.update_idletasks()
        width = input_window.winfo_width()
        height = input_window.winfo_height()
        x = (input_window.winfo_screenwidth() // 2) - (width // 2)
        y = (input_window.winfo_screenheight() // 2) - (height // 2)
        input_window.geometry(f'{width}x{height}+{x}+{y}')

        # Focus on the window
        input_window.focus_force()

        # Schedule dropdown
        ctk.CTkLabel(input_window, text="Select Schedule:").pack(pady=5)
        schedule_name = ctk.StringVar(value=schedules[0])  # Default to the first schedule
        schedule_dropdown = ctk.CTkOptionMenu(
            input_window,
            values=schedules,
            variable=schedule_name
        )
        schedule_dropdown.pack(pady=5)

        def submit_schedule():
            self.schedule_name = schedule_name.get()
            input_window.destroy()  # Close the input window after submission
            self.load_selected_schedule(self.schedule_name)  # Load the selected schedule

        # Submit button
        ctk.CTkButton(input_window, text="Submit", command=submit_schedule).pack(pady=10)

        if schedules:
            for schedule in schedules:
                self.tree.insert('', 'end', values=(schedule,))
        ctk.CTkButton(self.button_frame, text="Add Task", command=self.add_task).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="Edit Task", command=self.edit_task).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="Remove Task", command=self.remove_task).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="Exit", command=self.exit_task_view).pack(side=ctk.LEFT, padx=5)
        # Create a dropdown menu to select schedules
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM schedule")
        schedules = [row[0] for row in cursor.fetchall()]
        conn.close()

        
        
    def exit_task_view(self):
        """Exit the scheduler view and return to the normal view."""
        self.display_times()
        self.schedule_name = None  # Reset the active schedule name
        
        # Change the label back to "Dashboard"
        for widget in self.root.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "Scheduler":
                widget.configure(text="Dashboard")
                break
            
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
            
        # Add original buttons
        ctk.CTkButton(self.button_frame, text="Save Times", command=self.save_focus_times).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="View Total Times", command=self.view_total_times).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="Scheduler", command=self.open_scheduler).pack(side=ctk.LEFT, padx=5)
        
    def edit_task(self):
        """Edit the selected task in the scheduler."""
        selected_item = self.tree.focus()
        if not selected_item:
            return

        task_name = self.tree.item(selected_item, 'values')[0]
        new_name = ctk.CTkInputDialog(text="Enter new task name:", title="Edit Task").get_input()
        if new_name and new_name.strip():
            new_name = new_name.strip()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE schedule_times
                SET type = ?
                WHERE type = ? AND id = (
                    SELECT id FROM schedule WHERE name = ?
                )
            """, (new_name, task_name, self.schedule_name))
            conn.commit()
            conn.close()
            self.load_tasks()

    def get_dynamic_schedule(self, name):
        """Retrieve the dynamic schedule settings."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM schedule WHERE name = ?", (name,))
        data = cursor.fetchone()
        if not data:
            conn.close()
            return []

        next_id = data[0]
        schedule_items = []
        while next_id:
            cursor.execute("SELECT type, duration, next_id FROM schedule_times WHERE id = ?", (next_id,))
            row = cursor.fetchone()
            if not row:
                break
            schedule_items.append((row[0], row[1]))  # Append (type, duration)
            next_id = row[2]
        conn.close()
        return schedule_items

    def load_selected_schedule(self, selected_schedule):
        """Load the selected schedule from the dropdown."""
        if selected_schedule:
            self.schedule_name = selected_schedule  # Set the active schedule name
            self.tree.delete(*self.tree.get_children())  # Clear existing data
            dynamic_schedule = self.get_dynamic_schedule(self.schedule_name)
            for slot in dynamic_schedule:
                expected_duration = slot[1]
                self.tree.insert('', 'end', values=(slot[0], expected_duration))


    def add_task(self):
        """Add a new task to the scheduler."""
        # Create a new window for task input
        input_window = ctk.CTkToplevel(self.root)
        input_window.title("Add Task")
        input_window.geometry("400x400")

        # Center the window on the screen
        input_window.update_idletasks()
        width = input_window.winfo_width()
        height = input_window.winfo_height()
        x = (input_window.winfo_screenwidth() // 2) - (width // 2)
        y = (input_window.winfo_screenheight() // 2) - (height // 2)
        input_window.geometry(f'{width}x{height}+{x}+{y}')

        # Focus on the window
        input_window.focus_force()

        # Task name input
        ctk.CTkLabel(input_window, text="Enter task name:").pack(pady=5)
        task_name_entry = ctk.CTkEntry(input_window)
        task_name_entry.pack(pady=5)

        # Task type dropdown
        ctk.CTkLabel(input_window, text="Select Type:").pack(pady=5)
        type_check = ctk.StringVar(value="PRODUCTIVE")
        type_dropdown = ctk.CTkOptionMenu(
            input_window,
            values=["NONPRODUCTIVE", "PRODUCTIVE"],
            variable=type_check
        )
        type_dropdown.pack(pady=5)

        # Expected duration input
        ctk.CTkLabel(input_window, text="Enter expected duration (minutes):").pack(pady=5)
        duration_entry = ctk.CTkEntry(input_window)
        duration_entry.pack(pady=5)

        def submit_task():
            task_name = task_name_entry.get().strip()
            task_type = type_check.get()
            self.schedule_name = task_name
            expected_duration = duration_entry.get().strip()

            if task_name and expected_duration.isdigit():
                expected_duration = int(expected_duration)
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM schedule WHERE name = ?", (self.schedule_name,))
                schedule_id = cursor.fetchone()
            if not schedule_id:
                # Insert a new schedule if it doesn't exist
                cursor.execute("INSERT INTO schedule_times (next_id, type, duration) VALUES (NULL, ?, ?)", (task_type, expected_duration))
                schedule_id = cursor.lastrowid
                print(self.schedule_name)
                cursor.execute("INSERT INTO schedule (name, id) VALUES (?, ?)", (self.schedule_name, schedule_id,))
                conn.commit()
            else:
                schedule_id = schedule_id[0]
                has_next = True
                while has_next:
                    cursor.execute("SELECT next_id FROM schedule_times WHERE id = ?", (schedule_id,))
                    next_id = cursor.fetchone()
                    if not next_id[0]:
                        has_next = False
                    else:
                        schedule_id = next_id[0]
                cursor.execute("INSERT INTO schedule_times (next_id, type, duration) VALUES (NULL, ?, ?)", (task_type, expected_duration))
                new_id = cursor.lastrowid
                cursor.execute("UPDATE schedule_times SET next_id = ? WHERE id = ?", (new_id, schedule_id))
                conn.commit()
            conn.close()
            input_window.destroy()  # Close the input window after submission

        # Submit button
        ctk.CTkButton(input_window, text="Submit", command=submit_task).pack(pady=10)

    def remove_task(self):
        """Remove the selected task from the scheduler."""
        selected_item = self.tree.focus()
        if not selected_item:
            return

        task_name = self.tree.item(selected_item, 'values')[0]
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM schedule_times 
            WHERE type = ? AND id = (
                SELECT id FROM schedule WHERE name = ?
            )
        """, (task_name, self.schedule_name))
        conn.commit()
        conn.close()
        self.load_tasks()
        
    def view_tasks(self):
        """Create a dropdown menu to view and select user-created schedules."""
        self.stop_updates()  # Stop periodic updates

        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        # Retrieve all schedules from the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM schedule")
        schedules = [row[0] for row in cursor.fetchall()]
        conn.close()

        if schedules:
            # Pre-select the first schedule if no schedule is set
            if not self.schedule_name:
                self.schedule_name = schedules[0]

            self.schedule_var = ctk.StringVar(value=self.schedule_name)  # Default to the current schedule
            self.schedule_dropdown = ctk.CTkOptionMenu(
                self.button_frame,
                variable=self.schedule_var,
                values=schedules,
                command=self.load_selected_schedule  # Load the schedule when selected
            )
            self.schedule_dropdown.pack(side=ctk.LEFT, padx=5)

            # Automatically load the pre-selected schedule
            self.load_selected_schedule(self.schedule_name)
        else:
            # No schedules available, prompt the user to create one
            ctk.CTkLabel(self.button_frame, text="No schedules available").pack(side=ctk.LEFT, padx=5)
        # Add buttons for exiting the task view
        ctk.CTkButton(self.button_frame, text="Exit", command=self.exit_task_view).pack(side=ctk.LEFT, padx=5)


            


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