"""The tray application constructs on Windows.

Offscreen, so nothing is displayed; what this shows is that the Qt classes the
tray uses exist and behave the same way on the platform it was written for as
they do in the container the tests run in.
"""

import sys
from pathlib import Path

# Run as `python tools/x.py` from the repo root, which puts tools/ on the path
# and not the package beside it.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication

from poketokenbar.ui.app import TrayApp
from poketokenbar.ui.reader import StateReader


def main() -> int:
    app = QApplication([])
    tray = TrayApp(app, StateReader())
    tray.poll()
    window = tray.window
    window.refresh(tray.reader.state)

    print(f"  tooltip : {tray.tray.toolTip()}")
    print(f"  menu    : {[action.text() for action in tray.tray.contextMenu().actions()]}")
    print(f"  tabs    : {[item.text() for item in window.tabs._buttons.values()]}")

    # Every page has to build, not just the one that happens to be shown: a
    # panel that raises on this platform would otherwise be found by whoever
    # clicked the tab.
    for name in window.panels:
        window.show_tab(name)
    window.show_settings()
    window.show_tab("home")
    print(f"  pages   : {list(window.panels)} + settings")

    # A tray entry with no icon is invisible, and then there is no way to open
    # the window at all.
    assert not tray.tray.icon().isNull(), "the tray icon is empty"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
