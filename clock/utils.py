import customtkinter as ctk

def _create_ok_popup(root, message, title, ok_text="OK"):
    popup = _create_popup(root, message, title)
    
    ctk.CTkButton(popup, text=ok_text, command=popup.destroy).pack(pady=10)
    return popup

def _create_ok_popup_with_cancel(root, message, title, ok_text="OK", cancel_text="Cancel", on_cancel=None):
    popup = _create_ok_popup(root, message, title, ok_text)
    
    command = on_cancel if on_cancel else popup.destroy
    ctk.CTkButton(popup, text=cancel_text, command=command).pack(pady=10)
    return popup

def _create_popup(root, message, title="Alert"):
    popup = ctk.CTkToplevel(root)
    popup.title(title)
    popup.update_idletasks()
    width = 300
    height = 150
    x = (root.winfo_width() // 2) - (width // 2)
    y = (root.winfo_height() // 2) - (height // 2)
    popup.geometry(f'{width}x{height}+{x}+{y}')
    popup.resizable(False, False)        
            
    ctk.CTkLabel(popup, text=message, padx=10, pady=10, wraplength=280).pack(pady=20)
    return popup
    
def show_ok_popup(root, message, title="Alert", ok_text="OK"):
    popup = _create_ok_popup(root, message, title, ok_text)
    _show_popup(root, popup)
    
def show_ok_popup_with_cancel(root, message, title="Alert", ok_text="OK", cancel_text="Cancel", on_cancel=None):
    popup = _create_ok_popup_with_cancel(root, message, title, ok_text, cancel_text, on_cancel)
    _show_popup(root, popup)

def _show_popup(root, popup):
    popup.focus_force()
    popup.transient(root)
    root.wait_window(popup)
    
def format_time(seconds):
    """Convert time in seconds to a human-readable format with fixed units."""
    sec = int(seconds)
    if sec < 60:
        return f"{sec} s"
    elif sec < 3600:
        minutes = sec // 60
        sec = sec % 60
        return f"{minutes} min{'s' if minutes != 1 else ''} {sec} s"
    elif sec < 86400:
        hours = sec // 3600
        minutes = (sec % 3600) // 60
        sec = sec % 60
        return f"{hours} hr{'s' if hours != 1 else ''} {minutes} min{'s' if minutes != 1 else ''} {sec} s"
    else:
        days = sec // 86400
        hours = (sec % 86400) // 3600
        minutes = (sec % 3600) // 60
        sec = sec % 60
        return f"{days} day{'s' if days != 1 else ''} {hours} hr{'s' if hours != 1 else ''} {minutes} min{'s' if minutes != 1 else ''} {sec} s"