# clock/main.py
from gui import SmartClockApp
import customtkinter as ctk

def main():
    ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue"
    
    root = ctk.CTk()
    app = SmartClockApp(root)
    app.run()

if __name__ == "__main__":
    main()