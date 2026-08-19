"""Provider extension point — ports UsageProvider.swift.

Adding a source means adding an implementation and a PROVIDERS entry. Never
branch on a provider id in shared code; see docs/reference/provider-extension.md.
"""

from __future__ import annotations

from typing import Protocol

from ..models import DailyUsage, ProviderEnrichment


class UsageProvider(Protocol):
    id: str
    display_name: str
    reports_cost: bool

    def fetch_daily(self, today: str | None = None) -> DailyUsage | None:
        """Today's totals. None when the source is absent or unused today."""
        ...

    def fetch_enrichment(self) -> ProviderEnrichment:
        """Blocks and period totals. Best effort; never raises."""
        ...
