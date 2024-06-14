import tkinter as tk
from datetime import datetime
import pytz

# Define the timezones and their abbreviations
timezones = {
    "HK": "Asia/Hong_Kong",
    "IST": "Asia/Kolkata",
    "FR": "Europe/Paris",
    "UK": "Europe/London",
    "NY": "America/New_York"
}

# Function to update the time
def update_time():
    current_times = []
    for tz_abbr, tz_name in timezones.items():
        tz = pytz.timezone(tz_name)
        current_time = datetime.now(tz).strftime('%H:%M')
        current_times.append(f"{tz_abbr} {current_time}")

    time_display = "  /  ".join(current_times)
    label.config(text=time_display)

    # Refresh every second
    root.after(1000, update_time)

# Functions to move the window
def start_move(event):
    global last_click_x, last_click_y
    last_click_x = event.x
    last_click_y = event.y

def move_window(event):
    x = event.x_root - last_click_x
    y = event.y_root - last_click_y
    root.geometry(f"+{x}+{y}")

# Function to update window size
def update_window_size():
    root.update_idletasks()
    window_width = label.winfo_width() + 30  # Add some space for the close button
    window_height = label.winfo_height()
    root.geometry(f"{window_width}x{window_height}+100+100")
    root.configure(bg="white")  # Match window background to label background

# Function to close the application
def close_app(event):
    root.destroy()

# Create the main window
root = tk.Tk()
root.title("World Clock")

# Remove window decorations
root.overrideredirect(True)

# Make the window always on top
root.attributes("-topmost", True)

# Set window transparency
root.attributes("-alpha", 0.5)

# Create a frame to hold the label and the close button
frame = tk.Frame(root, bg="white")
frame.pack()

# Create a label to display the time
label = tk.Label(frame, font=("Helvetica", 14), bg="white", fg="black")
label.pack(side=tk.LEFT)

# Create a canvas to draw the red dot
canvas = tk.Canvas(frame, width=20, height=20, bg="white", highlightthickness=0)
canvas.pack(side=tk.RIGHT, padx=5)

# Draw the red dot
red_dot = canvas.create_oval(5, 5, 15, 15, fill="red", outline="red")

# Bind mouse events to move the window
root.bind("<Button-1>", start_move)
root.bind("<B1-Motion>", move_window)

# Bind the red dot to close the application
canvas.tag_bind(red_dot, "<Button-1>", close_app)

# Start the update process and adjust window size
update_time()
update_window_size()

# Ensure the window size updates correctly after a short delay
root.after(500, update_window_size)

# Run the application
root.mainloop()
