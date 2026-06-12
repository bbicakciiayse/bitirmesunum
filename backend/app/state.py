"""
Global in-memory workspace state.
One active session at a time — appropriate for academic / demo use.
"""
from typing import Any

_workspace: dict[str, Any] = {}


def get() -> dict:
    return _workspace


def update(**kwargs: Any) -> None:
    _workspace.update(kwargs)


def clear() -> None:
    _workspace.clear()


def ready(key: str) -> bool:
    return _workspace.get(key) is not None
