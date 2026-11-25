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


notch = NotchWindow()


class Api:
    """Methods the page can call as window.pywebview.api.<name>(...)."""

    def fit(self, width, height, radius, dpr):
        notch.fit(float(width), float(height), float(radius), float(dpr))


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
    webview.start()


if __name__ == "__main__":
    main()
