# Smart Time-Management Clock

Smart Time-Management Clock is a productivity tool that helps you monitor and manage your time spent on various applications. It includes features like focus mode, calendar view, and detailed statistics.

## Features

- **Dashboard**: View real-time focus times for different applications.
- **Focus Mode**: Minimize the app to the system tray and set a timer to reopen.
- **Calendar View**: Navigate through daily and monthly views of your application usage.
- **Statistics**: View detailed statistics for different time periods.
- **Settings**: Customize application names, enable autosave, and configure Pomodoro timer settings.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/smart-time-management-clock.git
    cd smart-time-management-clock
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Run the application:
    ```sh
    python clock/main.py
    ```

2. The main window will display the dashboard with real-time focus times for different applications.

3. Use the "Open Calendar" button to navigate to the calendar view and see your application usage for different days and months.

4. Use the "Settings" button to customize application names, enable autosave, and configure Pomodoro timer settings.

5. Use the "Activate Focus Mode" button to minimize the app to the system tray and set a timer to reopen.

## File Structure

- `clock/`
  - `__init__.py`: Package initialization.
  - `main.py`: Entry point for the application.
  - `gui.py`: Main GUI for the application.
  - `focus_mode.py`: Focus mode functionality.
  - `app_monitor.py`: Application monitoring functionality.
  - `dashboard.py`: Dashboard view functionality.
  - `calendar_view.py`: Calendar view functionality.
  - `settings.py`: Settings management functionality.
  - `statistics.py`: Statistics view functionality.
- `db/`
  - `usage_data.db`: SQLite database for storing usage data.
- `requirements.txt`: List of required Python packages.

## Dependencies

- `Pillow`
- `pystray`
- `customtkinter`
- `pyobjc` (macOS only)
- `pywin32` (Windows only)

## License

This project is licensed under the MIT License.