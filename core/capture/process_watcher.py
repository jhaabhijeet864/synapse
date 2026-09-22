"""
core/capture/process_watcher.py
───────────────────────────────
Active HWND & focus time tracker using win32gui + psutil.

Tracks:
  - Which application is currently in focus
  - How long the user has been focused on it (focus duration)
  - App switch frequency per hour (behavioral signal)
  - Detects "stuck" patterns: rapid switching = needs help

Architecture role: SLOW LANE — updates every 10s, enriches Context Bundle.
"""

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import psutil
import win32gui
import win32process


@dataclass
class FocusEvent:
    app_name: str
    window_title: str
    pid: int
    focused_at: datetime
    unfocused_at: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        end = self.unfocused_at or datetime.utcnow()
        return (end - self.focused_at).total_seconds()

    @property
    def duration_minutes(self) -> float:
        return self.duration_seconds / 60


@dataclass
class FocusState:
    """Snapshot of current focus behavior at a point in time."""
    active_app: str
    window_title: str
    focus_duration_mins: float
    switch_frequency_per_hour: float
    is_deep_work: bool           # True if long focus, low switches
    is_stuck: bool               # True if rapid switching pattern detected
    recent_apps: list[str]       # Last 5 apps in order


class ProcessWatcher:
    """
    Monitors application focus using Win32 hooks. Maintains a rolling
    window of focus events to compute behavioral metrics.

    Key signals emitted:
      - Deep work: focus > 20min, < 4 switches/hour
      - Stuck: > 6 switches in 5 minutes
      - App return: same app refocused after > 30min away
    """

    DEEP_WORK_THRESHOLD_MINS = 20
    STUCK_SWITCH_COUNT = 6
    STUCK_WINDOW_MINS = 5
    HISTORY_WINDOW_HOURS = 1
    POLL_INTERVAL_S = 10

    def __init__(self, on_focus_change=None):
        self.on_focus_change = on_focus_change
        self._current: Optional[FocusEvent] = None
        self._history: deque[FocusEvent] = deque(maxlen=100)
        self._switch_timestamps: deque[datetime] = deque(maxlen=50)
        self._app_focus_totals: defaultdict[str, float] = defaultdict(float)
        self._running = False

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────

    async def start(self) -> None:
        self._running = True
        while self._running:
            await self._poll()
            await asyncio.sleep(self.POLL_INTERVAL_S)

    def stop(self) -> None:
        self._running = False

    def get_state(self) -> FocusState:
        """Returns the current computed focus state."""
        active_app = self._current.app_name if self._current else "unknown"
        window_title = self._current.window_title if self._current else ""
        focus_duration = self._current.duration_minutes if self._current else 0

        switch_freq = self._compute_switch_frequency()
        is_deep = focus_duration >= self.DEEP_WORK_THRESHOLD_MINS and switch_freq < 4
        is_stuck = self._is_stuck_pattern()
        recent = self._recent_apps(n=5)

        return FocusState(
            active_app=active_app,
            window_title=window_title,
            focus_duration_mins=round(focus_duration, 1),
            switch_frequency_per_hour=round(switch_freq, 1),
            is_deep_work=is_deep,
            is_stuck=is_stuck,
            recent_apps=recent,
        )

    # ──────────────────────────────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────────────────────────────

    async def _poll(self) -> None:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return

        window_title = win32gui.GetWindowText(hwnd)
        _, pid = win32gui.GetWindowThreadProcessId(hwnd)
        app_name = self._get_app_name(pid)

        # Detect app switch
        if self._current is None or self._current.app_name != app_name:
            # Close out previous
            if self._current:
                self._current.unfocused_at = datetime.utcnow()
                self._app_focus_totals[self._current.app_name] += self._current.duration_seconds
                self._history.append(self._current)

            # Open new event
            self._current = FocusEvent(
                app_name=app_name,
                window_title=window_title,
                pid=pid,
                focused_at=datetime.utcnow(),
            )
            self._switch_timestamps.append(datetime.utcnow())

            if self.on_focus_change:
                await self.on_focus_change(self._current, self.get_state())
        else:
            # Update window title in case it changed (e.g., different file in VS Code)
            self._current.window_title = window_title

    def _compute_switch_frequency(self) -> float:
        """Switches per hour over the last HISTORY_WINDOW_HOURS."""
        cutoff = datetime.utcnow() - timedelta(hours=self.HISTORY_WINDOW_HOURS)
        recent_switches = sum(1 for t in self._switch_timestamps if t >= cutoff)
        return recent_switches / self.HISTORY_WINDOW_HOURS

    def _is_stuck_pattern(self) -> bool:
        """True if >= STUCK_SWITCH_COUNT switches in the last STUCK_WINDOW_MINS minutes."""
        cutoff = datetime.utcnow() - timedelta(minutes=self.STUCK_WINDOW_MINS)
        recent = sum(1 for t in self._switch_timestamps if t >= cutoff)
        return recent >= self.STUCK_SWITCH_COUNT

    def _recent_apps(self, n: int = 5) -> list[str]:
        apps = [e.app_name for e in list(self._history)[-n:]]
        if self._current:
            apps.append(self._current.app_name)
        return list(dict.fromkeys(apps))[-n:]  # deduplicate preserving order

    @staticmethod
    def _get_app_name(pid: int) -> str:
        try:
            return psutil.Process(pid).name().replace(".exe", "")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "unknown"
