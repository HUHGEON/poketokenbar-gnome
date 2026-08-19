"""Sprite fetching — ports SpriteLoader.swift.

Sprites are downloaded at runtime and cached on disk; none are bundled.

The macOS app decodes GIF frames with ImageIO. QML's AnimatedImage plays a GIF
directly, so here the job is only to put a file on disk and hand back its path.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

SPRITE_BASE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon"
USER_AGENT = "poketokenbar/0.1"
# Animated Black/White sprites exist for Gen I-V only.
MAX_ANIMATED_ID = 649


def cache_key(species_id: int, animated: bool, shiny: bool) -> str:
    return f"{species_id}-{'sh' if shiny else ''}{'a' if animated else 's'}"


def sprite_url(species_id: int, animated: bool, shiny: bool) -> str:
    if animated:
        shiny_part = "shiny/" if shiny else ""
        return (
            f"{SPRITE_BASE}/versions/generation-v/black-white/animated/"
            f"{shiny_part}{species_id}.gif"
        )
    return f"{SPRITE_BASE}/{'shiny/' if shiny else ''}{species_id}.png"


class SpriteStore:
    def __init__(self, cache_dir: Path | None = None) -> None:
        base = cache_dir or (Path.home() / ".cache" / "poketokenbar")
        self.dir = base / "sprites"
        self.dir.mkdir(parents=True, exist_ok=True)

    def path(self, species_id: int, animated: bool = True, shiny: bool = False) -> Path | None:
        """Local path to the sprite, downloading it once if needed.

        Returns None when unavailable so the caller can fall back rather than
        render a broken image.
        """
        if animated and species_id > MAX_ANIMATED_ID:
            animated = False

        key = cache_key(species_id, animated, shiny)
        target = self.dir / f"{key}.{'gif' if animated else 'png'}"
        if target.is_file() and target.stat().st_size > 0:
            return target

        request = urllib.request.Request(sprite_url(species_id, animated, shiny))
        request.add_header("User-Agent", USER_AGENT)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.status != 200:
                    return None
                data = response.read()
        except (urllib.error.URLError, TimeoutError, OSError):
            return None
        if not data:
            return None

        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(target)  # atomic — a crash must not leave a torn sprite
        return target
