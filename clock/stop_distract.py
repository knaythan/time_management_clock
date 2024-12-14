import customtkinter as ctk
import time
from threading import Thread
from utils import show_ok_popup, show_ok_popup_with_cancel

class StopDistract:
    def __init__(self, root, response_type, app_monitor):
        self.response_type = response_type
        self.app_monitor = app_monitor
        self.root = root
        self.popup_displayed = False
        self.check = False
        self.status = None
        self.changed = False
        
    def start(self):
        self.check = True
        Thread(target=self.check_response).start()
        
    def stop(self):
        self.status = None
        self.check = False
        
    def check_response(self):
        while self.check:
            if self.status == "PRODUCTIVE":
                if self.app_monitor.category == "NONPRODUCTIVE" and self.changed:
                    self.changed = False
                    self.trigger_response()
            time.sleep(1)
        
    def trigger_response(self):
        if self.response_type == "low":
            self.show_popup("You are off task!")
        elif self.response_type == "medium":
            self.show_popup_with_cancel("You have 5 seconds until unproductive apps are minimized.")
        elif self.response_type == "high":
            self.show_popup_no_cancel("You have 5 seconds until unproductive apps are minimized.")

    def show_popup(self, message):
        show_ok_popup(self.root, message=message)
        

    def show_popup_with_cancel(self, message):
        def on_cancel():
            nonlocal cancel
            cancel = True
            self.root.destroy()
            
        cancel = False
        show_ok_popup_with_cancel(self.root, message=message, on_cancel=on_cancel)

        def countdown():
            nonlocal cancel
            for _ in range(5, 0, -1):
                time.sleep(1)
            if not cancel:
                self.app_monitor.start_minimize()

        Thread(target=countdown).start()

    def show_popup_no_cancel(self, message):
        show_ok_popup(self.root, message=message)

        def countdown():
            for i in range(5, 0, -1):
                time.sleep(1)
            self.app_monitor.start_minimize()

        Thread(target=countdown).start()
