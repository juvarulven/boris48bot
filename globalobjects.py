from typing import Any


class GlobalObject:
    def __init__(self, value: Any):
        self._value = value

    def __call__(self, value: Any = None) -> Any:
        if value is None:
            return self._value
        else:
            self._value = value


RUNNING_FLAG = GlobalObject(True)

__all__ = ['RUNNING_FLAG']
