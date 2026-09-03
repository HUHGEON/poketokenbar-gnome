"""Desktop notifications, by whatever route this platform offers.

Cosmetic throughout: a failure is swallowed, never surfaced as an error, and
never allowed to interrupt a poll. That is also why the backends are tried in
order and a missing one is not a problem — the alternative is a tracker that
stops counting because it could not post a toast.

    Linux    notify-send (libnotify)
    macOS    osascript
    Windows  PowerShell, via the shell's own toast API

Windows has no equivalent of notify-send and no notification tool that ships
everywhere, so the toast is raised through PowerShell, which does. It is slower
than the other two — a process start of a few hundred milliseconds — but this
runs a handful of times a day, on hatches and limit crossings.
"""

from __future__ import annotations

import shutil
import subprocess
import sys

APP_NAME = "PokeTokenBar"
ICON = "utilities-system-monitor"

WINDOWS = "win32"
MACOS = "darwin"

# Long enough for a slow shell to start, short enough that a wedged one cannot
# hold up a poll. A notification is not worth waiting on.
TIMEOUT_SECONDS = 8


def _run(command: list[str]) -> bool:
    try:
        subprocess.run(
            command,
            check=False,
            timeout=TIMEOUT_SECONDS,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def _quote_applescript(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _quote_powershell(text: str) -> str:
    """Single-quoted PowerShell strings escape a quote by doubling it.

    XML-escaping comes on top of that, because the toast is defined as a
    document: a stray `&` in a Pokemon name would otherwise make the whole
    payload unparseable and the notification would silently not appear.
    """
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return escaped.replace("'", "''")


def available(system: str | None = None) -> bool:
    """Whether anything on this machine can post a notification."""
    system = system or sys.platform
    if system == WINDOWS:
        return shutil.which("powershell") is not None or shutil.which("pwsh") is not None
    if system == MACOS:
        return shutil.which("osascript") is not None
    return shutil.which("notify-send") is not None


def send(title: str, body: str = "", urgency: str = "normal",
         system: str | None = None) -> bool:
    """Post one notification. Returns whether it was dispatched."""
    system = system or sys.platform
    if system == WINDOWS:
        return _send_windows(title, body)
    if system == MACOS:
        return _send_macos(title, body)
    return _send_linux(title, body, urgency)


def _send_linux(title: str, body: str, urgency: str) -> bool:
    if shutil.which("notify-send") is None:
        return False
    return _run([
        "notify-send",
        "--app-name", APP_NAME,
        "--icon", ICON,
        "--urgency", urgency,
        title,
        body,
    ])


def _send_macos(title: str, body: str) -> bool:
    if shutil.which("osascript") is None:
        return False
    script = (
        f'display notification "{_quote_applescript(body)}"'
        f' with title "{_quote_applescript(title)}"'
    )
    return _run(["osascript", "-e", script])


def windows_script(title: str, body: str) -> str:
    """The PowerShell that raises one toast.

    Built as a string so it can be inspected by a test: nothing here can run
    PowerShell, and an unescaped quote in a Pokemon name is exactly the kind of
    thing that would only show up as a notification that never arrives.
    """
    return (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications,"
        " ContentType=WindowsRuntime] > $null;"
        "$xml = [Windows.UI.Notifications.ToastNotificationManager]::"
        "GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
        f"$xml.GetElementsByTagName('text')[0].AppendChild("
        f"$xml.CreateTextNode('{_quote_powershell(title)}')) > $null;"
        f"$xml.GetElementsByTagName('text')[1].AppendChild("
        f"$xml.CreateTextNode('{_quote_powershell(body)}')) > $null;"
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($xml);"
        "[Windows.UI.Notifications.ToastNotificationManager]::"
        f"CreateToastNotifier('{APP_NAME}').Show($toast);"
    )


def _send_windows(title: str, body: str) -> bool:
    shell = shutil.which("powershell") or shutil.which("pwsh")
    if shell is None:
        return False
    return _run([
        shell,
        "-NoProfile",
        # A machine-wide execution policy would otherwise refuse this, and the
        # refusal is silent from here.
        "-ExecutionPolicy", "Bypass",
        "-NonInteractive",
        "-Command", windows_script(title, body),
    ])


class Notifier:
    """Edge-triggered notifications for companion and limit events."""

    def __init__(self, send_fn=send) -> None:
        self._send = send_fn
        # kind -> highest tier already announced (1 = warn, 2 = crit).
        self._limit_tier: dict[str, int] = {}

    def companion(self, events, name: str | None = None,
                  banner: dict | None = None) -> None:
        """Announce a hatch, an evolution or a graduation.

        The wording comes from the celebration the store has already built, so
        the notification and the banner say the same thing in the same
        language. These used to be English sentences written here, which is
        how a Korean install got an English notification.
        """
        if events is None:
            return
        if banner and banner.get("title"):
            if (events.hatched is not None or events.evolved_to is not None
                    or events.graduated is not None or events.ditto_revealed):
                self._send(banner["title"], banner.get("detail", ""))
            return

        # No banner to borrow from — a caller that only has the events.
        label = name or "PokeTokenBar"
        if events.hatched is not None:
            self._send("An egg hatched!", f"{label} joined you.")
        if events.evolved_to is not None:
            self._send("Evolution!", f"{label} evolved.")
        if events.graduated is not None:
            self._send("Graduated!", f"{label} joined your Pokedex.")

    def limits(self, windows: dict[str, float], warn: float, crit: float) -> None:
        """Announce a window crossing warn or crit, once per crossing.

        Keyed by window kind alone. The Swift app re-notified on every refresh
        when volatile fields such as resets_at entered the key.
        """
        for kind, utilization in windows.items():
            tier = 2 if utilization >= crit else (1 if utilization >= warn else 0)
            previous = self._limit_tier.get(kind, 0)
            if tier == 0:
                self._limit_tier.pop(kind, None)  # rearm
                continue
            if tier <= previous:
                continue
            self._limit_tier[kind] = tier
            label = "5-hour" if kind == "session" else "weekly"
            self._send(
                f"{label.capitalize()} limit at {utilization:.0f}%",
                "Usage is close to the cap." if tier == 1 else "Usage is nearly exhausted.",
                urgency="critical" if tier == 2 else "normal",
            )
