"""Toolkit-neutral progress and cooperative cancellation contracts."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional, Protocol

from graver.errors import ApplicationError

__all__ = (
    "CancellationRequested",
    "CancellationToken",
    "ProgressEvent",
    "ProgressObserver",
)


class CancellationRequested(ApplicationError):
    """Report cooperative cancellation at a documented safe boundary.

    Attributes:
        operation: Stable operation name whose work was cancelled.
        stage: Safe stage at which cancellation was observed.
    """

    def __init__(self, operation: str, stage: str):
        self.operation = operation
        self.stage = stage
        super().__init__(
            f"{operation} was cancelled during {stage}",
            context={"operation": operation, "stage": stage},
        )

    code = "operation_cancelled"


class CancellationToken:
    """Provide thread-safe cooperative cancellation without an event loop.

    A client may call :meth:`cancel` from another thread. Application operations
    call :meth:`raise_if_cancelled` only at boundaries where stopping cannot violate
    persistence invariants. The token never interrupts a running transaction.
    """

    def __init__(self) -> None:
        self._event = threading.Event()

    @property
    def cancelled(self) -> bool:
        """Return whether cancellation has been requested."""
        return self._event.is_set()

    def cancel(self) -> None:
        """Request cancellation idempotently and safely from any thread."""
        self._event.set()

    def raise_if_cancelled(self, operation: str, stage: str) -> None:
        """Raise at a caller-selected safe boundary when cancellation is requested.

        Args:
            operation: Stable operation name exposed to application clients.
            stage: Safe operation stage at which the check occurs.

        Raises:
            CancellationRequested: If cancellation was previously requested.
        """
        if self.cancelled:
            raise CancellationRequested(operation, stage)


@dataclass(frozen=True)
class ProgressEvent:
    """Describe monotonic progress for one synchronous application operation.

    Attributes:
        operation: Stable operation name shared by application adapters.
        stage: Extensible, operation-specific stage name.
        completed: Completed logical units at this event.
        total: Expected logical units when known.
        message: Optional safe, presentation-neutral context.
    """

    operation: str
    stage: str
    completed: int
    total: Optional[int] = None
    message: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.operation or not self.stage:
            raise ValueError("Progress operation and stage are required")
        if self.completed < 0:
            raise ValueError("Progress completed count cannot be negative")
        if self.total is not None and self.total < self.completed:
            raise ValueError("Progress total cannot be less than completed count")


class ProgressObserver(Protocol):
    """Receive progress events synchronously in the operation's calling thread."""

    def __call__(self, event: ProgressEvent) -> None:
        """Observe one immutable progress event without changing domain state."""
