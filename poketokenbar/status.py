"""Provider incident status — ports ProviderStatusChecker.swift.

Reads the public Statuspage summary endpoints. Purely informational: shown in
the popup, never as a notification, and a failure leaves the section hidden
rather than reporting a false outage.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable

ENDPOINTS = {
    "claude": "https://status.anthropic.com/api/v2/status.json",
    "openai": "https://status.openai.com/api/v2/status.json",
}
USER_AGENT = "poketokenbar/0.1"

# Statuspage indicator -> (label, severity). "none" means operational.
INDICATORS = {
    "none": ("Operational", "ok"),
    "minor": ("Minor issues", "warn"),
    "major": ("Major outage", "crit"),
    "critical": ("Critical outage", "crit"),
    "maintenance": ("Maintenance", "warn"),
}

TTL_SECONDS = 600.0


def _fetch(url: str, timeout: float = 10.0) -> dict:
    request = urllib.request.Request(url)
    request.add_header("User-Agent", USER_AGENT)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


class StatusChecker:
    def __init__(self, fetch: Callable[[str], dict] = _fetch, clock=time.monotonic) -> None:
        self._fetch = fetch
        self._clock = clock
        self._cached: dict = {}
        self._fetched_at: float | None = None

    def get(self) -> dict:
        """Current status per provider, cached for TTL_SECONDS.

        Only providers that answered are included — an unreachable status page
        means "unknown", which must not render as an outage.
        """
        now = self._clock()
        if self._fetched_at is not None and (now - self._fetched_at) < TTL_SECONDS:
            return self._cached

        out: dict = {}
        for key, url in ENDPOINTS.items():
            try:
                payload = self._fetch(url)
            except (urllib.error.URLError, TimeoutError, OSError, ValueError):
                continue
            indicator = ((payload or {}).get("status") or {}).get("indicator")
            label, severity = INDICATORS.get(indicator, ("Status unknown", "unknown"))
            if severity == "ok":
                continue  # only surface problems; a healthy service needs no row
            out[key] = {"label": label, "severity": severity, "indicator": indicator}

        self._cached = out
        self._fetched_at = now
        return out
