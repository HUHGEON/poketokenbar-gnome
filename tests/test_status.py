import urllib.error

from poketokenbar.status import StatusChecker


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, s):
        self.now += s


def _payload(indicator):
    return {"status": {"indicator": indicator, "description": "x"}}


def test_healthy_providers_are_omitted():
    # A row saying "Operational" is noise; only problems earn space.
    checker = StatusChecker(fetch=lambda url: _payload("none"), clock=Clock())
    assert checker.get() == {}


def test_major_outage_is_reported():
    checker = StatusChecker(fetch=lambda url: _payload("major"), clock=Clock())
    result = checker.get()
    assert result["claude"]["severity"] == "crit"
    assert result["claude"]["label"] == "Major outage"


def test_minor_issue_is_a_warning():
    checker = StatusChecker(fetch=lambda url: _payload("minor"), clock=Clock())
    assert checker.get()["claude"]["severity"] == "warn"


def test_unknown_indicator_is_not_an_outage():
    checker = StatusChecker(fetch=lambda url: _payload("wat"), clock=Clock())
    assert checker.get()["claude"]["severity"] == "unknown"


def test_unreachable_status_page_is_omitted_not_an_outage():
    def boom(url):
        raise urllib.error.URLError("offline")

    assert StatusChecker(fetch=boom, clock=Clock()).get() == {}


def test_result_is_cached_within_the_ttl():
    calls = []

    def fetch(url):
        calls.append(url)
        return _payload("major")

    clock = Clock()
    checker = StatusChecker(fetch=fetch, clock=clock)
    checker.get()
    first = len(calls)
    clock.advance(60)
    checker.get()
    assert len(calls) == first


def test_cache_expires_after_the_ttl():
    calls = []

    def fetch(url):
        calls.append(url)
        return _payload("major")

    clock = Clock()
    checker = StatusChecker(fetch=fetch, clock=clock)
    checker.get()
    first = len(calls)
    clock.advance(601)
    checker.get()
    assert len(calls) > first
