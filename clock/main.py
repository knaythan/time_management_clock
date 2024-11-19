# clock/main.py
from gui import SmartClockApp
import tkinter as tk

def main():
    root = tk.Tk()
    app = SmartClockApp(root)
    app.run()

if __name__ == "__main__":
    main()