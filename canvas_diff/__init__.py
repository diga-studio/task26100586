"""canvas_diff：单页画布快照的版本差异库。"""

from .apply import apply_diff, revert_diff
from .diff import generate_diff
from .serialize import dump_diff, load_diff
from .types import DIFF_VERSION, Component, Diff, Snapshot

__all__ = [
    "Component",
    "DIFF_VERSION",
    "Diff",
    "Snapshot",
    "apply_diff",
    "dump_diff",
    "generate_diff",
    "load_diff",
    "revert_diff",
]
