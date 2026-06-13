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

# Show/hide is animated with an opacity fade rather than a positional slide.
# A slide has to move the window across the right screen edge, and DWM does not
# composite the off-screen portion per-frame for another process's window, so
# the slide collapses into an instant pop. Fading the layered-window alpha is
# fully on-screen and renders reliably cross-process.
FADE_STEPS = 14
FADE_STEP_DELAY = 0.016  # ~224ms total

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


def list_chrome_windows() -> set[int]:
    """Visible top-level Chrome/Edge windows (class Chrome_WidgetWin_1).

    Used to diff the window set before/after launching a tool so the newly
    spawned --app window can be located and force-sized (Chrome ignores
    --window-size/--window-position once a profile has saved bounds)."""
    found: set[int] = set()

    def cb(hwnd, _):
        if win32gui.GetClassName(hwnd) == "Chrome_WidgetWin_1" and win32gui.IsWindowVisible(hwnd):
            found.add(hwnd)

    win32gui.EnumWindows(cb, None)
    return found


def _set_alpha(hwnd: int, alpha: int) -> None:
    ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    if not (ex & win32con.WS_EX_LAYERED):
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex | win32con.WS_EX_LAYERED)
    win32gui.SetLayeredWindowAttributes(hwnd, 0, max(0, min(255, alpha)), win32con.LWA_ALPHA)


def _fade(hwnd: int, a_from: int, a_to: int) -> None:
    for i in range(1, FADE_STEPS + 1):
        t = i / FADE_STEPS
        a = int(round(a_from + (a_to - a_from) * t))
        _set_alpha(hwnd, a)
        time.sleep(FADE_STEP_DELAY)


def fade_in(hwnd: int, x: int, y: int, w: int, h: int) -> None:
    """Position the window at its docked rect and fade it in from transparent.

    Used for the initial launch: Chrome shows the window at its remembered spot
    the instant it is created, so we set alpha to 0 first (still hidden), then
    show and ramp the opacity up for a clean fade-in instead of a pop."""
    _set_alpha(hwnd, 0)
    win32gui.SetWindowPos(hwnd, 0, x, y, w, h, win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)
    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    _fade(hwnd, 0, 255)
    _force_foreground(hwnd)


def toggle_visibility(hwnd: int) -> str:
    """Show/hide the sidebar with an opacity fade (stays docked in place)."""
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    w, h = right - left, bottom - top
    screen_w = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    docked_x = screen_w - w

    if win32gui.IsWindowVisible(hwnd):
        _fade(hwnd, 255, 0)
        win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
        _set_alpha(hwnd, 255)  # restore so a later non-fade show isn't invisible
        return "hidden"

    fade_in(hwnd, docked_x, top, w, h)
    return "shown"


def _force_foreground(hwnd: int) -> None:
    """Windowsのフォアグラウンドロックを回避してフォーカスを奪う。

    SetForegroundWindowは別プロセス（前景アプリ）のスレッドに紐付かないと
    拒否されることが多い。前景ウィンドウのスレッドにAttachThreadInputで
    一時的に接続してからSetForegroundWindowすれば確実に奪える。
    """
    import ctypes
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    fg = user32.GetForegroundWindow()
    fg_tid = user32.GetWindowThreadProcessId(fg, None) if fg else 0
    cur_tid = kernel32.GetCurrentThreadId()
    attached = False
    if fg_tid and fg_tid != cur_tid:
        attached = bool(user32.AttachThreadInput(cur_tid, fg_tid, True))
    try:
        try:
            win32gui.SetForegroundWindow(hwnd)
        except win32gui.error:
            user32.BringWindowToTop(hwnd)
        user32.SetFocus(hwnd)
    finally:
        if attached:
            user32.AttachThreadInput(cur_tid, fg_tid, False)


def set_rect(hwnd: int, x: int, y: int, w: int, h: int) -> None:
    win32gui.SetWindowPos(hwnd, 0, x, y, w, h, win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)


def set_topmost(hwnd: int, on: bool) -> None:
    flag = win32con.HWND_TOPMOST if on else win32con.HWND_NOTOPMOST
    win32gui.SetWindowPos(hwnd, flag, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)


def is_topmost(hwnd: int) -> bool:
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    return bool(ex_style & win32con.WS_EX_TOPMOST)
