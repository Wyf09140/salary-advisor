"""Desktop notch app (Windows). Owner: Sophak.

Run:  python -m src.desktop
Shows the island UI from web/index.html docked to the top centre of the primary screen.

How the notch shape works: WebView2 can't be made see-through reliably (it renders on its own
composition layer, which ignores WinForms transparency keys). So instead of a big transparent window,
the window *is* the island: the page reports the island's size, and Python resizes the window to
exactly that, re-centres it at the top edge and clips its bottom corners round with a window region.
Everything outside the island is plain desktop, so clicks there go to other apps.
"""
import ctypes
import os
import sys
import threading
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import webview

from src.config import ROOT
from src.app.server import dispatch

PAGE = ROOT / "web" / "index.html"
START_W, START_H = 560, 430  # expanded Profile panel; corrected by the page's first fit() call


def page_html() -> str:
    """index.html with desktop mode switched on (only the island is drawn, filling the window).
    Set SA_DESKTOP_OPEN=1 to start with the panel open (handy for screenshots and testing)."""
    html = PAGE.read_text(encoding="utf-8")
    classes = "desktop start-open" if os.environ.get("SA_DESKTOP_OPEN") == "1" else "desktop"
    return html.replace('<html lang="en">', f'<html lang="en" class="{classes}">', 1)


class NotchWindow:
    """Keeps the native window the same size and shape as the island."""

    def __init__(self):
        self.window = None
        self._lock = threading.Lock()

    def _form(self):
        try:
            from webview.platforms.winforms import BrowserView
        except ImportError:  # not WinForms (not Windows): shaping not supported
            return None
        return BrowserView.instances.get(self.window.uid) if self.window else None

    def fit(self, width: float, height: float, radius: float, dpr: float) -> None:
        """Called from the page (via the JS bridge) whenever the island changes size.
        Sizes arrive in CSS pixels; the window works in physical pixels, hence * dpr."""
        form = self._form()
        if form is None:
            self.window.resize(int(width), int(height))
            return
        from System import Action
        from System.Drawing import Point, Size
        from System.Windows.Forms import Screen

        w, h, r = round(width * dpr), round(height * dpr), round(radius * dpr)

        def apply():
            area = Screen.PrimaryScreen.Bounds
            form.Size = Size(w, h)
            form.Location = Point(area.X + (area.Width - w) // 2, area.Y)
            # Rounded rect whose top corners sit above the window, so only the bottom corners are round.
            rgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, -r, w + 1, h + 1, 2 * r, 2 * r)
            ctypes.windll.user32.SetWindowRgn(ctypes.c_void_p(form.Handle.ToInt64()), rgn, True)

        with self._lock:
            form.Invoke(Action(apply))


    # ---------- desktop behaviour: hotkey, tray, focus ----------

    def toggle(self) -> None:
        """Open or close the island and bring the window forward so the keyboard goes to it."""
        form = self._form()
        if form is not None:
            from System import Action
            form.Invoke(Action(form.Activate))
        self.window.evaluate_js("window.saToggle && window.saToggle()")

    def setup_shell(self) -> None:
        """Tray icon (Open / Quit), no taskbar button. Runs on the UI thread once the window is shown."""
        form = self._form()
        if form is None:
            return
        from System import Action
        from System.Drawing import Bitmap, Brushes, Color, Font, FontStyle, Graphics, Icon, SolidBrush
        from System.Drawing.Drawing2D import SmoothingMode
        from System.Windows.Forms import ContextMenuStrip, NotifyIcon

        def build():
            hide_from_taskbar(form.Handle.ToInt64())
            bmp = Bitmap(32, 32)
            g = Graphics.FromImage(bmp)
            g.SmoothingMode = SmoothingMode.AntiAlias
            g.FillEllipse(SolidBrush(Color.FromArgb(255, 20, 21, 26)), 0, 0, 31, 31)
            g.DrawString("$", Font("Segoe UI", 15.0, FontStyle.Bold), Brushes.White, 7.0, 1.0)
            g.Dispose()
            menu = ContextMenuStrip()
            menu.Items.Add("Open advisor  (Ctrl+Alt+S)").Click += lambda s, e: self.toggle()
            menu.Items.Add("Quit").Click += lambda s, e: self.window.destroy()
            self.tray = NotifyIcon()
            self.tray.Icon = Icon.FromHandle(bmp.GetHicon())
            self.tray.Text = "Salary Advisor"
            self.tray.ContextMenuStrip = menu
            self.tray.DoubleClick += lambda s, e: self.toggle()
            self.tray.Visible = True

        form.Invoke(Action(build))

    def remove_tray(self) -> None:
        tray = getattr(self, "tray", None)
        if tray is not None:  # otherwise a dead icon lingers in the tray until hovered
            tray.Visible = False
            tray.Dispose()


def hide_from_taskbar(hwnd: int) -> None:
    """Give the window the tool-window style so it has no taskbar button (the tray icon replaces it).
    Done with SetWindowLong rather than WinForms ShowInTaskbar, which recreates the window handle and
    breaks the embedded WebView2. Hide/show makes the taskbar pick up the change."""
    GWL_EXSTYLE, WS_EX_TOOLWINDOW, WS_EX_APPWINDOW = -20, 0x00000080, 0x00040000
    user32, h = ctypes.windll.user32, ctypes.c_void_p(hwnd)
    style = user32.GetWindowLongW(h, GWL_EXSTYLE)
    user32.ShowWindow(h, 0)  # SW_HIDE
    user32.SetWindowLongW(h, GWL_EXSTYLE, (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW)
    user32.ShowWindow(h, 4)  # SW_SHOWNOACTIVATE


def hotkey_loop(on_press, modifiers: int = 0x0002 | 0x0001 | 0x4000, key: int = ord("S")) -> None:
    """Global Ctrl+Alt+S via Win32 RegisterHotKey (no extra packages). Blocks; run in a daemon thread.
    0x0002 = MOD_CONTROL, 0x0001 = MOD_ALT, 0x4000 = MOD_NOREPEAT."""
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    if not user32.RegisterHotKey(None, 1, modifiers, key):
        print("[salary-advisor] Ctrl+Alt+S is taken by another app; use the tray icon instead.", file=sys.stderr)
        return
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        if msg.message == 0x0312:  # WM_HOTKEY
            on_press()


notch = NotchWindow()


class Api:
    """Methods the page can call as window.pywebview.api.<name>(...)."""

    def fit(self, width, height, radius, dpr):
        notch.fit(float(width), float(height), float(radius), float(dpr))

    def call(self, path, body=None):
        """Same API as the web server (/api/skills, /api/estimate, /api/parse-resume), minus HTTP."""
        status, data = dispatch(str(path), body)
        return {"status": status, "data": data}


def main() -> None:
    screen = webview.screens[0]
    notch.window = webview.create_window(
        "Salary Advisor",
        html=page_html(),
        js_api=Api(),
        width=START_W, height=START_H,
        x=(screen.width - START_W) // 2, y=0,
        min_size=(120, 30),  # default (200, 100) would stop the window shrinking to the 38 px pill
        frameless=True, easy_drag=False, on_top=True, resizable=False, shadow=False,
        background_color="#121318",  # same as the island, so a resize never flashes another colour
    )
    notch.window.events.shown += notch.setup_shell
    notch.window.events.closed += notch.remove_tray
    if sys.platform == "win32":
        threading.Thread(target=hotkey_loop, args=(notch.toggle,), daemon=True).start()
    webview.start()


if __name__ == "__main__":
    main()
