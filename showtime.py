import configparser
import multiprocessing
import os
from datetime import datetime

import pytz
import tkinter as tk

_CONF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "showtime.conf")


def _load_config():
    cfg = configparser.ConfigParser()
    cfg.read(_CONF_PATH)

    # Order is defined by the [timezones] section in the conf file
    timezones = {k.upper(): v for k, v in cfg.items("timezones")}

    main_tz  = cfg.get("display", "main_timezone", fallback="HKT")
    refresh  = cfg.getint("display", "refresh_ms",  fallback=1000)
    bg       = cfg.get("display", "bg",             fallback="#3c3c3c")
    fg       = cfg.get("display", "fg",             fallback="lime")

    family      = cfg.get("fonts", "family",      fallback="Menlo")
    font_main   = (family, cfg.getint("fonts", "main_size",   fallback=10))
    font_table  = (family, cfg.getint("fonts", "table_size",  fallback=11))
    font_header = (family, cfg.getint("fonts", "header_size", fallback=11), "bold")

    alpha_main  = cfg.getfloat("transparency", "main_window",      fallback=0.68)
    alpha_table = cfg.getfloat("transparency", "conversion_table", fallback=0.90)

    init_x = cfg.getint("position", "x", fallback=None)
    init_y = cfg.getint("position", "y", fallback=None)

    return (timezones, main_tz, refresh, bg, fg,
            font_main, font_table, font_header,
            alpha_main, alpha_table,
            init_x, init_y)


(TIMEZONES, main_timezone, REFRESH_MS, BG, FG,
 FONT_MAIN, FONT_TABLE, FONT_HEADER,
 ALPHA_MAIN, ALPHA_TABLE,
 INIT_X, INIT_Y) = _load_config()


def _save_conf(**sections):
    """Write one or more {section: {key: value}} pairs to the conf file."""
    cfg = configparser.ConfigParser()
    cfg.read(_CONF_PATH)
    for section, kv in sections.items():
        if not cfg.has_section(section):
            cfg.add_section(section)
        for key, value in kv.items():
            cfg.set(section, key, str(value))
    with open(_CONF_PATH, "w") as f:
        cfg.write(f)


def _is_on_screen(root, w, h):
    """Return True if the window's centre point is on any connected display."""
    cx = root.winfo_x() + w // 2
    cy = root.winfo_y() + h // 2
    try:
        import AppKit
        primary_h = AppKit.NSScreen.mainScreen().frame().size.height
        for screen in AppKit.NSScreen.screens():
            f    = screen.frame()
            sx   = int(f.origin.x)
            sy   = int(primary_h - f.origin.y - f.size.height)
            sw_s = int(f.size.width)
            sh_s = int(f.size.height)
            if sx <= cx < sx + sw_s and sy <= cy < sy + sh_s:
                return True
        return False
    except Exception:
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        return 0 <= cx < sw and 0 <= cy < sh


def _center_on_current_monitor(root, w, h):
    """Return (x, y) that centres the window on whichever monitor it overlaps most."""
    wx, wy = root.winfo_x(), root.winfo_y()
    try:
        import AppKit
        # AppKit origin: bottom-left of primary screen.  Tk origin: top-left.
        primary_h = AppKit.NSScreen.mainScreen().frame().size.height
        best, best_area = None, 0
        for screen in AppKit.NSScreen.screens():
            f    = screen.frame()
            sx   = int(f.origin.x)
            sy   = int(primary_h - f.origin.y - f.size.height)
            sw_s = int(f.size.width)
            sh_s = int(f.size.height)
            ox   = max(0, min(wx + w, sx + sw_s) - max(wx, sx))
            oy   = max(0, min(wy + h, sy + sh_s) - max(wy, sy))
            area = ox * oy
            if area > best_area:
                best_area = area
                best = (sx, sy, sw_s, sh_s)
        if best:
            sx, sy, sw_s, sh_s = best
            return sx + (sw_s - w) // 2, sy + (sh_s - h) // 2
    except Exception:
        pass
    return (root.winfo_screenwidth() - w) // 2, (root.winfo_screenheight() - h) // 2


# ── conversion table (runs in its own process) ────────────────────────────────

def _run_conversion_table():
    table_labels  = []
    header_labels = []
    _base_col     = [list(TIMEZONES.keys()).index(main_timezone)]
    _now_row      = [0]   # tracks the current-hour row index
    _cur_t_size   = [FONT_TABLE[1]]
    col_widths    = [max(len(abbr), 5) + 2 for abbr in TIMEZONES.keys()]

    def highlight_row(row, col=None):
        if col is not None:
            _base_col[0] = col
        for i in range(24):
            for j, lbl in enumerate(table_labels[i]):
                bg = "#4D122F" if i == _now_row[0] else ("#464646" if i % 2 == 0 else "#414141")
                fg = "#fffdd0" if (i == row or j == _base_col[0]) else "#add8e6"
                lbl.config(bg=bg, fg=fg)

    def update_table(base_tz_name):
        _base_col[0] = list(TIMEZONES.values()).index(base_tz_name)
        base_tz  = pytz.timezone(base_tz_name)
        now_hour = datetime.now(base_tz).hour
        _now_row[0] = now_hour
        for i in range(24):
            base_time = datetime.now(base_tz).replace(hour=i, minute=0, second=0, microsecond=0)
            for j, tz_name in enumerate(TIMEZONES.values()):
                converted = base_time.astimezone(pytz.timezone(tz_name)).strftime("%H:%M")
                table_labels[i][j].config(text=converted)
        highlight_row(now_hour)
        canvas.yview_moveto(max(0, (now_hour - 3) / 24))

    root = tk.Tk()
    root.overrideredirect(True)
    root.configure(bg=BG)
    root.attributes("-alpha", ALPHA_TABLE)
    root.attributes("-topmost", True)

    def quit_table(_e=None):
        root.quit()
        root.destroy()

    title_bar = tk.Frame(root, bg="#484848", pady=5)
    title_bar.pack(fill=tk.X)

    tk.Label(title_bar, text="TIME CONVERSION TABLE", font=("Menlo", 9, "bold"),
             bg="#484848", fg="#aaddff").pack(side=tk.LEFT, padx=10)
    tk.Label(title_bar, text="click header to rebase",
             font=("Menlo", 7), bg="#484848", fg="#777777").pack(side=tk.LEFT, padx=(0, 10))

    # Red close button — packed last so it sits on the far right
    close_btn = tk.Canvas(title_bar, width=12, height=12, bg="#484848",
                          highlightthickness=0)
    close_btn.pack(side=tk.RIGHT, padx=(4, 8))
    _dot = close_btn.create_oval(1, 1, 11, 11, fill="#ff5f57", outline="")
    close_btn.bind("<Enter>",    lambda e: close_btn.itemconfig(_dot, fill="#bf4743"))
    close_btn.bind("<Leave>",    lambda e: close_btn.itemconfig(_dot, fill="#ff5f57"))
    # Defer destruction so bind_all handlers don't fire on a dead window
    close_btn.bind("<Button-1>", lambda e: root.after(0, quit_table))

    container = tk.Frame(root, bg=BG)
    container.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
    inner  = tk.Frame(canvas, bg=BG)

    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.pack(fill=tk.BOTH, expand=True)

    for j, abbr in enumerate(TIMEZONES.keys()):
        hdr = tk.Label(inner, text=abbr, font=FONT_HEADER, bg="#505050", fg="#aaddff",
                       width=col_widths[j], relief="flat", pady=4)
        hdr.grid(row=0, column=j, padx=1, pady=1, sticky="ew")
        hdr.bind("<Button-1>", lambda e, tz=list(TIMEZONES.values())[j]: update_table(tz))
        header_labels.append(hdr)

    for i in range(24):
        row_labels = []
        for j in range(len(TIMEZONES)):
            cell = tk.Label(inner, text="", font=FONT_TABLE, bg="#464646", fg="#add8e6",
                            width=col_widths[j], relief="flat", pady=3)
            cell.grid(row=i + 1, column=j, padx=1, pady=1, sticky="ew")
            cell.bind("<Button-1>", lambda e, r=i, c=j: highlight_row(r, c))
            row_labels.append(cell)
        table_labels.append(row_labels)

    update_table(TIMEZONES[main_timezone])

    root.update_idletasks()
    tw = inner.winfo_reqwidth()
    th = inner.winfo_reqheight() + title_bar.winfo_reqheight()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{tw}x{th}+{(sw - tw) // 2}+{(sh - th) // 2}")
    root.update()
    root.focus_force()   # grab keyboard focus so Ctrl+/− work immediately

    # ── font scaling ─────────────────────────────────────────────────────────

    def apply_table_font_size(size):
        size = max(6, size)
        _cur_t_size[0] = size
        f_table  = (FONT_TABLE[0], size)
        f_header = (FONT_TABLE[0], size, "bold")
        for hdr in header_labels:
            hdr.config(font=f_header)
        for row in table_labels:
            for cell in row:
                cell.config(font=f_table)
        def _commit():
            tw = inner.winfo_reqwidth()
            th = inner.winfo_reqheight() + title_bar.winfo_reqheight()
            root.geometry(f"{tw}x{th}+{root.winfo_x()}+{root.winfo_y()}")
            _save_conf(fonts={"table_size": size})
        root.after(1, _commit)

    # ── drag & close ─────────────────────────────────────────────────────────

    _d = {}

    def on_press(e):
        root.focus_force()
        _d["x"], _d["y"] = e.x_root, e.y_root

    def on_drag(e):
        root.geometry(
            f"+{root.winfo_x() + e.x_root - _d['x']}"
            f"+{root.winfo_y() + e.y_root - _d['y']}"
        )
        _d["x"], _d["y"] = e.x_root, e.y_root

    for w in [title_bar] + [c for c in title_bar.winfo_children() if c is not close_btn]:
        w.bind("<Button-1>", on_press)
        w.bind("<B1-Motion>", on_drag)

    # Re-grab focus on any click so keyboard shortcuts keep working
    root.bind_all("<Button-1>", lambda e: root.focus_force())
    root.bind_all("<MouseWheel>",       lambda e: apply_table_font_size(
                                            _cur_t_size[0] + (1 if e.delta > 0 else -1)))
    root.bind_all("<Control-equal>",    lambda e: apply_table_font_size(_cur_t_size[0] + 1))
    root.bind_all("<Control-plus>",     lambda e: apply_table_font_size(_cur_t_size[0] + 1))
    root.bind_all("<Control-minus>",    lambda e: apply_table_font_size(_cur_t_size[0] - 1))
    root.bind_all("<Control-0>",        lambda e: apply_table_font_size(FONT_TABLE[1]))

    root.mainloop()


# ── desktop widget ────────────────────────────────────────────────────────────

def main():
    _table_proc = [None]
    _cur_size   = [FONT_MAIN[1]]   # mutable; tracks live font size for Ctrl+/-/0

    root = tk.Tk()
    root.overrideredirect(True)
    root.configure(bg=BG)
    root.attributes("-alpha", ALPHA_MAIN)

    outer = tk.Frame(root, bg=BG, padx=12, pady=8)
    outer.pack(fill=tk.BOTH, expand=True)

    tk.Label(outer, text="WORLD CLOCK", font=("Menlo", 9, "bold"),
             bg=BG, fg="#6699cc").pack(anchor="w", pady=(0, 5))

    time_labels = {}
    abbr_labels = {}
    for abbr in TIMEZONES:
        row = tk.Frame(outer, bg=BG)
        row.pack(fill=tk.X, pady=1)
        al = tk.Label(row, text=abbr, font=(FONT_MAIN[0], FONT_MAIN[1], "bold"),
                      bg=BG, fg="#aaddff", width=5, anchor="w")
        al.pack(side=tk.LEFT)
        abbr_labels[abbr] = al
        lbl = tk.Label(row, text="--:--", font=FONT_MAIN, bg=BG, fg=FG, anchor="w")
        lbl.pack(side=tk.LEFT)
        time_labels[abbr] = lbl

    _tz_cache = {abbr: (pytz.timezone(tz_name), "%H:%M:%S" if abbr == main_timezone else "%H:%M")
                 for abbr, tz_name in TIMEZONES.items()}

    def tick():
        for abbr, (tz, fmt) in _tz_cache.items():
            time_labels[abbr].config(text=datetime.now(tz).strftime(fmt))
        root.after(REFRESH_MS, tick)

    tick()
    root.update_idletasks()
    w = root.winfo_reqwidth()
    h = root.winfo_reqheight()

    if INIT_X is not None and INIT_Y is not None:
        root.geometry(f"+{INIT_X}+{INIT_Y}")
    else:
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")
    root.update()

    # Saved position may be stale (monitor unplugged, resolution changed, etc.)
    if not _is_on_screen(root, w, h):
        nx, ny = _center_on_current_monitor(root, w, h)
        root.geometry(f"+{nx}+{ny}")
        _save_conf(position={"x": nx, "y": ny})

    try:
        import AppKit
        ns_app = AppKit.NSApplication.sharedApplication()
        ns_app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
        ns_win = ns_app.windows()[-1]
        ns_win.setLevel_(-1)
        ns_win.setCollectionBehavior_(
            (1 << 0) |  # CanJoinAllSpaces
            (1 << 4) |  # Stationary
            (1 << 6)    # IgnoresCycle
        )
    except Exception:
        pass

    # ── font scaling ──────────────────────────────────────────────────────────

    def apply_font_size(size):
        size = max(6, size)
        _cur_size[0] = size
        f_reg  = (FONT_MAIN[0], size)
        f_bold = (FONT_MAIN[0], size, "bold")
        for lbl in time_labels.values():
            lbl.config(font=f_reg)
        for lbl in abbr_labels.values():
            lbl.config(font=f_bold)
        # Delay by 1 ms so Tk processes font changes before we measure.
        # Use outer.winfo_reqwidth (not root) — root's reqwidth returns the
        # previously-pinned explicit size, not the content's natural size.
        def _commit():
            nw = outer.winfo_reqwidth()
            nh = outer.winfo_reqheight()
            root.geometry(f"{nw}x{nh}+{root.winfo_x()}+{root.winfo_y()}")
            _save_conf(fonts={"main_size": size})
        root.after(1, _commit)

    # ── interaction handlers ──────────────────────────────────────────────────

    def open_table(_e=None):
        if _table_proc[0] and _table_proc[0].is_alive():
            return
        _table_proc[0] = multiprocessing.Process(target=_run_conversion_table, daemon=True)
        _table_proc[0].start()

    _d = {"x": 0, "y": 0, "dragged": False}

    def on_press(e):
        # Grab keyboard focus so Ctrl+/− work after clicking the widget
        root.focus_force()
        _d["x"], _d["y"] = e.x_root, e.y_root
        _d["dragged"] = False

    def on_drag(e):
        root.geometry(
            f"+{root.winfo_x() + e.x_root - _d['x']}"
            f"+{root.winfo_y() + e.y_root - _d['y']}"
        )
        _d["x"], _d["y"] = e.x_root, e.y_root
        _d["dragged"] = True

    def on_release(e):
        if _d["dragged"]:
            rx, ry = root.winfo_x(), root.winfo_y()
            cw, ch = root.winfo_width(), root.winfo_height()
            if not _is_on_screen(root, cw, ch):
                rx, ry = _center_on_current_monitor(root, cw, ch)
                root.geometry(f"+{rx}+{ry}")
            _save_conf(position={"x": rx, "y": ry})
            _d["dragged"] = False

    def on_ctrl_click(_e=None):
        cw = root.winfo_width()
        ch = root.winfo_height()
        nx, ny = _center_on_current_monitor(root, cw, ch)
        root.geometry(f"+{nx}+{ny}")
        _save_conf(position={"x": nx, "y": ny})

    def quit_app(_e=None):
        root.quit()
        root.destroy()

    # Scroll wheel is the reliable resize path on macOS (keyboard needs focus first)
    root.bind_all("<MouseWheel>",       lambda e: apply_font_size(
                                            _cur_size[0] + (1 if e.delta > 0 else -1)))
    root.bind_all("<Button-1>",         on_press)
    root.bind_all("<B1-Motion>",        on_drag)
    root.bind_all("<ButtonRelease-1>",  on_release)
    root.bind_all("<Double-Button-1>",  open_table)
    root.bind_all("<Button-2>",         quit_app)
    root.bind_all("<Button-3>",         quit_app)
    root.bind_all("<Control-Button-1>", on_ctrl_click)
    # Ctrl++ / Ctrl+= both map to the same physical key (= / +)
    root.bind_all("<Control-equal>",    lambda e: apply_font_size(_cur_size[0] + 1))
    root.bind_all("<Control-plus>",     lambda e: apply_font_size(_cur_size[0] + 1))
    root.bind_all("<Control-minus>",    lambda e: apply_font_size(_cur_size[0] - 1))
    root.bind_all("<Control-0>",        lambda e: apply_font_size(FONT_MAIN[1]))

    root.mainloop()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
