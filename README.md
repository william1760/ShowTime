
# ShowTime
<img width="237" height="386" alt="image" src="https://github.com/user-attachments/assets/23d33ea9-b217-466c-a0f4-2eaaa610a046" />

<img width="658" height="742" alt="image" src="https://github.com/user-attachments/assets/11add5bd-dc78-460c-86a9-a8eb412e680d" />


A lightweight macOS desktop world clock widget built with Python and tkinter.  
Displays live times for multiple timezones in a borderless, always-on-top floating window.  
A 24-hour time conversion table is one double-click away.

---

## Features

- **Floating world clock** — borderless, always-on-top, spans all Spaces
- **Live display** — main timezone shows `HH:MM:SS`, all others show `HH:MM`
- **Time conversion table** — 24-hour grid across all configured timezones, opens in a separate window
  - Highlight current-hour row in a distinct colour
  - Click any column header to rebase the whole table to that timezone
  - Drag the title bar to reposition
  - Red close button (top-right)
- **Fully configurable** via `showtime.conf` — no code changes needed
- **Font scaling** — scroll wheel or `Ctrl +` / `Ctrl -` / `Ctrl 0` on both windows
- **Position memory** — last position saved to `showtime.conf`, restored on next launch
- **Multi-monitor aware** — centers on the correct monitor; snaps back if dragged off-screen
- **Ctrl+click** — instantly centers the widget on the current monitor

---

## Requirements

- macOS (uses AppKit for multi-monitor and window management)
- Python 3.9+ (3.13 recommended)
- Dependencies:

```
pytz
```

Install:

```bash
pip install -r requirements.txt
```

> **Note:** `rumps` is listed in `requirements.txt` but is not used by the current version.

---

## Usage

```bash
python3 showtime.py
```

### Main window controls

| Action | Result |
|---|---|
| Drag | Move the widget |
| Double-click | Open time conversion table |
| Scroll wheel | Resize font (up = larger, down = smaller) |
| `Ctrl +` / `Ctrl -` | Resize font (click widget first to focus) |
| `Ctrl 0` | Reset font to configured default |
| `Ctrl + click` | Center widget on current monitor |
| Right-click / Middle-click | Quit |

### Conversion table controls

| Action | Result |
|---|---|
| Click column header | Rebase table to that timezone |
| Click any row | Highlight that row |
| Scroll wheel | Resize font |
| `Ctrl +` / `Ctrl -` | Resize font |
| `Ctrl 0` | Reset font to configured default |
| Red dot (top-right) | Close table |
| Drag title bar | Move table window |

---

## Configuration

All settings live in `showtime.conf` next to `showtime.py`.  
The app re-reads the file on every launch — just edit and restart.

```ini
[timezones]
; One entry per timezone. Label = pytz timezone name.
; Display order follows the order defined here.
SYD = Australia/Sydney
TYO = Asia/Tokyo
HKT = Asia/Hong_Kong
IST = Asia/Kolkata
PAR = Europe/Paris
BST = Europe/London
GMT = Etc/GMT
NYK = America/New_York
UTC = UTC
SEA = America/Los_Angeles

[display]
main_timezone = HKT      ; shows HH:MM:SS; all others show HH:MM
refresh_ms    = 1000     ; update interval in milliseconds
bg            = #3c3c3c  ; background colour (hex)
fg            = #00ff00  ; time text colour (hex)

[fonts]
family      = Menlo      ; font family
main_size   = 19         ; main window font size (pt)
table_size  = 14         ; conversion table font size (pt)
header_size = 11         ; conversion table header font size (pt)

[transparency]
main_window      = 0.50  ; 0.0 (invisible) – 1.0 (opaque)
conversion_table = 0.90

[position]
; Auto-written by the app when you drag or centre the widget.
; Delete these lines to reset to screen centre on next launch.
x = 100
y = 100
```

### Adding or removing timezones

Edit the `[timezones]` section — use any [pytz timezone name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).  
Both windows update automatically; no code changes needed.

```ini
[timezones]
LON = Europe/London
NYC = America/New_York
```

---

## Launch via Automator (click-to-launch from Dock)

1. Open **Automator** → New Document → **Application**
2. Add action: **Run Shell Script**  
   Shell: `/bin/zsh` | Pass input: `as arguments`
3. Paste:

```bash
PYTHON=$(which python3)

if [ -z "$PYTHON" ]; then
    osascript -e 'display alert "python3 not found in PATH"'
    exit 1
fi

APP_DIR=$(dirname "$(osascript -e 'tell application "Finder" to get POSIX path of (path to me)')")
"$PYTHON" "$APP_DIR/showtime.py"
```

4. Save as `ShowTime.app` in the **same folder** as `showtime.py`
5. Drag `ShowTime.app` to the Dock for one-click launch

---

## Launch via keyboard shortcut (macOS Shortcuts app)

1. Open **Shortcuts** → **+** New Shortcut
2. Add action: **Run Shell Script**, paste:

```bash
PYTHON=$(which python3)
"$PYTHON" /path/to/ShowTime/showtime.py
```

3. **⚙ → Add Keyboard Shortcut** → assign your combo (e.g. `⌥⌘S`)

---

## File structure

```
ShowTime/
├── showtime.py       # entire application (single file)
├── showtime.conf     # configuration (auto-updated at runtime)
├── requirements.txt
└── README.md
```

---

## License

MIT
