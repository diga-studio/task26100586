"""画布版本差异库：生成差异、正向应用、反向应用、JSON 存取。"""

from .apply import apply_diff, revert_diff
from .diff import generate_diff
from .io import load_diff, save_diff
from .types import Component, Diff, Snapshot

__all__ = [
    "Component",
    "Diff",
    "Snapshot",
    "generate_diff",
    "apply_diff",
    "revert_diff",
    "save_diff",
    "load_diff",
]
