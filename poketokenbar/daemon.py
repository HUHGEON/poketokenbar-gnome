"""poketokend — polls providers, writes state.json, drains commands."""

from __future__ import annotations

import os
import time
from pathlib import Path

from . import commands, config, state
from .limits_source import LimitsSource
from .cache import ScanCache
from .models import DailyUsage


class Daemon:
    def __init__(
        self, state_path: Path, config_path: Path, cache, providers, limits_source=None
    ) -> None:
        self.state_path = state_path
        self.config_path = config_path
        self.cache = cache
        self.providers = providers
        # Injected so tests never reach the network. None disables limits.
        self.limits_source = limits_source
        self.spool: Path | None = None
        self.config_values = config.load(config_path)

    def poll_once(self) -> dict:
        for command in commands.drain(spool=self.spool):
            if command.get("name") == "reload_config":
                self.config_values = config.load(self.config_path)

        daily_by_provider: dict[str, DailyUsage] = {}
        errors: list[str] = []
        for provider in self.providers:
            try:
                daily = provider.fetch_daily()
            except Exception as exc:  # per-provider isolation
                errors.append(f"{provider.id}: {exc}")
                continue
            if daily is not None:
                daily_by_provider[provider.id] = daily

        limit_status = None
        if self.limits_source is not None:
            # Best effort: limits failing hides that section but must never
            # affect the token counts, which come from local logs.
            limit_status = self.limits_source.get()
            if self.limits_source.last_error:
                errors.append(f"limits: {self.limits_source.last_error}")

        payload = state.build(
            daily_by_provider, self.config_values, errors, limit_status=limit_status
        )
        state.write(self.state_path, payload)
        return payload

    def run(self) -> None:
        while True:
            self.poll_once()
            interval = int(self.config_values.get("refresh_interval", 120))
            # Sleep in short slices so a queued command is picked up promptly
            # without re-scanning the logs every second.
            waited = 0
            while waited < interval:
                time.sleep(min(2, interval - waited))
                waited += 2
                if self._has_commands():
                    break

    def _has_commands(self) -> bool:
        spool = self.spool or commands.spool_dir()
        return spool.is_dir() and any(spool.glob("*.json"))


def main() -> int:
    from .providers.claude import ClaudeProvider

    cache_base = os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
    cache = ScanCache(Path(cache_base) / "poketokenbar" / "scan.db")
    daemon = Daemon(
        state_path=state.default_path(),
        config_path=config.default_path(),
        cache=cache,
        providers=[ClaudeProvider(cache=cache)],
        limits_source=LimitsSource(),
    )
    try:
        daemon.run()
    except KeyboardInterrupt:
        return 0
    finally:
        cache.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
