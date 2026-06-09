import random
import time
import logging
from enum import Enum
from typing import Any, Coroutine

logger = logging.getLogger(__name__)


class CBState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    """
    Simple circuit breaker with jitter on the reset timeout.

    States:
      CLOSED    — normal, failures counted
      OPEN      — fast-fail; after reset_timeout + jitter seconds → HALF_OPEN
      HALF_OPEN — one probe request; success → CLOSED, failure → OPEN again
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: float = 30.0,
        jitter_max: float = 10.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.jitter_max = jitter_max
        self._state = CBState.CLOSED
        self._failure_count = 0
        self._reset_deadline: float | None = None

    @property
    def state(self) -> CBState:
        if self._state == CBState.OPEN and time.monotonic() >= self._reset_deadline:
            self._state = CBState.HALF_OPEN
            logger.info("Circuit '%s' → HALF_OPEN", self.name)
        return self._state

    @property
    def is_open(self) -> bool:
        return self.state == CBState.OPEN

    def _on_success(self) -> None:
        if self._state != CBState.CLOSED:
            logger.info("Circuit '%s' → CLOSED", self.name)
        self._state = CBState.CLOSED
        self._failure_count = 0

    def _on_failure(self) -> None:
        self._failure_count += 1
        if self._state == CBState.HALF_OPEN or self._failure_count >= self.failure_threshold:
            jitter = random.uniform(0, self.jitter_max)
            deadline = self.reset_timeout + jitter
            self._reset_deadline = time.monotonic() + deadline
            self._state = CBState.OPEN
            logger.warning(
                "Circuit '%s' → OPEN (failures=%d, retry in %.1fs)",
                self.name,
                self._failure_count,
                deadline,
            )

    async def call(self, coro: Coroutine) -> Any:
        """Await *coro* through the circuit breaker. Raises CircuitOpenError if OPEN."""
        if self.state == CBState.OPEN:
            raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")
        try:
            result = await coro
            # Treat HTTP 5xx responses as failures too
            if hasattr(result, "status_code") and result.status_code >= 500:
                self._on_failure()
            else:
                self._on_success()
            return result
        except CircuitOpenError:
            raise
        except Exception:
            self._on_failure()
            raise
