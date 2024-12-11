import json
import os
import sqlite3
import customtkinter

class Settings:
    def __init__(self):
        self.file_path = "settings.json"
        self.data = {}
        self.load()
        self.data.setdefault("response_type", 1)  # Default to 1 if not set

    def load(self):
        """Load settings from a file if it exists."""
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                self.data.update(json.load(file))

    def save(self):
        """Save current settings to a file."""
        with open(self.file_path, 'w') as file:
            json.dump(self.data, file, indent=4)

    def update(self, key, value):
        """Update a setting and save it."""
        self.data[key] = value
        self.save()
        
    def get(self, key, default=None):
        """Retrieve a setting value, returning a default if not found."""
        return self.data.get(key, default)

    def get_dynamic_schedule(self):
        """Retrieve dynamic schedule settings."""
        return self.data.get("dynamic_schedule", {})

    def update_dynamic_schedule(self, key, value):
        """Update dynamic schedule settings and save."""
        if "dynamic_schedule" not in self.data:
            self.data["dynamic_schedule"] = {}
        self.data["dynamic_schedule"][key] = value
        self.save()
