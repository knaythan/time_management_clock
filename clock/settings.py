import json
import os
import sqlite3

class Settings:
    def __init__(self):
        self.file_path = "settings.json"
        self.db_path = os.path.join(os.path.dirname(__file__), '../db/usage_data.db')
        self.data = {
            "custom_app_names": {},
            "autosave": True,  # Default to autosave enabled
            "pomodoro_timer": 25,  # Default Pomodoro timer in minutes
            "short_break": 5,  # Default short break in minutes
            "long_break": 15,  # Default long break in minutes
            "long_break_interval": 4  # Number of Pomodoros before a long break
        }
        self.load()
        self._setup_database()

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

    def _setup_database(self):
        """Set up SQLite database for saving focus times."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_data (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                app_name TEXT NOT NULL,
                focus_time REAL NOT NULL,
                UNIQUE(date, app_name)
            )
        """)
        conn.commit()
        conn.close()