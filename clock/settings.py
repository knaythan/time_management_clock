import json
import os
import sqlite3
import customtkinter

class Settings:
    def __init__(self):
        self.file_path = "settings.json"
        self.data = {}
        self.load()

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
        
    def get(self, key):
        """Retrieve a setting value."""
        return self.data.get(key, None)
    