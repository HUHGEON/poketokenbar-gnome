"""The small pieces the panels are built from.

Qt plays a GIF natively through QMovie, so unlike the GNOME front end there is
no frame decoding here at all — the animated Gen-V sprites are handed to Qt as
files and it does the rest.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QMovie, QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

# Utilisation bands, matching limits.level() in the daemon. Stated outright
# rather than taken from the palette: "close to your limit" has to read as a
# warning whatever theme is in use.
LEVEL_COLOURS = {
    "ok": "#3fb950",
    "warn": "#d29922",
    "crit": "#f85149",
}


def level_colour(level: str | None) -> str:
    return LEVEL_COLOURS.get(level or "ok", LEVEL_COLOURS["ok"])


class Sprite(QLabel):
    """An animated sprite.

    A repeat of the same path is a no-op: rebuilding the QMovie on every poll
    would restart the animation from frame one every two seconds, so the
    companion would visibly stutter rather than loop.
    """

    def __init__(self, size: int = 64, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._size = size
        self._path: str | None = None
        self._movie: QMovie | None = None
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(size, size)

    def set_path(self, path: str | None) -> None:
        if path == self._path:
            return
        self._path = path
        if self._movie is not None:
            self._movie.stop()
            self._movie = None
        if not path:
            self.clear()
            return

        movie = QMovie(path)
        if movie.isValid():
            # Scaled here rather than by the label: QMovie renders at its own
            # size and a scaledContents label would resample every frame.
            movie.setScaledSize(QSize(self._size, self._size))
            self._movie = movie
            self.setMovie(movie)
            movie.start()
            return

        # A still PNG, or a GIF Qt could not read. Either way one frame beats
        # a blank square.
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.clear()
            return
        self.setPixmap(pixmap.scaled(
            self._size, self._size, Qt.KeepAspectRatio, Qt.FastTransformation))

    def set_paused(self, paused: bool) -> None:
        """Stop animating without discarding the movie.

        The window spends most of its life hidden in the tray, and a sprite
        nobody can see should not be costing frames.
        """
        if self._movie is None:
            return
        self._movie.setPaused(paused)


def label(text: str = "", *, dim: bool = False, bold: bool = False,
          colour: str | None = None, size: int | None = None) -> QLabel:
    widget = QLabel(text)
    parts = []
    if bold:
        parts.append("font-weight: bold")
    if colour:
        parts.append(f"color: {colour}")
    if size:
        parts.append(f"font-size: {size}px")
    if dim:
        parts.append("color: palette(mid)")
    if parts:
        widget.setStyleSheet("; ".join(parts))
    widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return widget


def heading(text: str) -> QLabel:
    return label(text, bold=True)


def row(*widgets: QWidget) -> QWidget:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    for widget in widgets:
        layout.addWidget(widget)
    return container


def stat_line(name: str, value: str, colour: str | None = None) -> QWidget:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(label(name, dim=True))
    layout.addStretch(1)
    layout.addWidget(label(value, colour=colour))
    return container


def meter(fraction: float, level: str | None = None) -> QProgressBar:
    bar = QProgressBar()
    bar.setRange(0, 100)
    # Clamped so a limit past 100% still reads as full rather than wrapping.
    bar.setValue(max(0, min(100, round((fraction or 0) * 100))))
    bar.setTextVisible(False)
    bar.setFixedHeight(6)
    bar.setStyleSheet(
        "QProgressBar { border: none; background: palette(alternate-base); }"
        f"QProgressBar::chunk {{ background: {level_colour(level)}; }}"
    )
    return bar


def button(text: str, on_click, enabled: bool = True) -> QPushButton:
    widget = QPushButton(text)
    widget.clicked.connect(on_click)
    widget.setEnabled(enabled)
    return widget


def separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line


def card(*widgets: QWidget) -> QWidget:
    container = QWidget()
    container.setStyleSheet(
        "background: palette(alternate-base); border-radius: 6px;")
    layout = QHBoxLayout(container)
    layout.setContentsMargins(8, 6, 8, 6)
    for widget in widgets:
        layout.addWidget(widget)
    return container


def column(*widgets: QWidget) -> QWidget:
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)
    for widget in widgets:
        layout.addWidget(widget)
    return container


def clear_layout(layout) -> None:
    """Empty a layout, destroying what was in it.

    `deleteLater` rather than a plain drop: a widget removed from its layout is
    still parented and still painted until Qt collects it, so without this a
    rebuilt panel shows both versions at once.
    """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
