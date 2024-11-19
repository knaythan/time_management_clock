# clock/focus_mode.py
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import tkinter as tk
import threading

class FocusMode:
    def __init__(self, root):
        self.root = root
        self.is_active = False
        self.tray_icon = None

    def activate(self):
        """Minimize the app to the system tray."""
        if self.is_active:
            return
        self.is_active = True
        self.root.withdraw()  # Hide the main window
        self.create_tray_icon()

    def deactivate(self):
        """Restore the app from the system tray."""
        if not self.is_active:
            return
        self.is_active = False
        self.root.deiconify()  # Show the main window
        if self.tray_icon:
            self.tray_icon.stop()

    def create_tray_icon(self):
        """Create a system tray icon with menu options."""
        icon_image = self._create_icon_image()
        menu = Menu(
            MenuItem("Open", self._restore_from_tray),
            MenuItem("Exit", self._exit_app)
        )

        self.tray_icon = Icon("Smart Clock", icon_image, "Smart Clock", menu)
        
        # Run the tray icon in a separate thread to prevent blocking the main loop
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()

    def _create_icon_image(self):
        """Create a simple icon for the system tray."""
        icon_size = 64
        image = Image.new('RGB', (icon_size, icon_size), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 16, 48, 48), fill=(0, 0, 255))  # Blue square
        return image

    def _restore_from_tray(self, icon=None, item=None):
        """Restore the main app window from the system tray."""
        self.deactivate()

    def _exit_app(self, icon=None, item=None):
        """Exit the application gracefully."""
        self.tray_icon.stop()
        self.root.quit()
