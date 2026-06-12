"""
notebook_runner.py — DEPRECATED.  No longer used.

All ML logic previously loaded from Untitled37.ipynb at runtime is now
implemented directly in ml_engine.py.  This file is kept to avoid breaking
any stale import that might reference it, but it does nothing.
"""


def load() -> None:
    raise RuntimeError(
        "notebook_runner.load() was called, but the notebook-runner system "
        "has been removed.  All ML logic now lives in app/services/ml_engine.py."
    )


def get(name: str):
    raise RuntimeError(
        f"notebook_runner.get('{name}') was called, but the notebook-runner "
        "system has been removed.  All ML logic now lives in app/services/ml_engine.py."
    )
