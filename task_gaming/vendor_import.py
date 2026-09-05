"""Import the vendored thesis modules without executing the package __init__.

Why this exists. `vendor/Probing-Safety-Behaviours/safety_probes/__init__.py` eagerly imports
every submodule, including `viz`, which needs plotly, circuitsvis and IPython. `scripts/BOX_SETUP.md`
deliberately does not install those (this project's figures are matplotlib; the token trace in
Figure 2 is written here, not by viz). So a plain `import safety_probes` dies on `plotly`.

The three alternatives were worse: installing plotly is an install nobody needs, editing the
vendored `__init__` would be silently undone by `scripts/clone_vendor.sh`, and stubbing plotly in
sys.modules would leave a fake module lying around for anything else to trip over.

Instead: build the package module object from its spec and register it WITHOUT running its
`__init__`. Submodule imports then resolve normally through `__path__`, and their relative imports
(`from . import runtime`) work, because `sys.modules['safety_probes']` exists. `viz` is simply
never imported.

Usage:
    from task_gaming.vendor_import import load_safety_probes
    sp = load_safety_probes()
    sp.runtime, sp.chat, sp.extraction, sp.probes, sp.metrics, sp.datasets, sp.judge
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
import types
from pathlib import Path

VENDOR_PKG = Path(__file__).resolve().parents[1] / "vendor" / "Probing-Safety-Behaviours" / "safety_probes"

# Everything this project uses. `viz`, `steering`, `evaluation`, `export` and `summary` are out of
# scope per the study plan and §7 and are not loaded.
SUBMODULES = ("runtime", "chat", "extraction", "probes", "metrics", "datasets", "judge", "spec")


def load_safety_probes(submodules: tuple[str, ...] = SUBMODULES) -> types.ModuleType:
    """Return the `safety_probes` package with `submodules` imported and set as attributes."""
    if not VENDOR_PKG.is_dir():
        raise FileNotFoundError(
            f"{VENDOR_PKG} not found — run `bash scripts/clone_vendor.sh` first."
        )

    pkg = sys.modules.get("safety_probes")
    if pkg is None:
        spec = importlib.util.spec_from_file_location(
            "safety_probes",
            VENDOR_PKG / "__init__.py",
            submodule_search_locations=[str(VENDOR_PKG)],
        )
        pkg = importlib.util.module_from_spec(spec)
        sys.modules["safety_probes"] = pkg  # NB: spec.loader.exec_module(pkg) is deliberately skipped

    for name in submodules:
        setattr(pkg, name, importlib.import_module(f"safety_probes.{name}"))
    return pkg
