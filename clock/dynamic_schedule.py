import json
import time
from datetime import datetime, timedelta

class DynamicSchedule:
    def __init__(self, settings_file='settings.json'):
        self.settings_file = settings_file
        self.load_settings()
        self.current_task = None
        self.start_time = None

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as file:
                self.settings = json.load(file)
        except FileNotFoundError:
            print(f"Settings file {self.settings_file} not found. Using default settings.")
            self.settings = {"tasks": {}, "techniques": {}}

    def save_settings(self):
        with open(self.settings_file, 'w') as file:
            json.dump(self.settings, file, indent=4)

    def start_task(self, task_name):
        self.current_task = task_name
        self.start_time = datetime.now()
        print(f"Started task: {task_name} at {self.start_time}")

    def end_task(self):
        if self.current_task:
            end_time = datetime.now()
            duration = end_time - self.start_time
            print(f"Ended task: {self.current_task} at {end_time}, duration: {duration}")
            self.adjust_schedule(duration)
            self.current_task = None
            self.start_time = None

    def adjust_schedule(self, duration):
        task_settings = self.settings.get('tasks', {}).get(self.current_task, {})
        if task_settings:
            expected_duration = timedelta(minutes=task_settings.get('expected_duration', 25))
            if duration > expected_duration:
                task_settings['expected_duration'] += 5
            elif duration < expected_duration:
                task_settings['expected_duration'] = max(5, task_settings['expected_duration'] - 5)
            self.save_settings()

    def pomodoro(self):
        technique = self.settings.get('techniques', {}).get('pomodoro', {})
        focus_duration = technique.get('focus_duration', 25)
        short_break = technique.get('short_break', 5)
        long_break = technique.get('long_break', 15)
        long_break_interval = technique.get('long_break_interval', 4)

        for i in range(long_break_interval):
            self.start_task('Pomodoro')
            time.sleep(focus_duration * 60)
            self.end_task()
            print(f"Take a {short_break}-minute break.")
            time.sleep(short_break * 60)
        
        print(f"Take a {long_break}-minute break.")
        time.sleep(long_break * 60)

    def custom_technique(self, technique_name):
        technique = self.settings.get('techniques', {}).get(technique_name, {})
        if technique:
            for block in technique.get('blocks', []):
                self.start_task(block['name'])
                time.sleep(block['duration'] * 60)
                self.end_task()
                if 'break' in block:
                    print(f"Take a {block['break']} minute break.")
                    time.sleep(block['break'] * 60)

    def eat_the_frog(self):
        self.start_task('Eat the Frog')
        time.sleep(60 * 60)  # 1 hour
        self.end_task()
        print("Take a 10-minute break.")
        time.sleep(10 * 60)  # 10 minutes

    def time_blocking(self, blocks):
        for block in blocks:
            self.start_task(block['name'])
            time.sleep(block['duration'] * 60)
            self.end_task()
            if 'break' in block:
                print(f"Take a {block['break']} minute break.")
                time.sleep(block['break'] * 60)

if __name__ == "__main__":
    scheduler = DynamicSchedule()
    scheduler.pomodoro()
    # Example of using a custom technique
    # scheduler.custom_technique('CustomTechniqueName')