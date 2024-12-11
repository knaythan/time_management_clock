# clock/app_monitor.py
import time
import psutil
import platform
import sqlite3
from datetime import date
from pynput import keyboard, mouse

if platform.system() == "Windows":
    import win32gui
    import win32process
    import uiautomation as auto
elif platform.system() == "Darwin":
    from AppKit import NSWorkspace
    import Quartz
from threading import Thread
import os
from distraction import DetectDistraction

class AppMonitor:
    def __init__(self, title, db_path):
        self.app_times = {}  # {app_name: time_in_seconds}
        self.title = title
        self.db_path = db_path
        self.current_app = None
        self.category = None
        self.monitoring = False
        self.afk_detection = False
        self.last_activity_time = time.time()
        self.afk_threshold = 3  # 10 seconds of inactivity
        self.afk_app_name = "afk_time"

    def start_monitoring(self):
        """Start monitoring the focused application."""
        self.monitoring = True
        Thread(target=self._monitor_loop, daemon=True).start()

    def stop_monitoring(self):
        """Stop monitoring the focused application."""
        self.monitoring = False

    def start_afk_detection(self):
        """Start AFK detection by monitoring keyboard and mouse activity."""
        self.afk_detection = True
        Thread(target=self._afk_monitor_loop, daemon=True).start()

    def stop_afk_detection(self):
        """Stop AFK detection."""
        self.afk_detection = False
        
    def start_minimize(self):
        """Start minimizing unproductive apps."""
        self.minimize = True
        Thread(target=self._minimize_loop, daemon=True).start()
        
    def stop_minimize(self):
        """Stop minimizing unproductive apps."""
        self.minimize = False
        
    def _minimize_loop(self):
        """Minimize unproductive apps."""
        while self.minimize:
            focused_app = self._get_focused_app()
            if focused_app:
                self._minimize_distraction(focused_app)

    def _afk_monitor_loop(self):
        """Monitor for AFK status."""
        def on_activity(*args):
            self.last_activity_time = time.time()

        with keyboard.Listener(on_press=on_activity), mouse.Listener(on_click=on_activity, on_move=on_activity):
            while self.afk_detection:
                if time.time() - self.last_activity_time > self.afk_threshold:
                    self.current_app = self.afk_app_name  # Set current app to AFK
                    self._update_app_time(self.afk_app_name)  # Start counting AFK time
                time.sleep(1)

    def _monitor_loop(self):
        """Continuously monitor the focused application."""
        while self.monitoring:
            focused_app = self._get_focused_app()
            if focused_app:
                self._update_app_time(focused_app)
            time.sleep(1)
            
    def _find_address_bar(self, window):
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

    def _get_browser_url(self, browser_name="Google Chrome"):
        """Fetch the URL from the browser's address bar."""
        if self.minimize:
            time.sleep(5)
        try:
            url = None
            if platform.system() == "Windows":
                # Get the foreground window control
                with auto.UIAutomationInitializerInThread():
                    window = auto.GetForegroundControl()
                if not window:
                    pass

                # Check if the window is a browser
                if "chrome" in window.Name.lower() or "edge" in window.Name.lower():
                    url = self._find_address_bar(window)
                    return url if url else None

                return None
            elif platform.system() != "Darwin":
                script = f"""
                tell application "{browser_name}"
                    if (count of windows) > 0 then
                        return URL of {"current tab of front window" if browser_name in ["Safari", "Firefox"] else "active tab of front window"}
                    else
                        return ""
                    end if
                end tell
                """
                url = os.popen(f"osascript -e '{script}'").read().strip()
                    
            if url:
                url = url.split('/')[2] if '//' in url else url.split('/')[0]
            return url
        except Exception:
            return "Error fetching browser URL."

    def _get_focused_app(self):
        """Get the name of the currently focused application."""
        try:
            win_browswers = ["Chrome", "Edge"]
            mac_browsers = ["Google Chrome", "Safari"]

            if platform.system() == "Windows":
                hwnd = win32gui.GetForegroundWindow()
                win_name = win32gui.GetWindowText(hwnd)
                if any(browser in win_name for browser in win_browswers):
                    return self._get_browser_url()
            elif platform.system() == "Darwin":
                active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
                win_name = active_app.localizedName()
                browser_name = [browser for browser in mac_browsers if browser in win_name]
                if browser_name:
                    return self._get_browser_url(browser_name[0])
            if win_name == self.title:
                return None
            return win_name
        except Exception as e:
            print(f"Error detecting focused app: {e}")
        return None
    
    def _minimize_distraction(self, app_name):
        if platform.system() == "Windows":
            hwnd = win32gui.GetForegroundWindow()
            pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid[-1])
            process_name = process.name()
            if self.category == "NONPRODUCTIVE":
                win32gui.ShowWindow(hwnd, 6)  # Minimize the window
        elif platform.system() == "Darwin":
            process_name = app_name
            if self.category == "NONPRODUCTIVE":
                os.system(f"osascript -e 'tell application \"{process_name}\" to set miniaturized of front window to true'")

    def _update_app_time(self, app_name):
        """Update the focus time for the given application."""
        if app_name != self.current_app:
            self.current_app = app_name
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT category FROM classify_app WHERE app_name = ?", (app_name,))
                result = cursor.fetchone()
                if not result:
                    detector = DetectDistraction()
                    category = detector.classify(app_name)
                    cursor.execute(
                        """
                        INSERT INTO classify_app (app_name, category)
                        VALUES (?, ?)
                        ON CONFLICT(app_name) DO UPDATE SET category = excluded.category
                        """, (app_name, category)
                    )
                    conn.commit()
                    conn.close()
                    self.category = category
                    return
                self.category = result[0]
                return
            except Exception as e:
                print(f"Error detecting distraction: {e}")
        elif app_name == self.current_app:
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
