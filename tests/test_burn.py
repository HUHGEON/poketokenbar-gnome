from poketokenbar.burn import BurnTracker


class Clock:
    def __init__(self):
        self.now = 1_000_000.0

    def __call__(self):
        return self.now

    def advance_minutes(self, m):
        self.now += m * 60


def test_no_forecast_before_enough_samples():
    c = Clock()
    t = BurnTracker(c)
    t.record("session", 10.0)
    c.advance_minutes(5)
    t.record("session", 12.0)
    assert t.forecast("session") is None


def test_steady_burn_projects_an_eta():
    c = Clock()
    t = BurnTracker(c)
    # 1%/min for 10 minutes, ending at 20% -> 80 minutes to full.
    for pct in (10.0, 15.0, 20.0):
        t.record("session", pct)
        c.advance_minutes(5)
    f = t.forecast("session")
    assert f is not None
    assert abs(f.rate_per_minute - 1.0) < 0.01
    assert abs(f.minutes_to_full - 80) < 1


def test_eta_text_is_a_clock_time():
    c = Clock()
    t = BurnTracker(c)
    for pct in (10.0, 20.0, 30.0):
        t.record("session", pct)
        c.advance_minutes(5)
    assert ":" in t.forecast("session").eta_text


def test_flat_usage_yields_no_eta():
    c = Clock()
    t = BurnTracker(c)
    for _ in range(4):
        t.record("session", 40.0)
        c.advance_minutes(5)
    f = t.forecast("session")
    assert f is not None
    assert f.minutes_to_full is None


def test_window_reset_clears_history():
    # Utilization dropping means the window reset. Keeping the old samples
    # would fit a negative slope and suppress the forecast entirely.
    c = Clock()
    t = BurnTracker(c)
    for pct in (80.0, 90.0, 99.0):
        t.record("session", pct)
        c.advance_minutes(5)
    t.record("session", 2.0)  # reset
    assert t.forecast("session") is None

    for pct in (6.0, 10.0):
        c.advance_minutes(5)
        t.record("session", pct)
    f = t.forecast("session")
    assert f is not None
    assert f.rate_per_minute > 0


def test_old_samples_fall_out_of_the_window():
    c = Clock()
    t = BurnTracker(c)
    t.record("session", 10.0)
    c.advance_minutes(60)  # older than WINDOW_SECONDS
    for pct in (50.0, 51.0, 52.0):
        t.record("session", pct)
        c.advance_minutes(5)
    f = t.forecast("session")
    # Rate reflects the recent 0.2%/min, not the huge jump from the stale point.
    assert f.rate_per_minute < 0.5


def test_windows_are_tracked_separately():
    c = Clock()
    t = BurnTracker(c)
    for pct in (10.0, 20.0, 30.0):
        t.record("session", pct)
        t.record("weekly", 5.0)
        c.advance_minutes(5)
    assert t.forecast("session").minutes_to_full is not None
    assert t.forecast("weekly").minutes_to_full is None


def test_payload_only_includes_windows_with_data():
    c = Clock()
    t = BurnTracker(c)
    for pct in (10.0, 20.0, 30.0):
        t.record("session", pct)
        c.advance_minutes(5)
    payload = t.payload()
    assert "session" in payload
    assert "weekly" not in payload
