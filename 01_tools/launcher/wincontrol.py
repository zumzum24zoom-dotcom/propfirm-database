"""Win32 helpers: clipboard read/write and sidebar window show/hide/topmost."""
from __future__ import annotations

import io
import struct
import time

import win32api
import win32clipboard
import win32con
import win32gui
from PIL import Image

# AnimateWindow (AW_SLIDE) is ignored by DWM for top-level windows owned by
# another process - it just shows/hides instantly with DWM's own fade.
# Instead, slide manually by repositioning the window in small steps.
SLIDE_STEPS = 12
SLIDE_STEP_DELAY = 0.012  # ~144ms total

CF_PNG = None  # registered lazily (must run after OpenClipboard-capable thread init)


def _cf_png() -> int:
    global CF_PNG
    if CF_PNG is None:
        CF_PNG = win32clipboard.RegisterClipboardFormat("PNG")
    return CF_PNG


def read_clipboard() -> tuple[str | None, object]:
    """Return ('text', str), ('image', png_bytes) or (None, None).

    OpenClipboard commonly fails transiently (access denied) right when
    WM_CLIPBOARDUPDATE is delivered, because the process that just changed
    the clipboard may still hold its lock. Retry briefly before giving up.
    """
    for attempt in range(5):
        try:
            win32clipboard.OpenClipboard()
            break
        except win32clipboard.error:
            if attempt == 4:
                return None, None
            time.sleep(0.02)
    try:
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
            dib = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
            return "image", _dib_to_png(dib)
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
            text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            return "text", text
    finally:
        win32clipboard.CloseClipboard()
    return None, None


def _dib_to_png(dib_bytes: bytes) -> bytes:
    bmp_header = struct.pack("<2sIHHI", b"BM", 14 + len(dib_bytes), 0, 0, 14 + 40)
    img = Image.open(io.BytesIO(bmp_header + dib_bytes))
    out = io.BytesIO()
    img.convert("RGBA").save(out, format="PNG")
    return out.getvalue()


def write_text(text: str) -> None:
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, text)
    finally:
        win32clipboard.CloseClipboard()


def write_image(png_bytes: bytes) -> None:
    img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    out = io.BytesIO()
    img.save(out, format="BMP")
    bmp_data = out.getvalue()[14:]  # strip BITMAPFILEHEADER
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
        win32clipboard.SetClipboardData(_cf_png(), png_bytes)
    finally:
        win32clipboard.CloseClipboard()


def find_sidebar_window(title_substr: str) -> int | None:
    found = []

    def cb(hwnd, _):
        if win32gui.GetClassName(hwnd) == "Chrome_WidgetWin_1" and title_substr in win32gui.GetWindowText(hwnd):
            found.append(hwnd)

    win32gui.EnumWindows(cb, None)
    return found[0] if found else None


def _slide_to(hwnd: int, x_from: int, x_to: int, y: int, w: int, h: int) -> None:
    for i in range(1, SLIDE_STEPS + 1):
        x = x_from + (x_to - x_from) * i // SLIDE_STEPS
        win32gui.SetWindowPos(hwnd, 0, x, y, w, h, win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)
        time.sleep(SLIDE_STEP_DELAY)


def toggle_visibility(hwnd: int) -> str:
    """Show/hide the sidebar by sliding it horizontally off/on the right screen edge."""
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    w, h = right - left, bottom - top
    screen_w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    docked_x = screen_w - w
    offscreen_x = screen_w

    if win32gui.IsWindowVisible(hwnd):
        _slide_to(hwnd, docked_x, offscreen_x, top, w, h)
        win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
        return "hidden"

    win32gui.SetWindowPos(hwnd, 0, offscreen_x, top, w, h, win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)
    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    _slide_to(hwnd, offscreen_x, docked_x, top, w, h)
    try:
        win32gui.SetForegroundWindow(hwnd)
    except win32gui.error:
        pass  # foreground-lock restrictions can reject this; window is still shown
    return "shown"


def set_rect(hwnd: int, x: int, y: int, w: int, h: int) -> None:
    win32gui.SetWindowPos(hwnd, 0, x, y, w, h, win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)


def set_topmost(hwnd: int, on: bool) -> None:
    flag = win32con.HWND_TOPMOST if on else win32con.HWND_NOTOPMOST
    win32gui.SetWindowPos(hwnd, flag, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)


def is_topmost(hwnd: int) -> bool:
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    return bool(ex_style & win32con.WS_EX_TOPMOST)
