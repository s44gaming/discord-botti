"""Jaettu tila bottin ja web-sovelluksen välillä (dev-portaalia varten)."""
import sys
import traceback
import threading
from collections import deque
from datetime import datetime, timezone

CONSOLE_MAX_LINES = 500
ERROR_LOG_MAX = 100
METRICS_SAMPLES = 60

_console_lines: deque[str] = deque(maxlen=CONSOLE_MAX_LINES)
_error_log: deque[dict] = deque(maxlen=ERROR_LOG_MAX)
_latency_samples: deque[dict] = deque(maxlen=METRICS_SAMPLES)
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


def add_error(exc: BaseException, context: str = "") -> None:
    """Tallentaa virheen virhelokiin (kehittäjäportaali)."""
    with _lock:
        tb = traceback.format_exc()
        _error_log.append({
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "msg": str(exc),
            "context": context,
            "traceback": tb,
        })


def get_recent_errors(limit: int = 50) -> list[dict]:
    with _lock:
        return list(_error_log)[-limit:]


def clear_errors() -> None:
    with _lock:
        _error_log.clear()


def push_latency_sample(latency_ms: float) -> None:
    """Tallentaa latenssin otoksen graafille."""
    with _lock:
        _latency_samples.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "ms": round(latency_ms, 1),
        })


def get_latency_history() -> list[dict]:
    with _lock:
        return list(_latency_samples)


def push_memory_sample(mb: float) -> None:
    """Varattu – käytetään jos tarvitaan muistihistoriaa."""
    pass

# Tekijänoikeudet S44Gaming kaikki oikeudet pidätetään. https://discord.gg/ujB4JHfgcg
