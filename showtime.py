import tkinter as tk
from datetime import datetime, timedelta
import pytz
import signal
import sys

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

    time_display = " | ".join(current_times)
    label.config(text=time_display)
    root.after(refresh_interval, update_time)

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
    window_width = label.winfo_width() + 200  # Adjusted for better spacing
    window_height = label.winfo_height() + 10  # Adjusted to avoid clipping
    root.geometry(f"{window_width}x{window_height}+100+100")

# Function to close the application
def close_app(event=None):
    root.destroy()
    sys.exit(0)

# Signal handler for SIGINT
def signal_handler(sig, frame):
    print("Application closed by user.")
    close_app()

# Function to update the conversion table
def update_conversion_table(base_tz_name):
    base_tz = pytz.timezone(base_tz_name)
    for i in range(24):
        base_time = datetime.now(base_tz).replace(hour=i, minute=0, second=0, microsecond=0)
        for j, tz_name in enumerate(timezones.values()):
            tz = pytz.timezone(tz_name)
            converted_time = base_time.astimezone(tz).strftime('%H:%M')
            table_labels[i][j].config(text=converted_time)

# Function to create the conversion table
def create_conversion_table():
    global table_labels
    table_labels = [[None for _ in range(len(timezones))] for _ in range(24)]

    for i, tz_abbr in enumerate(timezones.keys()):
        header = tk.Label(conversion_window, text=tz_abbr, font=("Helvetica", 12, "bold"), bg="white", fg="black")
        header.grid(row=0, column=i, padx=1, pady=1)
        header.bind("<Button-1>", lambda e, tz=list(timezones.values())[i]: on_header_click(tz))

    for i in range(24):
        for j in range(len(timezones)):
            label = tk.Label(conversion_window, text="", font=("Helvetica", 10), bg="white", fg="black")
            label.grid(row=i+1, column=j, padx=1, pady=1)
            label.bind("<Button-1>", lambda e, row=i: highlight_row(row))
            table_labels[i][j] = label

# Function to handle header click
def on_header_click(base_tz_name):
    update_conversion_table(base_tz_name)

# Function to highlight a row
def highlight_row(row):
    for i in range(24):
        for j in range(len(timezones)):
            if i == row:
                table_labels[i][j].config(bg="LightGoldenRodYellow")
            else:
                table_labels[i][j].config(bg="white")

# Function to show the conversion table
def show_conversion_table(event=None):
    global conversion_window
    conversion_window = tk.Toplevel(root)
    conversion_window.title("Time Conversion Table")
    conversion_window.configure(bg="white")
    create_conversion_table()
    update_conversion_table("Asia/Hong_Kong")

# Create the main window
root = tk.Tk()
root.title("World Clock")

# Remove window decorations
root.overrideredirect(True)

# Make the window always on top
root.attributes("-topmost", True)

# Set window transparency (alpha channel)
root.attributes("-alpha", 0.8)  # Adjust alpha if needed for slight transparency

# Create a frame to hold the label and the close button
frame = tk.Frame(root, padx=5, pady=5, bg="white")  # Added more padding and set background color
frame.pack()

# Create a label to display the time
label = tk.Label(frame, font=("Helvetica", 16), fg="black", bg="white")  # Set font color and background color
label.pack(side=tk.LEFT, padx=10, pady=(1, 1))  # Adjusted padding

# Create a canvas to draw the red dot and blue rectangle
canvas = tk.Canvas(frame, width=40, height=20, highlightthickness=0, bg="white")  # Set background color
canvas.pack(side=tk.RIGHT, padx=5, pady=(1, 1))  # Adjusted padding

# Draw the red dot
red_dot = canvas.create_oval(5, 5, 15, 15, fill="red", outline="red")
canvas.tag_bind(red_dot, "<Button-1>", close_app)  # Bind the red dot to close the application

# Draw the blue rectangle
blue_rectangle = canvas.create_rectangle(25, 5, 35, 15, fill="blue", outline="blue")
canvas.tag_bind(blue_rectangle, "<Button-1>", show_conversion_table)  # Bind the blue rectangle to open the conversion window

# Bind mouse events to move the window
root.bind("<Button-1>", start_move)
root.bind("<B1-Motion>", move_window)

# Set the refresh interval (in milliseconds)
refresh_interval = 1000  # You can adjust this value to see the effect

# Start the update process and adjust window size
update_time()
update_window_size()

# Ensure the window size updates correctly after a short delay
root.after(500, update_window_size)

# Register signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)

# Run the application inside a try/except block to handle KeyboardInterrupt
try:
    root.mainloop()
except KeyboardInterrupt:
    print("Application closed by user.")
    close_app()
