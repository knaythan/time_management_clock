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

    def _get_focused_app(self):
        """Get the name of the currently focused application."""
        try:
            if platform.system() == "Windows":
                hwnd = win32gui.GetForegroundWindow()
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['pid'] == pid:
                        return proc.info['name']
            elif platform.system() == "Darwin":
                active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
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
