"""
notebook_runner.py
==================
Loads Untitled37.ipynb and executes its function-definition section in a
clean Python namespace.  Everything from the first line up to (but not
including) the # MAIN EXECUTION block is exec'd once on first access.

After load(), every function defined in the notebook is available as an
attribute of this module:

    from app.services import notebook_runner as nb
    pipeline, scenario = nb.build_lasso_price_probability_model(...)
    prob = nb.predict_win_probability_for_price(...)

If a function is changed in Untitled37.ipynb the backend picks up the new
logic automatically on next server restart — no manual sync required.
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from typing import Any

# ── Notebook path: 4 directories up from this file ────────────────────────────
#   backend/app/services/notebook_runner.py
#   └── parent: services/
#   └── parent: app/
#   └── parent: backend/
#   └── parent: project root  → Untitled37.ipynb
_NOTEBOOK_PATH: Path = (
    Path(__file__).resolve()
    .parent   # services/
    .parent   # app/
    .parent   # backend/
    .parent   # project root (btpcode/)
    / "Untitled37.ipynb"
)

# ── Namespace that holds every object exec'd from the notebook ─────────────────
_NS: dict[str, Any] = {}
_loaded: bool = False


# ── Module-level helpers ───────────────────────────────────────────────────────

def _mock_non_backend_modules() -> None:
    """
    Inject minimal stubs for modules the notebook imports but the backend
    never uses (matplotlib for plotting, IPython.display for notebook output).

    These stubs prevent ImportError during exec() while having zero effect
    on any ML computation.
    """
    if "matplotlib" not in sys.modules:
        _mpl = types.ModuleType("matplotlib")
        _mpl_pyplot = types.ModuleType("matplotlib.pyplot")
        # Stub every plt.* call as a no-op that returns None or a trivial object
        class _PlotStub:
            def __call__(self, *a, **k):
                return _PlotStub()
            def __getattr__(self, _):
                return _PlotStub()
            def __iter__(self):          # support fig, ax = plt.subplots()
                yield _PlotStub()
                yield _PlotStub()
            def __enter__(self): return self
            def __exit__(self, *_): pass
        _stub = _PlotStub()
        for _attr in dir(_mpl_pyplot):
            try:
                setattr(_mpl_pyplot, _attr, _stub)
            except (AttributeError, TypeError):
                pass
        _mpl_pyplot.subplots  = lambda *a, **k: (_PlotStub(), _PlotStub())
        _mpl_pyplot.close     = lambda *a, **k: None
        _mpl_pyplot.show      = lambda *a, **k: None
        _mpl.pyplot  = _mpl_pyplot
        _mpl.use     = lambda *a, **k: None
        _mpl.rcParams = {}
        sys.modules["matplotlib"]         = _mpl
        sys.modules["matplotlib.pyplot"]  = _mpl_pyplot

    if "IPython" not in sys.modules:
        _ipy = types.ModuleType("IPython")
        _ipy_display = types.ModuleType("IPython.display")
        _ipy_display.display = lambda *a, **k: None
        _ipy.display = _ipy_display
        sys.modules["IPython"]         = _ipy
        sys.modules["IPython.display"] = _ipy_display


def load() -> None:
    """
    Execute the notebook's function-definition section once; no-op thereafter.

    Raises
    ------
    FileNotFoundError
        If Untitled37.ipynb is not in the project root.
    RuntimeError
        If the MAIN EXECUTION marker cannot be found in cell 0.
    """
    global _loaded
    if _loaded:
        return

    if not _NOTEBOOK_PATH.exists():
        raise FileNotFoundError(
            f"Notebook not found: {_NOTEBOOK_PATH}\n"
            "Untitled37.ipynb must be in the project root "
            "(the folder that contains backend/)."
        )

    with open(_NOTEBOOK_PATH, encoding="utf-8") as fh:
        nb = json.load(fh)

    src: str = "".join(nb["cells"][0]["source"])

    # Cut at the start of the MAIN EXECUTION banner so we exec only
    # the function / constant / import definitions, never the main block.
    #
    # The notebook contains:
    #   # ==============================
    #   # MAIN EXECUTION
    #   # ==============================
    #   data = load_dataset(...)     ← must NOT run from backend
    #
    marker = "# ==============================\n# MAIN EXECUTION"
    cut_idx = src.find(marker)
    if cut_idx == -1:
        # Fallback: find the first bare load_dataset() call
        cut_idx = src.find("\ndata = load_dataset(")
    if cut_idx == -1:
        raise RuntimeError(
            "Could not locate '# MAIN EXECUTION' in Untitled37.ipynb cell 0. "
            "The notebook structure may have changed."
        )

    definitions_src: str = src[:cut_idx]

    # Stub missing modules before exec so the notebook's imports don't fail
    _mock_non_backend_modules()

    # Execute in a clean namespace (builtins available)
    exec(compile(definitions_src, str(_NOTEBOOK_PATH), "exec"), _NS)

    _loaded = True
    n_fns = sum(1 for v in _NS.values() if callable(v) and not isinstance(v, type))
    print(
        f"[notebook_runner] {_NOTEBOOK_PATH.name} loaded — "
        f"{n_fns} callables in namespace.",
        file=sys.stderr,
    )


def get(name: str) -> Any:
    """
    Return a notebook-defined object by name, loading the notebook on
    first call.

    Raises AttributeError if the name is not in the notebook namespace.
    """
    load()
    if name in _NS:
        return _NS[name]
    available = sorted(k for k in _NS if not k.startswith("_") and callable(_NS[k]))
    raise AttributeError(
        f"notebook_runner: '{name}' not found in notebook namespace.\n"
        f"Available callables: {available}"
    )


# ── Module __getattr__ allows:  notebook_runner.evaluate_feature_additions(...) ─
def __getattr__(name: str) -> Any:
    if name.startswith("_"):
        raise AttributeError(name)
    return get(name)
