"""差异应用：正向应用得到新快照，反向应用恢复旧快照。

应用不是逐条模拟操作，而是按差异中记录的绝对位置一次性重建完整序列：
- 正向：move.to 与 add.at 指定了新序列中的位置，其余空位由未移动公共组件
  （保持旧版相对顺序）依次填充。
- 反向：del.at 指定了旧序列中的位置，其余空位为公共组件名次；移动组件占据
  各自的 move.from 名次，未移动公共组件（保持新版相对顺序）填充剩余名次。
"""

from typing import Dict, List, Tuple

from .types import Component, Diff, Snapshot


def apply_diff(old: Snapshot, diff: Diff) -> Snapshot:
    """正向应用：old + diff -> new。返回完整组件内容与完整叠放顺序。"""
    props: Dict[str, dict] = {cid: p for cid, p in old}
    for op in diff["del"]:
        del props[op["id"]]
    for op in diff["upd"]:
        props[op["id"]] = op["new"]
    for op in diff["add"]:
        props[op["id"]] = op["props"]

    moved_ids = {op["id"] for op in diff["move"]}
    stayers = [cid for cid, _ in old if cid in props and cid not in moved_ids]

    n = len(stayers) + len(diff["move"]) + len(diff["add"])
    slots: List[Component] = [None] * n  # type: ignore[list-item]
    for op in diff["move"]:
        slots[op["to"]] = (op["id"], props[op["id"]])
    for op in diff["add"]:
        slots[op["at"]] = (op["id"], op["props"])
    it = iter(stayers)
    for i in range(n):
        if slots[i] is None:
            cid = next(it)
            slots[i] = (cid, props[cid])
    return slots


def revert_diff(new: Snapshot, diff: Diff) -> Snapshot:
    """反向应用：new + diff -> old。返回完整组件内容与完整叠放顺序。"""
    props: Dict[str, dict] = {cid: p for cid, p in new}
    for op in diff["add"]:
        del props[op["id"]]
    for op in diff["upd"]:
        props[op["id"]] = op["old"]
    for op in diff["del"]:
        props[op["id"]] = op["props"]

    moved_ids = {op["id"] for op in diff["move"]}
    add_ids = {op["id"] for op in diff["add"]}
    stayers = [cid for cid, _ in new if cid not in moved_ids and cid not in add_ids]

    mover_by_from: Dict[int, str] = {op["from"]: op["id"] for op in diff["move"]}

    m = len(stayers) + len(diff["move"]) + len(diff["del"])
    slots: List[Tuple[str, dict]] = [None] * m  # type: ignore[list-item]
    for op in diff["del"]:
        slots[op["at"]] = (op["id"], op["props"])
    common_positions = [i for i in range(m) if slots[i] is None]
    it = iter(stayers)
    for rank, pos in enumerate(common_positions):
        cid = mover_by_from.get(rank)
        if cid is None:
            cid = next(it)
        slots[pos] = (cid, props[cid])
    return slots
