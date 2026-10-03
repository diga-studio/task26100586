"""生成差异。

移动次数最少的依据：未移动的共有组件在两版中的相对顺序一致，
构成公共子序列；故最少移动数 = 共有组件数 - 最长公共子序列长度。
这里用 LIS（耐心排序）在 O(n log n) 内求出一条最长公共子序列，
其余共有组件各产生一次移动。
"""

import json
from bisect import bisect_left
from typing import Dict, List, Optional, Set

from .types import DIFF_VERSION, Diff, Snapshot


def _canon(props) -> str:
    """属性的规范化序列化：键序无关，数组顺序与值保真。"""
    return json.dumps(props, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _lis_kept_indices(seq: List[int]) -> Set[int]:
    """返回 seq 中属于某条最长递增子序列的下标集合。"""
    tails_val: List[int] = []
    tails_idx: List[int] = []
    prev = [-1] * len(seq)
    for i, x in enumerate(seq):
        j = bisect_left(tails_val, x)
        if j == len(tails_val):
            tails_val.append(x)
            tails_idx.append(i)
        else:
            tails_val[j] = x
            tails_idx[j] = i
        if j > 0:
            prev[i] = tails_idx[j - 1]
    kept: Set[int] = set()
    k = tails_idx[-1] if tails_idx else -1
    while k != -1:
        kept.add(k)
        k = prev[k]
    return kept


def _predecessors(ids: List[str], skip: Set[str]) -> Dict[str, Optional[str]]:
    """对 ids 中不属于 skip 的元素，给出其在过滤后序列中的直接前驱。"""
    result: Dict[str, Optional[str]] = {}
    prev: Optional[str] = None
    for cid in ids:
        if cid in skip:
            continue
        result[cid] = prev
        prev = cid
    return result


def generate_diff(old: Snapshot, new: Snapshot) -> Diff:
    """由旧、新两份快照生成差异，移动操作总数最少。"""
    old_ids = [c["id"] for c in old]
    new_ids = [c["id"] for c in new]
    old_props = {c["id"]: c["props"] for c in old}
    new_props = {c["id"]: c["props"] for c in new}

    old_set = set(old_ids)
    new_set = set(new_ids)
    added = new_set - old_set
    deleted = old_set - new_set

    # 共有组件中未移动者 = 一条最长公共子序列
    old_common = [cid for cid in old_ids if cid not in deleted]
    pos_in_new = {cid: i for i, cid in enumerate(new_ids) if cid not in added}
    kept_idx = _lis_kept_indices([pos_in_new[cid] for cid in old_common])
    kept = {old_common[i] for i in kept_idx}
    moved = [cid for cid in new_ids if cid not in added and cid not in kept]

    # 移动：前驱分别取“新版去掉新增”“旧版去掉删除”后的直接前驱
    new_pred = _predecessors(new_ids, added)
    old_pred = _predecessors(old_ids, deleted)
    mov = [{"i": cid, "a": new_pred[cid], "b": old_pred[cid]} for cid in moved]

    # 新增：按新版自底向上，锚点为新版完整序列中的直接前驱
    full_new_pred = _predecessors(new_ids, set())
    add = [
        {"i": cid, "p": new_props[cid], "a": full_new_pred[cid]}
        for cid in new_ids
        if cid in added
    ]

    # 删除：按旧版自底向上，锚点为旧版完整序列中的直接前驱，携带旧属性以支持还原
    full_old_pred = _predecessors(old_ids, set())
    dele = [
        {"i": cid, "p": old_props[cid], "b": full_old_pred[cid]}
        for cid in old_ids
        if cid in deleted
    ]

    # 属性替换：仅共有且属性规范化后不一致的组件，新旧属性都携带
    set_ops = []
    for cid in old_common:
        op, np_ = old_props[cid], new_props[cid]
        if op is not np_ and _canon(op) != _canon(np_):
            set_ops.append({"i": cid, "o": op, "n": np_})

    return {"v": DIFF_VERSION, "add": add, "del": dele, "set": set_ops, "mov": mov}
