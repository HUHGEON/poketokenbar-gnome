"""Burn-rate forecast — when the current limit window will hit 100%.

The macOS app derives this from ccusage's `burnRate.tokensPerMinute`. We have
no ccusage, and the token→percent mapping is not published, so tokens/minute
cannot be converted into percent/minute.

Instead this samples the utilization percentage the API already reports and
fits a slope to it. That measures the thing we actually want to project, needs
no mapping, and stays correct even if Anthropic changes how usage is weighted.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass

# Ignore samples older than this: a 5-hour window's early burn says little
# about the last hour.
WINDOW_SECONDS = 45 * 60
# Below this the slope is noise, not a trend.
MIN_SAMPLES = 3
# Percent-per-minute under which a forecast is meaningless (would be days out).
MIN_RATE = 0.01


@dataclass(slots=True)
class Forecast:
    rate_per_minute: float
    minutes_to_full: float | None
    eta_epoch: float | None

    @property
    def eta_text(self) -> str:
        if self.eta_epoch is None:
            return ""
        return time.strftime("%H:%M", time.localtime(self.eta_epoch))


class BurnTracker:
    """Keeps a short history of utilization samples per window kind."""

    def __init__(self, clock=time.time) -> None:
        self._clock = clock
        self._samples: dict[str, deque] = {}

    def record(self, kind: str, utilization: float) -> None:
        now = self._clock()
        series = self._samples.setdefault(kind, deque())
        # A window reset makes utilization drop sharply. Keeping the old, higher
        # samples would compute a negative slope and forecast nothing at all.
        if series and utilization < series[-1][1] - 1.0:
            series.clear()
        series.append((now, utilization))
        while series and now - series[0][0] > WINDOW_SECONDS:
            series.popleft()

    def forecast(self, kind: str) -> Forecast | None:
        series = self._samples.get(kind)
        if not series or len(series) < MIN_SAMPLES:
            return None

        first_t, first_u = series[0]
        last_t, last_u = series[-1]
        elapsed_minutes = (last_t - first_t) / 60.0
        if elapsed_minutes <= 0:
            return None

        rate = (last_u - first_u) / elapsed_minutes
        if rate < MIN_RATE:
            # Flat or falling: no meaningful ETA, but report the rate so the UI
            # can still say "holding steady".
            return Forecast(rate_per_minute=max(0.0, rate), minutes_to_full=None, eta_epoch=None)

        remaining = max(0.0, 100.0 - last_u)
        minutes = remaining / rate
        return Forecast(
            rate_per_minute=rate,
            minutes_to_full=minutes,
            eta_epoch=self._clock() + minutes * 60.0,
        )

    def payload(self, kinds=("session", "weekly")) -> dict:
        out = {}
        for kind in kinds:
            forecast = self.forecast(kind)
            if forecast is None:
                continue
            out[kind] = {
                "rate_per_minute": round(forecast.rate_per_minute, 4),
                "minutes_to_full": (
                    round(forecast.minutes_to_full) if forecast.minutes_to_full else None
                ),
                "eta_text": forecast.eta_text,
            }
        return out
