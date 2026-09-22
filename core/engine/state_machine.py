"""
core/engine/state_machine.py
─────────────────────────────
Event triage & trigger debouncer.

Maintains a simple FSM for Synapse's operational state:
  IDLE → CAPTURING → REASONING → READY → IDLE

Prevents duplicate triggers (debounce), manages state transitions,
and exposes the current state to the UI via WebSocket.
"""

import asyncio
from enum import Enum, auto
from datetime import datetime
from typing import Optional, Callable


class SynapseState(Enum):
    IDLE       = auto()   # Monitoring, no active inference
    CAPTURING  = auto()   # Context bundle being assembled
    REASONING  = auto()   # Nemotron is processing
    READY      = auto()   # Response ready, card visible
    SUPPRESSED = auto()   # User dismissed, brief cooldown


class StateMachine:
    """
    Lightweight FSM to track and broadcast Synapse's operational state.
    The UI uses this to drive the NeuronSphere animation (idle drift vs
    active green pulses vs rapid firing during reasoning).

    Valid transitions:
        IDLE → CAPTURING → REASONING → READY → IDLE
        Any → SUPPRESSED → IDLE (after cooldown)
    """

    SUPPRESSION_COOLDOWN_S = 60
    REASONING_TIMEOUT_S = 30  # Max time to wait for Nemotron before reset

    VALID_TRANSITIONS: dict[SynapseState, set[SynapseState]] = {
        SynapseState.IDLE:       {SynapseState.CAPTURING},
        SynapseState.CAPTURING:  {SynapseState.REASONING, SynapseState.IDLE},
        SynapseState.REASONING:  {SynapseState.READY, SynapseState.IDLE},
        SynapseState.READY:      {SynapseState.IDLE, SynapseState.SUPPRESSED},
        SynapseState.SUPPRESSED: {SynapseState.IDLE},
    }

    def __init__(self, on_state_change: Optional[Callable] = None):
        self._state = SynapseState.IDLE
        self._state_entered_at: datetime = datetime.utcnow()
        self._on_change = on_state_change
        self._timeout_task: Optional[asyncio.Task] = None

    @property
    def state(self) -> SynapseState:
        return self._state

    @property
    def state_name(self) -> str:
        return self._state.name

    async def transition(self, new_state: SynapseState) -> bool:
        """
        Attempt a state transition. Returns True if successful.
        Invalid transitions are silently ignored (logged in debug).
        """
        if new_state not in self.VALID_TRANSITIONS.get(self._state, set()):
            return False

        self._state = new_state
        self._state_entered_at = datetime.utcnow()

        # Cancel any pending timeout
        if self._timeout_task and not self._timeout_task.done():
            self._timeout_task.cancel()

        # Set watchdog timeouts for long-running states
        if new_state == SynapseState.REASONING:
            self._timeout_task = asyncio.create_task(
                self._reasoning_timeout()
            )
        elif new_state == SynapseState.SUPPRESSED:
            self._timeout_task = asyncio.create_task(
                self._suppression_cooldown()
            )

        if self._on_change:
            await self._on_change(new_state)
        return True

    async def _reasoning_timeout(self) -> None:
        await asyncio.sleep(self.REASONING_TIMEOUT_S)
        if self._state == SynapseState.REASONING:
            await self.transition(SynapseState.IDLE)

    async def _suppression_cooldown(self) -> None:
        await asyncio.sleep(self.SUPPRESSION_COOLDOWN_S)
        if self._state == SynapseState.SUPPRESSED:
            await self.transition(SynapseState.IDLE)

    def to_ui_payload(self) -> dict:
        """Serializable state for WebSocket broadcast to the Tauri UI."""
        elapsed = (datetime.utcnow() - self._state_entered_at).total_seconds()
        return {
            "state": self._state.name,
            "elapsed_s": round(elapsed, 1),
        }
