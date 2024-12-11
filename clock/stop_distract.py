import tkinter as tk
from tkinter import messagebox
import time
import threading
from app_monitor import AppMonitor

class StopDistract:
    def __init__(self, status, response_type, app_monitor):
        self.status = status
        self.response_type = response_type
        self.app_monitor = app_monitor
        if self.status == "UNPRODUCTIVE":
            self.trigger_response()

    def trigger_response(self):
        if self.response_type == 1:
            self.show_popup("You are off task!")
        elif self.response_type == 2:
            self.show_popup_with_cancel("You have 5 seconds until unproductive apps are minimized.")
        elif self.response_type == 3:
            self.show_popup_no_cancel("You have 5 seconds until unproductive apps are minimized.")

    def show_popup(self, message):
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Alert", message)
        root.destroy()

    def show_popup_with_cancel(self, message):
        def on_cancel():
            nonlocal cancel
            cancel = True
            root.destroy()

        cancel = False
        root = tk.Tk()
        root.withdraw()
        popup = tk.Toplevel(root)
        popup.title("Alert")
        tk.Label(popup, text=message).pack()
        cancel_button = tk.Button(popup, text="Cancel", command=on_cancel)
        cancel_button.pack()
        root.update()
        root.deiconify()

        def countdown():
            nonlocal cancel
            for i in range(5, 0, -1):
                if cancel:
                    break
                time.sleep(1)
            if not cancel:
                self.app_monitor.start_minimize()

        threading.Thread(target=countdown).start()
        root.mainloop()

    def show_popup_no_cancel(self, message):
        root = tk.Tk()
        root.withdraw()
        popup = tk.Toplevel(root)
        popup.title("Alert")
        tk.Label(popup, text=message).pack()
        root.update()
        root.deiconify()

        def countdown():
            for i in range(5, 0, -1):
                time.sleep(1)
            self.app_monitor.start_minimize()

        threading.Thread(target=countdown).start()
        root.mainloop()