"""差异生成：由旧、新两份快照生成最小移动次数的差异。

最小移动次数 = 公共组件数 - 公共组件在两版中相对顺序保持不变的最长子序列长度。
对“旧序列中公共组件在新公共序列中的名次”序列求 LIS，LIS 外的公共组件各移动一次。
"""

from bisect import bisect_left
from typing import List, Set

from .types import DIFF_VERSION, Diff, Snapshot


def _lis_member_indices(seq: List[int]) -> Set[int]:
    """返回 seq 中属于某个最长严格递增子序列的元素下标集合。O(n log n)。"""
    tail_vals: List[int] = []
    tail_idx: List[int] = []
    prev = [-1] * len(seq)
    for i, v in enumerate(seq):
        pos = bisect_left(tail_vals, v)
        if pos:
            prev[i] = tail_idx[pos - 1]
        if pos == len(tail_vals):
            tail_vals.append(v)
            tail_idx.append(i)
        else:
            tail_vals[pos] = v
            tail_idx[pos] = i
    members: Set[int] = set()
    if tail_idx:
        i = tail_idx[-1]
        while i != -1:
            members.add(i)
            i = prev[i]
    return members


def generate_diff(old: Snapshot, new: Snapshot) -> Diff:
    """生成从 old 到 new 的差异。移动次数在所有合法差异中最少。"""
    old_props = {cid: props for cid, props in old}
    new_props = {cid: props for cid, props in new}

    dels = [
        {"id": cid, "at": i, "props": old_props[cid]}
        for i, (cid, _) in enumerate(old)
        if cid not in new_props
    ]
    adds = [
        {"id": cid, "at": i, "props": new_props[cid]}
        for i, (cid, _) in enumerate(new)
        if cid not in old_props
    ]
    upds = [
        {"id": cid, "old": old_props[cid], "new": new_props[cid]}
        for cid, _ in old
        if cid in new_props and old_props[cid] != new_props[cid]
    ]

    old_common = [cid for cid, _ in old if cid in new_props]
    new_common_rank = {}
    rank = 0
    for cid, _ in new:
        if cid in old_props:
            new_common_rank[cid] = rank
            rank += 1
    new_full_index = {cid: i for i, (cid, _) in enumerate(new)}

    seq = [new_common_rank[cid] for cid in old_common]
    stayers = _lis_member_indices(seq)

    moves = [
        {"id": cid, "from": i, "to": new_full_index[cid]}
        for i, cid in enumerate(old_common)
        if i not in stayers
    ]
    moves.sort(key=lambda op: op["to"])

    return {"v": DIFF_VERSION, "del": dels, "upd": upds, "move": moves, "add": adds}
