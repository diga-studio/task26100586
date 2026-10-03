"""正向 / 反向应用差异。

顺序重建分两步：
1. 未移动组件保持相对顺序，被移动组件以“直接前驱”锚点构成链，
   按链归并得到去掉新增（正向）/ 去掉删除（反向）后的序列，O(n)。
2. 新增（正向）/ 删除（反向）的组件按差异中自底向上的顺序，
   用链表头插/锚点后插，O(1) 每个，避免大列表下标插入的 O(n^2)。
"""

from typing import Dict, List, Optional

from .types import Diff, Snapshot


def _merge_order(kept_seq: List[str], succ: Dict[Optional[str], str]) -> List[str]:
    """把保持相对顺序的 kept 序列与被移动组件的前驱链归并成完整序列。"""
    result: List[str] = []
    ki = 0
    n = len(kept_seq)

    def next_kept() -> Optional[str]:
        nonlocal ki
        if ki < n:
            cid = kept_seq[ki]
            ki += 1
            return cid
        return None

    cur = succ.get(None)
    if cur is None:
        cur = next_kept()
    while cur is not None:
        result.append(cur)
        nxt = succ.get(cur)
        cur = nxt if nxt is not None else next_kept()
    return result


def _apply_inserts(order: List[str], ops: List[dict], anchor_key: str) -> List[str]:
    """在 order 基础上按 ops 顺序做“插入到锚点之后”（锚点为 None 时插到最底层）。"""
    nodes = list(order)
    idx = {cid: i for i, cid in enumerate(nodes)}
    n = len(nodes)
    nxt = list(range(1, n)) + [-1]
    prv = [-1] + list(range(n - 1))
    head = 0 if n else -1
    for op in ops:
        cid = op["i"]
        anchor = op[anchor_key]
        ci = len(nodes)
        nodes.append(cid)
        idx[cid] = ci
        nxt.append(-1)
        prv.append(-1)
        if anchor is None:
            if head == -1:
                head = ci
            else:
                nxt[ci] = head
                prv[head] = ci
                head = ci
        else:
            ai = idx[anchor]
            bi = nxt[ai]
            nxt[ai] = ci
            prv[ci] = ai
            nxt[ci] = bi
            if bi != -1:
                prv[bi] = ci
    result: List[str] = []
    cur = head
    while cur != -1:
        result.append(nodes[cur])
        cur = nxt[cur]
    return result


def _build_snapshot(order: List[str], props: Dict[str, dict]) -> Snapshot:
    return [{"id": cid, "props": props[cid]} for cid in order]


def apply_diff(old: Snapshot, diff: Diff) -> Snapshot:
    """旧快照 + 差异 -> 新快照（完整内容与完整叠放顺序）。"""
    props = {c["id"]: c["props"] for c in old}
    for op in diff["del"]:
        del props[op["i"]]
    for op in diff["set"]:
        props[op["i"]] = op["n"]
    for op in diff["add"]:
        props[op["i"]] = op["p"]

    moved = {op["i"] for op in diff["mov"]}
    deleted = {op["i"] for op in diff["del"]}
    kept_seq = [c["id"] for c in old if c["id"] not in deleted and c["id"] not in moved]
    succ = {op["a"]: op["i"] for op in diff["mov"]}
    order = _merge_order(kept_seq, succ)
    order = _apply_inserts(order, diff["add"], "a")
    return _build_snapshot(order, props)


def revert_diff(new: Snapshot, diff: Diff) -> Snapshot:
    """新快照 + 差异 -> 旧快照（完整内容与完整叠放顺序）。"""
    props = {c["id"]: c["props"] for c in new}
    for op in diff["add"]:
        del props[op["i"]]
    for op in diff["set"]:
        props[op["i"]] = op["o"]
    for op in diff["del"]:
        props[op["i"]] = op["p"]

    moved = {op["i"] for op in diff["mov"]}
    added = {op["i"] for op in diff["add"]}
    kept_seq = [c["id"] for c in new if c["id"] not in added and c["id"] not in moved]
    succ = {op["b"]: op["i"] for op in diff["mov"]}
    order = _merge_order(kept_seq, succ)
    order = _apply_inserts(order, diff["del"], "b")
    return _build_snapshot(order, props)
