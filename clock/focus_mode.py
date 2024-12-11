# clock/focus_mode.py
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import tkinter as tk
import threading
import platform

class FocusMode:
    def __init__(self, root):
        self.root = root
        self.is_active = False
        self.tray_icon = None

    def activate(self, interval=25):
        """Minimize the app to the system tray and set a timer to reopen."""
        if self.is_active:
            return
        self.is_active = True
        self.root.withdraw()  # Hide the main window
        if platform.system() == "Darwin":
            self.create_tray_icon()
        else:
            self.create_tray_icon()
        self.root.after(interval * 60 * 1000, self.deactivate)  # Reopen after interval minutes

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
            MenuItem("Open", self._restore_from_tray, default=True),
            MenuItem("Exit", self._exit_app)
        )

        self.tray_icon = Icon("Smart Clock", icon_image, "Smart Clock", menu)
        self.tray_icon.run_detached()
        self.tray_icon.icon = icon_image
        self.tray_icon.visible = True
        self.tray_icon.menu = menu
        self.tray_icon._icon._menu = menu  # Ensure the menu is set
        self.tray_icon._icon._on_left_click = self._restore_from_tray  # Handle left-click event

    def _create_icon_image(self):
        """Create a simple icon for the system tray with a transparent background and a larger clock."""
        icon_size = 64
        image = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))  # Transparent background
        draw = ImageDraw.Draw(image)
        draw.ellipse((0, 0, icon_size, icon_size), fill=(255, 255, 255))  # Clock face
        draw.ellipse((0, 0, icon_size, icon_size), outline=(0, 0, 0), width=2)  # Larger clock face
        draw.line((32, 32, 32, 16), fill=(0, 0, 0), width=2)  # Minute hand
        draw.line((32, 32, 48, 32), fill=(0, 0, 0), width=2)  # Hour hand   
        return image

    def _restore_from_tray(self, icon=None, item=None):
        """Restore the main app window from the system tray."""
        if self.is_active:
            self.deactivate()
        else:
            if self.tray_icon:
                self.tray_icon.stop()
                self.tray_icon = None

    def _exit_app(self, icon=None, item=None):
        """Exit the application gracefully."""
        self.tray_icon.stop()
        self.root.quit()
