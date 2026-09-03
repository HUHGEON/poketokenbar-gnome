"""The companion, living on the desktop.

A frameless always-on-top window rather than an actor on a compositor's stage,
which is what the GNOME front end gets to use. Windows has no equivalent of that
and no equivalent of Wayland's refusal to let a client place its own window
either, so the plain approach works: a borderless translucent widget positioned
wherever it was last left.

Hover shows today's usage, click opens the main window, drag moves it, and the
position is written back through the daemon's own config so it survives a
reboot.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from .widgets import Sprite, label

# How far a press may travel and still count as a click rather than a drag.
# Without it every click ends as a one-pixel drag and the window never opens.
CLICK_SLOP = 4

DEFAULT_SIZE = 96

# Shown until a sprite has been fetched even once.
FALLBACK_GLYPH = "\N{EGG}"


class DesktopPet(QWidget):
    def __init__(self, on_activate=None, on_moved=None) -> None:
        super().__init__()
        self._on_activate = on_activate or (lambda: None)
        self._on_moved = on_moved or (lambda x, y: None)
        self._press: QPoint | None = None
        self._dragging = False
        self._tooltip_text = ""
        # The last path that actually resolved to a file. A sprite the daemon
        # could not download comes through as "", and drawing that meant an
        # invisible window — so the pet vanished and came back as the network
        # flapped, which is the same thing as "it keeps disappearing".
        self._last_sprite = ""

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            # Keeps it off the taskbar and out of Alt-Tab: it is an ornament,
            # not a window someone switches to.
            | Qt.Tool
            # And it must never become the active window. Windows owns a tool
            # window to whichever window of the application was last active, so
            # a pet that takes activation on click becomes owned by the popup —
            # and vanishes with it the moment the popup is closed again. That
            # is the "it disappears when I click it" report.
            | Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Same reason, for the show() that follows: showing a window normally
        # activates it.
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.NoFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.sprite = Sprite(DEFAULT_SIZE)
        layout.addWidget(self.sprite)
        self.set_size(DEFAULT_SIZE)

    # --- state -------------------------------------------------------------

    def set_size(self, size: int) -> None:
        self.sprite.setFixedSize(size, size)
        self.sprite._size = size
        self.setFixedSize(size, size)

    def update_state(self, state: dict | None) -> None:
        panel = (state or {}).get("panel") or {}
        # Follows the panel, so a pinned species shows here too — the daemon has
        # already resolved which one that is. An empty path is a fetch that has
        # not succeeded yet, never a decision to show nothing, so the last one
        # that worked stays up rather than the pet blanking.
        path = panel.get("sprite_path") or ""
        if path:
            self._last_sprite = path
        # Before the first sprite ever arrives — a fresh install with no
        # network — the glyph is what stands in. An empty translucent window
        # is indistinguishable from the pet being gone.
        self.sprite.set_fallback(FALLBACK_GLYPH)
        self.sprite.set_path(self._last_sprite or None)

        config = (state or {}).get("config") or {}
        size = int(config.get("floating_pet_size") or DEFAULT_SIZE)
        if size != self.width():
            self.set_size(size)
        # Both always-visible surfaces share one quality setting, as upstream's
        # do: a frame costs a redraw wherever it is drawn.
        from .widgets import quality_of

        self.sprite.set_quality(quality_of(config))

        today = (state or {}).get("today") or {}
        self._tooltip_text = today.get("tokens_grouped", "")
        self.setToolTip(self._tooltip_text)

    def place(self, x: int, y: int) -> None:
        """Move the pet, clamped so it cannot end up off every screen.

        A position saved on a monitor that is no longer attached would
        otherwise leave it invisible with no way to get it back.
        """
        screen = self.screen() or self.parentWidget()
        if screen is not None and hasattr(screen, "availableGeometry"):
            area = screen.availableGeometry()
            x = max(area.left(), min(int(x), area.right() - self.width()))
            y = max(area.top(), min(int(y), area.bottom() - self.height()))
        self.move(int(x), int(y))

    # --- interaction --------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._press = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._dragging = False
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        if self._press is None:
            return
        target = event.globalPosition().toPoint() - self._press
        if not self._dragging:
            travelled = (target - self.pos()).manhattanLength()
            if travelled < CLICK_SLOP:
                return
            self._dragging = True
        self.place(target.x(), target.y())
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if self._press is None:
            return
        was_dragging = self._dragging
        self._press = None
        self._dragging = False
        if was_dragging:
            self._on_moved(self.x(), self.y())
        else:
            self._on_activate()
        event.accept()
