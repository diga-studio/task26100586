"""差异的本地 JSON 文件读写。"""

import json

from .types import Diff


def save_diff(diff: Diff, path: str) -> None:
    """把差异保存为本地 JSON 文件（紧凑格式，UTF-8）。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(diff, f, ensure_ascii=False, separators=(",", ":"))


def load_diff(path: str) -> Diff:
    """从本地 JSON 文件读取差异。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
