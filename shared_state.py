"""Jaettu tila bottin ja web-sovelluksen välillä (dev-portaalia varten)."""
import sys
import threading
from collections import deque
from datetime import datetime, timezone

CONSOLE_MAX_LINES = 500
_console_lines: deque[str] = deque(maxlen=CONSOLE_MAX_LINES)
_lock = threading.Lock()
_bot_instance = None
_start_time: datetime | None = None


def set_bot(bot):
    global _bot_instance, _start_time
    _bot_instance = bot
    _start_time = datetime.now(timezone.utc)


def get_bot():
    return _bot_instance


def get_uptime() -> float | None:
    if _start_time is None:
        return None
    return (datetime.now(timezone.utc) - _start_time).total_seconds()


class ConsoleCapture:
    """Ohjaa stdout/stderr konsolilokiin ja läpikulkuun."""

    def __init__(self, stream):
        self._stream = stream

    def write(self, data: str):
        if data.strip():
            with _lock:
                for line in data.rstrip().split("\n"):
                    if line.strip():
                        ts = datetime.now().strftime("%H:%M:%S")
                        _console_lines.append(f"[{ts}] {line}")
        self._stream.write(data)
        self._stream.flush()

    def flush(self):
        self._stream.flush()

    def __getattr__(self, name):
        return getattr(self._stream, name)


def capture_console():
    """Ohjaa stdout ja stderr konsolilokiin."""
    sys.stdout = ConsoleCapture(sys.__stdout__)
    sys.stderr = ConsoleCapture(sys.__stderr__)


def get_console_lines(limit: int = 200) -> list[str]:
    with _lock:
        return list(_console_lines)[-limit:]


def clear_console() -> None:
    with _lock:
        _console_lines.clear()

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
