# clock/app_monitor.py
import time
import psutil
import platform
import sqlite3
from datetime import date

if platform.system() == "Windows":
    import win32gui
    import win32process
elif platform.system() == "Darwin":
    from AppKit import NSWorkspace
    import Quartz
from threading import Thread
import uiautomation as auto
import os

class AppMonitor:
    def __init__(self):
        self.app_times = {}  # {app_name: time_in_seconds}
        self.current_app = None
        self.monitoring = False

    def start_monitoring(self):
        """Start monitoring the focused application."""
        self.monitoring = True
        Thread(target=self._monitor_loop, daemon=True).start()

    def stop_monitoring(self):
        """Stop monitoring the focused application."""
        self.monitoring = False

    def _monitor_loop(self):
        """Continuously monitor the focused application."""
        while self.monitoring:
            focused_app = self._get_focused_app()
            if focused_app:
                self._update_app_time(focused_app)
            time.sleep(1)
            
    def find_address_bar(self, window):
        """Find the address bar control by traversing the window's UI hierarchy."""
        try:
            # Traverse through child elements
            for control in window.GetChildren():
                if control.ControlTypeName == "Edit" or "address" in control.Name.lower() or "url" in control.Name.lower():
                    return control.GetValuePattern().Value
                # Recursively search child controls
                sub_result = self.find_address_bar(control)
                if sub_result:
                    return sub_result
        except Exception:
            return None  # Suppress errors and return None
        return None

    def get_browser_url(self):
        """Fetch the URL from the browser's address bar."""
        try:
            # Get the foreground window control
            with auto.UIAutomationInitializerInThread():
                window = auto.GetForegroundControl()
            if not window:
                pass

            # Check if the window is a browser
            if "chrome" in window.Name.lower() or "edge" in window.Name.lower():
                url = self.find_address_bar(window)
                return url if url else None

            return None
        except Exception:
            return "Error fetching browser URL."
    
    def get_safari_url():
        try:
            script = """
            tell application "Safari"
                if (count of windows) > 0 then
                    return URL of current tab of front window
                else
                    return "No Safari window open"
                end if
            end tell
            """
            url = os.popen(f"osascript -e '{script}'").read().strip()
            return url
        except Exception as e:
            return "Error fetching URL from Safari."

    def _get_focused_app(self):
        """Get the name of the currently focused application."""
        try:
            if platform.system() == "Windows":
                hwnd = win32gui.GetForegroundWindow()
                browers = ["Chrome", "Edge"]
                if any(browser in win32gui.GetWindowText(hwnd) for browser in browers):
                    url = self.get_browser_url()
                    if url:
                        url = url.split('/')[2] if '//' in url else url.split('/')[0]
                        return url
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['pid'] == pid:
                        return proc.info['name']
            elif platform.system() == "Darwin":
                active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
                if active_app.bundleIdentifier() == "com.apple.Safari":
                    url = self.get_safari_url()
                    if url:
                        url = url.split('/')[2] if '//' in url else url.split('/')[0]
                        return url
                return active_app.localizedName()
        except Exception as e:
            print(f"Error detecting focused app: {e}")
        return None

    def _update_app_time(self, app_name):
        """Update the focus time for the given application."""
        if app_name != self.current_app:
            self.current_app = app_name
        self.app_times[app_name] = self.app_times.get(app_name, 0) + 1

    def get_app_times(self):
        """Return the accumulated focus times for each application."""
        return {app: time for app, time in sorted(self.app_times.items(), key=lambda x: -x[1])}

    def save_focus_times(self, db_path):
        """Save the accumulated focus times to the database."""
        retries = 5
        while retries > 0:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                for app_name, focus_time in self.app_times.items():
                    cursor.execute("""
                        INSERT INTO usage_data (date, app_name, focus_time)
                        VALUES (?, ?, ?)
                        ON CONFLICT(date, app_name) DO UPDATE SET focus_time = focus_time + excluded.focus_time
                    """, (date.today().isoformat(), app_name, focus_time))
                conn.commit()
                conn.close()
                break
            except sqlite3.OperationalError as e:
                if 'database is locked' in str(e):
                    retries -= 1
                    time.sleep(1)
                else:
                    raise
