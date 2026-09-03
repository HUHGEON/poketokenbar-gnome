"""The tray icon and the window it opens.

Windows has no panel to extend, so the companion lives in the notification
area: the tray icon is the sprite, its tooltip carries today's numbers, and
clicking it opens the tabs.

The window is hidden rather than closed. Recreating it on every open would
throw away the Pokedex page someone was on and restart every sprite, and on
Windows a closed tray app that is still running is the normal shape.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QIcon, QMovie, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMenu, QSystemTrayIcon, QTabWidget, QVBoxLayout, QWidget,
)

from .. import commands, config
from .pet import DesktopPet
from .panels import (
    BagPanel, CollectionPanel, HomePanel, SettingsPanel, ShopPanel, ago,
)
from .reader import StateReader
from .widgets import label, quality_of

# The window is a fixed width so the Pokedex grid never reflows mid-browse.
WINDOW_SIZE = (420, 620)
# Matches the daemon's own default refresh, which is what actually changes the
# file — polling faster only re-reads the same bytes.
POLL_MILLISECONDS = 2000
# Tray icons are small; the sprite is scaled to this.
TRAY_ICON_SIZE = 22


class Window(QWidget):
    """The tabs, plus a footer that says whether the daemon is alive."""

    def __init__(self, reader: StateReader) -> None:
        super().__init__()
        self.reader = reader
        self.setWindowTitle("PokeTokenBar")
        self.resize(*WINDOW_SIZE)

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.panels = {
            "home": HomePanel(reader),
            "shop": ShopPanel(reader),
            "bag": BagPanel(reader),
            "collection": CollectionPanel(reader),
            "settings": SettingsPanel(reader),
        }
        for key, panel in self.panels.items():
            self.tabs.addTab(panel, self._tab_title(key))
        layout.addWidget(self.tabs)

        self.footer = label("", dim=True)
        layout.addWidget(self.footer)

    def _tab_title(self, key: str) -> str:
        # "Settings" is the extension's own word; the rest come from the
        # daemon's catalogue.
        return "Settings" if key == "settings" else self.reader.text(key)

    def _retitle_tabs(self) -> None:
        """Re-label the tabs from the current catalogue.

        They are created before the first successful read, when `text()` still
        returns the key itself — so without this the tabs read "home", "shop",
        "bag" in lower case forever, and a language change never reaches them.
        """
        for index, key in enumerate(self.panels):
            title = self._tab_title(key)
            if self.tabs.tabText(index) != title:
                self.tabs.setTabText(index, title)

    def refresh(self, state: dict | None) -> None:
        self._retitle_tabs()
        # Only the visible tab is rebuilt: the others would throw their children
        # away again before anyone saw them.
        current = self.tabs.currentWidget()
        for panel in self.panels.values():
            if panel is current:
                panel.update(state)
        self.footer.setText(self._footer_text(state))

    def _footer_text(self, state: dict | None) -> str:
        if self.reader.error:
            return self.reader.error
        if self.reader.is_stale():
            return self.reader.text("stale_warning")
        errors = (state or {}).get("errors") or []
        if errors:
            return ", ".join(errors)
        if (state or {}).get("scanning"):
            return "scanning…"
        age = self.reader.age_seconds()
        return "" if age is None else f"Updated {ago(age)}"


class TrayApp:
    """Wires the reader, the tray icon and the window together."""

    def __init__(self, app: QApplication, reader: StateReader | None = None) -> None:
        self.app = app
        self.reader = reader or StateReader()
        self.window = Window(self.reader)
        self._sprite_path: str | None = None
        self._movie: QMovie | None = None

        # Created only when the setting is on, and destroyed when it goes off.
        self.pet: DesktopPet | None = None

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self._fallback_icon())
        self.tray.setContextMenu(self._menu())
        self.tray.activated.connect(self._on_activated)

        self.timer = QTimer()
        self.timer.setInterval(POLL_MILLISECONDS)
        self.timer.timeout.connect(self.poll)

    def _menu(self) -> QMenu:
        menu = QMenu()
        show = QAction("Open", menu)
        show.triggered.connect(self.toggle_window)
        menu.addAction(show)

        refresh = QAction("Refresh", menu)
        refresh.triggered.connect(lambda: commands.enqueue("refresh", {}))
        menu.addAction(refresh)

        menu.addSeparator()
        # The daemon has handled these all along; without a control they were
        # reachable only from poketokenctl, which is not where anyone would look
        # for "move my Pokedex to another machine".
        export = QAction("Export save", menu)
        export.triggered.connect(
            lambda: commands.enqueue("export", {"path": str(self.save_path())}))
        menu.addAction(export)

        import_action = QAction("Import save", menu)
        import_action.triggered.connect(
            lambda: commands.enqueue("import", {"path": str(self.save_path())}))
        menu.addAction(import_action)

        menu.addSeparator()
        quit_action = QAction("Quit", menu)
        # Quits this window only. The daemon is a separate process and keeps
        # counting — closing the view must not lose someone's progress.
        quit_action.triggered.connect(self.app.quit)
        menu.addAction(quit_action)
        return menu

    def save_path(self):
        """Where a save is written to and read from.

        A fixed, predictable path rather than a file dialog: the export is
        triggered from a tray menu, and a modal file chooser from there is more
        ceremony than moving a Pokedex is worth.
        """
        from pathlib import Path

        return Path.home() / "poketokenbar-save.json"

    def _fallback_icon(self) -> QIcon:
        """A blank icon, so the tray entry exists before the first sprite.

        Without one the tray shows nothing at all and there is no way to open
        the window — which looks exactly like a crash.
        """
        pixmap = QPixmap(TRAY_ICON_SIZE, TRAY_ICON_SIZE)
        pixmap.fill(Qt.transparent)
        return QIcon(pixmap)

    def start(self) -> None:
        self.tray.show()
        self.poll()
        self.timer.start()

    def poll(self) -> None:
        state = self.reader.read()
        self._update_tray(state)
        self._sync_pet(state)
        if self.window.isVisible():
            self.window.refresh(state)

    def _sync_pet(self, state: dict | None) -> None:
        """Create, update or remove the pet to match the daemon's settings.

        Removed rather than hidden when it is switched off: a hidden always-on-
        top window still exists, and the setting is meant to mean "not there".
        """
        wanted = bool(((state or {}).get("config") or {}).get("floating_pet_enabled"))
        if not wanted:
            if self.pet is not None:
                self.pet.close()
                self.pet = None
            return

        if self.pet is None:
            self.pet = DesktopPet(
                on_activate=self.toggle_window,
                on_moved=self._remember_pet_position,
            )
            config_values = (state or {}).get("config") or {}
            self.pet.update_state(state)
            self.pet.place(
                int(config_values.get("floating_pet_x") or 80),
                int(config_values.get("floating_pet_y") or 80),
            )
            self.pet.show()
        else:
            self.pet.update_state(state)

    def _remember_pet_position(self, x: int, y: int) -> None:
        # Through the daemon's own config, so the pet comes back where it was
        # left — including after a reboot.
        config.set_value(config.default_path(), "floating_pet_x", str(x))
        config.set_value(config.default_path(), "floating_pet_y", str(y))
        commands.enqueue("reload_config", {})

    def _update_tray(self, state: dict | None) -> None:
        panel = (state or {}).get("panel") or {}
        # The pinned species when there is one, else the companion: the daemon
        # has already resolved that, so this only has to draw it.
        path = panel.get("sprite_path") or None
        if path != self._sprite_path:
            self._sprite_path = path
            self._set_icon(path)
        self.tray.setToolTip(self._tooltip(state))

    def _apply_quality(self, state: dict | None) -> None:
        quality = quality_of((state or {}).get("config"))
        if self.pet is not None:
            self.pet.sprite.set_quality(quality)

    def _set_icon(self, path: str | None) -> None:
        if not path:
            self.tray.setIcon(self._fallback_icon())
            return
        # A still frame, not the animation: Qt has no animated QIcon, and a
        # tray icon redrawn per frame is a wakeup per frame for something the
        # size of a thumbnail.
        movie = QMovie(path)
        if movie.isValid():
            movie.jumpToFrame(0)
            pixmap = movie.currentPixmap()
        else:
            pixmap = QPixmap(path)
        if pixmap.isNull():
            self.tray.setIcon(self._fallback_icon())
            return
        self.tray.setIcon(QIcon(pixmap.scaled(
            TRAY_ICON_SIZE, TRAY_ICON_SIZE, Qt.KeepAspectRatio, Qt.FastTransformation)))

    def _tooltip(self, state: dict | None) -> str:
        panel = (state or {}).get("panel") or {}
        parts = [panel.get("tokens_text"), panel.get("cost_text")]
        parts += [window["text"] for window in panel.get("limit_windows") or []]
        text = " · ".join(part for part in parts if part)
        return text or "PokeTokenBar"

    def _on_activated(self, reason) -> None:
        # Middle-click and hover are not "open": on Windows a hover fires this
        # too, and a window that appears under the cursor is startling.
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.toggle_window()

    def toggle_window(self) -> None:
        if self.window.isVisible():
            self.window.hide()
            return
        self.window.refresh(self.reader.state)
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()


def main(argv: list[str] | None = None) -> int:
    app = QApplication(argv if argv is not None else sys.argv)
    # Closing the window leaves the tray icon behind rather than ending the
    # process, which is what a tray application is for.
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("PokeTokenBar")

    tray = TrayApp(app)
    tray.start()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
