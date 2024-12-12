import tkinter as tk
from tkinter import messagebox
import time
import threading

class StopDistract:
    def __init__(self, dashboard, response_type, app_monitor):
        self.dashboard = dashboard
        self.response_type = response_type
        self.app_monitor = app_monitor
        self.popup_displayed = False
        self.check_thread = threading.Thread(target=self.check_response, daemon=True)
        self.check_thread.start()
        
    def check_response(self):
        while True:
            if self.dashboard.status == "PRODUCTIVE":
                if self.app_monitor.category == "NONPRODUCTIVE" and not self.popup_displayed:
                    self.trigger_response()
            time.sleep(1)  # Add a small delay to prevent high CPU usage
        
    def trigger_response(self):
        self.popup_displayed = True
        if self.response_type == "low":
            self.show_popup("You are off task!")
        elif self.response_type == "medium":
            self.show_popup_with_cancel("You have 5 seconds until unproductive apps are minimized.")
        elif self.response_type == "high":
            self.show_popup_no_cancel("You have 5 seconds until unproductive apps are minimized.")

    def show_popup(self, message):
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Alert", message)
        root.destroy()
        self.popup_displayed = False

    def show_popup_with_cancel(self, message):
        def on_cancel():
            nonlocal cancel
            cancel = True
            root.destroy()
            self.popup_displayed = False

        cancel = False
        root = tk.Tk()
        root.withdraw()
        popup = tk.Toplevel(root)
        popup.title("Alert")
        popup.geometry("300x100")
        popup.resizable(False, False)
        tk.Label(popup, text=message, padx=10, pady=10).pack()
        cancel_button = tk.Button(popup, text="Cancel", command=on_cancel)
        cancel_button.pack(pady=5)
        popup.transient(root)
        popup.grab_set()
        root.update()
        root.deiconify()

        def countdown():
            nonlocal cancel
            for _ in range(5, 0, -1):
                time.sleep(1)
            if not cancel:
                self.app_monitor.start_minimize()
            self.popup_displayed = False

        threading.Thread(target=countdown).start()
        root.mainloop()

    def show_popup_no_cancel(self, message):
        root = tk.Tk()
        root.withdraw()
        popup = tk.Toplevel(root)
        popup.title("Alert")
        popup.geometry("300x100")
        popup.resizable(False, False)
        tk.Label(popup, text=message, padx=10, pady=10).pack()
        popup.transient(root)
        popup.grab_set()
        root.update()
        root.deiconify()

        def countdown():
            for i in range(5, 0, -1):
                time.sleep(1)
            self.app_monitor.start_minimize()
            self.popup_displayed = False

        threading.Thread(target=countdown).start()
        root.mainloop()
