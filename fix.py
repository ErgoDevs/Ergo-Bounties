import enum
import threading
from typing import Union

class OpsState(enum.Enum):
    IDLE = 'idle'
    ACTIVE = 'active'
    COMPLETE = 'complete'

class BountyOps:
    def __init__(self, identifier: str = None):
        self._identifier = identifier or "DefaultOps"
        self._state = OpsState.ACTIVE
        self._lock = threading.Lock()

    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def status(self) -> str:
        with self._lock:
            return self._state.value

    @status.setter
    def status(self, value: Union[str, OpsState]):
        with self._lock:
            if isinstance(value, str):
                self._state = OpsState(value)
            else:
                self._state = value

    def set(self, value: Union[str, OpsState]):
        self.status = value

    def toggle(self):
        with self._lock:
            self._state = OpsState.ACTIVE if self._state == OpsState.IDLE else OpsState.IDLE

    def __str__(self) -> str:
        return f"{self._identifier}:{self._state.value}"

    def __repr__(self) -> str:
        return f"<BountyOps({self._identifier})>"

    def is_active(self) -> bool:
        with self._lock:
            return self._state == OpsState.ACTIVE

    def __bool__(self) -> bool:
        with self._lock:
            return self._state not in (OpsState.IDLE, OpsState.COMPLETE)

if __name__ == "__main__":
    ops = BountyOps("ErgoBounty-1")
    ops.status = "active"
    print(ops)
    print(ops.is_active())
    ops.toggle()
    print(ops)