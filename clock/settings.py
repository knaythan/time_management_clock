# clock/settings.py
import json

class Settings:
    def __init__(self, filename='settings.json'):
        self.filename = filename
        self.default_settings = {
            "reminder_interval": 30,  # in minutes
            "focus_mode_shortcut": "Ctrl+Shift+F"
        }
        self.settings = self.load_settings()

    def load_settings(self):
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.default_settings

    def save_settings(self):
        with open(self.filename, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get(self, key):
        return self.settings.get(key, None)

    def update(self, key, value):
        self.settings[key] = value
        self.save_settings()
