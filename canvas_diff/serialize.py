"""差异的本地 JSON 文件保存与读取。

差异本身即是纯 JSON 结构，序列化不附带任何快照或完整叠放序列；
重新读取后仅凭旧快照+差异可得到新快照，仅凭新快照+差异可恢复旧快照。
"""

import json

from .types import DIFF_VERSION, Diff

_REQUIRED_KEYS = ("del", "upd", "move", "add")


def dump_diff(diff: Diff, path: str) -> None:
    """把差异保存为本地 JSON 文件（UTF-8，紧凑分隔符）。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(diff, f, ensure_ascii=False, separators=(",", ":"))


def load_diff(path: str) -> Diff:
    """从本地 JSON 文件读取差异，并做基本结构校验。"""
    with open(path, "r", encoding="utf-8") as f:
        diff = json.load(f)
    if not isinstance(diff, dict) or diff.get("v") != DIFF_VERSION:
        raise ValueError("不支持的差异文件格式或版本")
    for key in _REQUIRED_KEYS:
        if not isinstance(diff.get(key), list):
            raise ValueError(f"差异文件缺少列表字段: {key}")
    return diff
