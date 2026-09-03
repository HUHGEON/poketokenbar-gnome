"""Qt front end.

Built for Windows, where there is no panel to extend and no Plasma widget to
install, but it is plain Qt and runs anywhere Qt does.

Two things make this the least risky of the three front ends. It is Python, so
it imports `poketokenbar.state` and `poketokenbar.commands` directly instead of
reimplementing the file protocol — there is no contract to get wrong. And Qt
runs offscreen, so every widget here is actually constructed and fed a real
payload by the test suite, rather than only being read.
"""
