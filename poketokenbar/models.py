"""Usage data models — ports Sources/PokeTokenBar/Core/Models.swift."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Entry:
    """One assistant turn's token usage, as parsed from a provider log line."""

    id: str
    date: datetime
    local_day: str
    model: str
    input: int = 0
    output: int = 0
    cache_write: int = 0
    cache_read: int = 0
    # Some agents persist the exact charge alongside token usage (omp, Grok,
    # OpenCode). Prefer it over the model price table so a local report matches
    # what the tool itself billed. Only a value > 0 counts: free or unpriced
    # models are written as 0, which means "no figure", not "cost nothing".
    explicit_cost: float | None = None

    @property
    def total(self) -> int:
        return self.input + self.output + self.cache_write + self.cache_read


@dataclass(slots=True)
class DailyUsage:
    date: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


@dataclass(slots=True)
class BlockUsage:
    id: str
    start_time: str
    end_time: str
    is_active: bool = False
    total_tokens: int = 0
    cost_usd: float = 0.0
    tokens_per_minute: float | None = None


@dataclass(slots=True)
class PeriodUsage:
    period: str
    total_tokens: int = 0
    total_cost: float = 0.0


@dataclass(slots=True)
class ProviderEnrichment:
    """Best-effort detail. The *_ok flags distinguish 'failed' from 'empty' —
    on failure the caller keeps its previous values instead of zeroing them.
    """

    active_block: BlockUsage | None = None
    blocks_ok: bool = False
    week_total: PeriodUsage | None = None
    month_total: PeriodUsage | None = None
    periods_ok: bool = False
