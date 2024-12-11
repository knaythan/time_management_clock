# clock/main.py
from gui import SmartClockApp
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw  # Import ImageDraw
import os
import platform

def main():
    ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "green", "dark-blue")
    
    root = ctk.CTk()
    
    # Create the icon image using the same method as in focus_mode.py
    icon_size = 64  # Use a smaller icon size for better compatibility
    image = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))  # Transparent background
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, icon_size, icon_size), fill=(255, 255, 255))  # Clock face
    draw.ellipse((0, 0, icon_size, icon_size), outline=(0, 0, 0), width=2)  # Larger clock face
    draw.line((32, 32, 32, 16), fill=(0, 0, 0), width=2)  # Minute hand
    draw.line((32, 32, 48, 32), fill=(0, 0, 0), width=2)  # Hour hand

    # Convert the PIL image to a PhotoImage for tkinter
    icon_photo = ImageTk.PhotoImage(image)
    # Save the icon image as a .ico file
    if platform.system() == "Darwin":
        root.iconphoto(True, icon_photo)  # Set the custom icon
    else:
        icon_path = os.path.join(os.path.dirname("../icons"), "icon.ico")
        image.save(icon_path, format='ICO')

        # Set the custom icon
        root.iconbitmap(icon_path)  # Set the custom icon

    app = SmartClockApp(root)
    app.run()

if __name__ == "__main__":
    main()