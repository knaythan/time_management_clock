import customtkinter as ctk
from tkinter import ttk
import sqlite3
from utils import show_ok_popup, format_time

class ProductivityDashboard:
    def __init__(self, root, app_monitor, rename_callback, db_path, stop_distract):
        self.root = root
        self.app_monitor = app_monitor
        self.stop_distract = stop_distract
        self.tree = None
        self.rename_callback = rename_callback
        self.update_job = None  # To track scheduled updates
        self.db_path = db_path  # Add db_path attribute
        self.viewing_total_times = False  # Track if viewing total times
        self.schedules = []  # Track all schedules
        self.schedule = None  # Track the scheduler window
        self.schedule_name = None

    def display(self):
        """Display the dashboard with a tree view of focused app times."""
        ctk.CTkLabel(self.root, text="Dashboard", font=("Arial", 16)).pack(pady=10)
        self._time_display()
        
        self.tree.bind("<Double-1>", self.edit_name)

        self.button_frame = ctk.CTkFrame(self.root)
        self.button_frame.pack(pady=10)
        
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(self.button_frame, text="Save Times", command=self.save_focus_times).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="View Total Times", command=self.view_total_times).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="Scheduler", command=self.open_scheduler).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

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
            
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)

        # Add new buttons for sorting and exiting
        ctk.CTkButton(self.button_frame, text="Sort Ascending", command=lambda: self.sort_treeview("asc", records)).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="Sort Descending", command=lambda: self.sort_treeview("desc", records)).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="Exit", command=self.exit_total_times_view).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

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
            
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)

        # Add original buttons
        ctk.CTkButton(self.button_frame, text="Save Times", command=self.save_focus_times).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="View Total Times", command=self.view_total_times).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="Scheduler", command=self.open_scheduler).grid(row=0, column=2, padx=5, pady=5, sticky="ew")

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
        
        self.schedules = schedules

        if schedules:
            self.load_selected_schedule(self.schedule_name)

        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()

        # Add buttons for managing tasks
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)
        self.button_frame.grid_columnconfigure(3, weight=1)
        self.button_frame.grid_columnconfigure(4, weight=1)
        self.button_frame.grid_columnconfigure(5, weight=1)
        self.button_frame.grid_columnconfigure(6, weight=1)

        ctk.CTkButton(self.button_frame, text="Add Task", command=self.add_task).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="Edit Task", command=self.edit_task).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="Remove Task", command=self.remove_task).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="Exit", command=self.exit_task_view).grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="Select Schedule", command=self.select_schedule).grid(row=0, column=4, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="Start", command=self.start_schedule).grid(row=0, column=5, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="Finish", command=self.finish_task_early).grid(row=0, column=6, padx=5, pady=5, sticky="ew")
        
    def select_schedule(self):
        # Create a new window for schedule selection
        input_window = ctk.CTkToplevel(self.root)
        input_window.title("Select Schedule")

        # Center the window on the screen
        input_window.update_idletasks()
        width = 300
        height = 300

        x = (self.root.winfo_width() // 2) - (width // 2)
        y = (self.root.winfo_height() // 2) - (height // 2)

        input_window.geometry(f'{width}x{height}+{x}+{y}')

        # Focus on the window
        input_window.focus_force()
        input_window.transient(self.root)
        
        schedules = self.schedules

        # Schedule dropdown
        ctk.CTkLabel(input_window, text="Select Schedule:").pack(pady=5)
        schedule_name = ctk.StringVar(value=schedules[0] if schedules else "")
        schedule_dropdown = ctk.CTkOptionMenu(
            input_window,
            values=schedules,
            variable=schedule_name
        )
        schedule_dropdown.pack(pady=5)

        def submit_schedule():
            input_window.destroy()  # Close the input window after submission
            for widget in self.root.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text") == "Scheduler":
                    widget.configure(text=schedule_name.get() + " Schedule")
            self.load_selected_schedule(schedule_name.get())  # Load the selected schedule

        # Submit button
        ctk.CTkButton(input_window, text="Submit", command=submit_schedule).pack(pady=10)

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
            
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)
            
        # Add original buttons
        ctk.CTkButton(self.button_frame, text="Save Times", command=self.save_focus_times).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="View Total Times", command=self.view_total_times).pack(side=ctk.LEFT, padx=5)
        ctk.CTkButton(self.button_frame, text="Scheduler", command=self.open_scheduler).pack(side=ctk.LEFT, padx=5)
        
    def edit_task(self):
        """Edit the selected task in the scheduler."""
        selected_item = self.tree.focus()
        if not selected_item:
            return

        item_tags = self.tree.item(selected_item, 'tags')
        if not item_tags:
            return

        task_id = item_tags[0]

        # Task type dropdown
        input_window = ctk.CTkToplevel(self.root)
        input_window.title("Edit Task")

        # Center the window on the screen
        input_window.update_idletasks()
        width = 300
        height = 300
        
        x = (self.root.winfo_width() // 2) - (width // 2)
        y = (self.root.winfo_height() // 2) - (height // 2)

        input_window.geometry(f'{width}x{height}+{x}+{y}')

        # Focus on the window
        input_window.focus_force()
        input_window.transient(self.root)
        
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
        
        def submit_edit():
            try:
                duration = float(duration_entry.get().strip())
                if duration <= 0:
                    raise ValueError("Duration must be greater than 0")
            except ValueError as e:
                ctk.CTkMessageBox.show_error("Invalid Input", str(e))
                return
            task_type = type_check.get()
            if duration:
                self.update_task(task_id, task_type, float(duration) * 60)
            else:
                self.update_task(task_id, task_type, None)
            input_window.destroy()
            
        ctk.CTkButton(input_window, text="Submit", command=submit_edit).pack(pady=10)
        
    def update_task(self, task_id, task_type, duration):
        """Update the task in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if duration is not None:
            cursor.execute("""
                UPDATE schedule_times
                SET type = ?, duration = ?
                WHERE id = ?
            """, (task_type, duration, task_id))
        else:
            cursor.execute("""
                UPDATE schedule_times
                SET type = ?
                WHERE id = ?
            """, (task_type, task_id))
        conn.commit()
        conn.close()
        self.load_selected_schedule(self.schedule_name)

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
            cursor.execute("SELECT type, duration, id, next_id FROM schedule_times WHERE id = ?", (next_id,))
            row = cursor.fetchone()
            if not row:
                break
            schedule_items.append((row[0], row[1], row[2]))  # Append (type, duration)
            next_id = row[3]
        conn.close()
        return schedule_items

    def load_selected_schedule(self, selected_schedule):
        """Load the selected schedule from the dropdown."""
        if selected_schedule:
            self.schedule_name = selected_schedule  # Set the active schedule name
            self.tree.delete(*self.tree.get_children())  # Clear existing data
            dynamic_schedule = self.get_dynamic_schedule(self.schedule_name)
            self.schedule = dynamic_schedule
            for slot in dynamic_schedule:
                expected_duration = format_time(slot[1])
                self.tree.insert('', 'end', values=(slot[0], expected_duration), tags=(slot[2],))

            self.tree.tag_bind('all', '<ButtonRelease-1>', self.on_task_click)

    def on_task_click(self, event):
        """Handle task click event to access the hidden id."""
        selected_item = self.tree.focus()
        if not selected_item:
            return

        item_tags = self.tree.item(selected_item, 'tags')
        if item_tags:
            task_id = item_tags[0]
            print(f"Task ID: {task_id}")

    def add_task(self):
        """Add a new task to the scheduler."""
        # Create a new window for task input
        input_window = ctk.CTkToplevel(self.root)
        input_window.title("Add Task")

        # Center the window on the screen
        input_window.update_idletasks()
        width = 300
        height = 300
        
        x = (self.root.winfo_width() // 2) - (width // 2)
        y = (self.root.winfo_height() // 2) - (height // 2)

        input_window.geometry(f'{width}x{height}+{x}+{y}')

        # Focus on the window
        input_window.focus_force()
        input_window.transient(self.root)

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
            try:
                expected_duration = float(duration_entry.get().strip())
                if expected_duration <= 0:
                    raise ValueError("Duration must be greater than 0")
            except ValueError as e:
                ctk.CTkMessageBox.show_error("Invalid Input", str(e))
                return

            if task_name and expected_duration:
                expected_duration = float(expected_duration) * 60
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM schedule WHERE name = ?", (self.schedule_name,))
                schedule_id = cursor.fetchone()
                if not schedule_id:
                    # Insert a new schedule if it doesn't exist
                    cursor.execute("INSERT INTO schedule_times (next_id, type, duration) VALUES (NULL, ?, ?)", (task_type, expected_duration))
                    schedule_id = cursor.lastrowid
                    cursor.execute("INSERT INTO schedule (name, id) VALUES (?, ?)", (self.schedule_name, schedule_id,))
                    conn.commit()
                else:
                    schedule_id = schedule_id[0]
                    has_next = True
                    while has_next:
                        cursor.execute("SELECT next_id FROM schedule_times WHERE id = ?", (schedule_id,))
                        next_id = cursor.fetchone()
                        if not next_id:
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
        selected_item = self.tree.focus()
        if not selected_item:
            return

        task_id = self.tree.item(selected_item, 'tags')[0]

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Find the previous task that references this task
        cursor.execute("SELECT id FROM schedule_times WHERE next_id = ?", (task_id,))
        previous_task = cursor.fetchone()

        # Find the next task that this task references
        cursor.execute("SELECT next_id FROM schedule_times WHERE id = ?", (task_id,))
        next_task = cursor.fetchone()

        # Check if the task being deleted is the one referenced by the schedule name
        cursor.execute("SELECT id FROM schedule WHERE name = ?", (self.schedule_name,))
        schedule_id = cursor.fetchone()

        if schedule_id and schedule_id[0] == task_id:
            if next_task:
                # Update the schedule to reference the next task
                cursor.execute("UPDATE schedule SET id = ? WHERE name = ?", (next_task[0], self.schedule_name))
            else:
                # If there is no next task, delete the schedule
                cursor.execute("DELETE FROM schedule WHERE name = ?", (self.schedule_name,))

        # Delete the selected task
        cursor.execute("DELETE FROM schedule_times WHERE id = ?", (task_id,))

        if previous_task:
            if next_task:
                # Update the previous task to reference the next task
                cursor.execute("UPDATE schedule_times SET next_id = ? WHERE id = ?", (next_task[0], previous_task[0]))
            else:
                # If there is no next task, set the next_id of the previous task to NULL
                cursor.execute("UPDATE schedule_times SET next_id = NULL WHERE id = ?", (previous_task[0],))

        conn.commit()
        conn.close()

        self.load_selected_schedule(self.schedule_name)
        
    def start_schedule(self):
        """Start the schedule countdown."""
        if not self.schedule:
            return

        self.current_task_index = 0
        self.stop_distract.start()
        self.run_task()

    def run_task(self):
        """Run the current task in the schedule."""
        if self.current_task_index >= len(self.schedule):
            title = "Schedule Complete"
            message = "You have gone through all scheduled times."
            self.stop_distract.stop()

            # Wait for the user to click the OK button before continuing
            show_ok_popup(self.root, message, title=title)
            
            self.current_task_index = None
            self.load_selected_schedule(self.schedule_name)
            
            return
        
        self.stop_distract.status = self.schedule[self.current_task_index][0]
        self.stop_distract.changed = True

        task_type, duration, task_id = self.schedule[self.current_task_index]
        self.current_task_index += 1

        self.tree.delete(*self.tree.get_children())  # Clear existing data
        self.tree.insert('', 'end', values=(task_type, format_time(duration)))

        self.countdown(duration)

    def countdown(self, remaining_time):
        """Countdown timer for the current task."""
        if remaining_time <= 0:
            if self.current_task_index > 0 and self.current_task_index < len(self.schedule):
                previous_task_type = self.schedule[self.current_task_index - 1][0]
                current_task_type = self.schedule[self.current_task_index][0]
            else:
                self.run_task()
                return

            # Display the appropriate message
            if previous_task_type == "NONPRODUCTIVE" and current_task_type == "PRODUCTIVE":
                message = "Time to get to work!"
            elif previous_task_type == "PRODUCTIVE" and current_task_type == "NONPRODUCTIVE":
                message = "Time to get some rest!"
            else:
                message = "Task transition"

            # Wait for the user to click the OK button before continuing
            show_ok_popup(self.root, message, title="Task Complete", ok_text="Next Task")
            self.run_task()  # Move to the next task
            return

        self.tree.item(self.tree.get_children()[0], values=(self.tree.item(self.tree.get_children()[0], 'values')[0], format_time(remaining_time)))
        self.update_job = self.root.after(1000, self.countdown, remaining_time - 1)

    def finish_task_early(self):
        """Finish the current task early and move to the next one."""
        if self.update_job:
            self.root.after_cancel(self.update_job)
            self.run_task()