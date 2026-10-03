"""功能测试：生成、正向应用、反向应用、JSON 存取。"""

import json

from canvas_diff import apply_diff, generate_diff, load_diff, revert_diff, save_diff


def make_snap(ids, props=None):
    props = props or {}
    return [{"id": i, "props": props.get(i, {})} for i in ids]


def ids_of(snap):
    return [c["id"] for c in snap]


def lcs_len(a, b):
    """独立 O(n*m) DP 求最长公共子序列长度，作为最优移动数的对照。"""
    dp = [0] * (len(b) + 1)
    for x in a:
        prev = 0
        for j, y in enumerate(b, 1):
            cur = dp[j]
            dp[j] = prev + 1 if x == y else max(dp[j], dp[j - 1])
            prev = cur
    return dp[-1]


def check_roundtrip(old, new):
    diff = generate_diff(old, new)
    assert apply_diff(old, diff) == new
    assert revert_diff(new, diff) == old
    # 移动次数与独立求得的最优值一致
    old_common = [c["id"] for c in old if c["id"] in {x["id"] for x in new}]
    new_common = [c["id"] for c in new if c["id"] in {x["id"] for x in old}]
    expected = len(old_common) - lcs_len(old_common, new_common)
    assert len(diff["mov"]) == expected
    return diff


def test_bottom_to_top_single_move():
    old = make_snap(list("ABCD"))
    new = make_snap(list("BCDA"))
    diff = check_roundtrip(old, new)
    assert len(diff["mov"]) == 1
    assert diff["mov"][0]["i"] == "A"
    assert not diff["add"] and not diff["del"] and not diff["set"]


def test_pure_insert_no_moves():
    old = make_snap(list("ABC"))
    new = make_snap(list("AXBYC"))
    diff = check_roundtrip(old, new)
    assert len(diff["mov"]) == 0
    assert sorted(op["i"] for op in diff["add"]) == ["X", "Y"]


def test_pure_delete_no_moves():
    old = make_snap(list("AXBYC"))
    new = make_snap(list("ABC"))
    diff = check_roundtrip(old, new)
    assert len(diff["mov"]) == 0
    assert sorted(op["i"] for op in diff["del"]) == ["X", "Y"]


def test_mixed_add_del_move_props():
    props_old = {"A": {"x": 1}, "B": {"y": [1, 2]}, "C": {}, "D": {"z": "s"}}
    props_new = {
        "A": {"x": 2},          # 属性修改 + 移动
        "B": {"y": [1, 2]},     # 不变
        "D": {"z": "s"},        # 不变但移动
        "E": {"new": True},     # 新增
    }
    old = make_snap(list("ABCD"), props_old)
    new = make_snap(list("DBEA"), props_new)
    diff = check_roundtrip(old, new)

    # 新增/删除恰好一次；共有组件不得删后重增
    assert [op["i"] for op in diff["add"]] == ["E"]
    assert [op["i"] for op in diff["del"]] == ["C"]
    # 属性变化的恰好替换一次，未变化的不产生替换
    assert [op["i"] for op in diff["set"]] == ["A"]
    assert diff["set"][0]["o"] == {"x": 1}
    assert diff["set"][0]["n"] == {"x": 2}
    # 属性未变的组件，差异中不得携带其属性副本
    for op in diff["mov"]:
        assert "p" not in op and "o" not in op and "n" not in op
    # 移动数最优：共有 A,B,D 在新版完全逆序，LCS 长度 1 -> 2 次移动
    assert len(diff["mov"]) == 2


def test_prop_key_order_irrelevant_array_order_matters():
    old = make_snap(["A"], {"A": {"k1": 1, "k2": [1, 2]}})
    same = make_snap(["A"], {"A": {"k2": [1, 2], "k1": 1}})
    diff = generate_diff(old, same)
    assert not diff["set"] and not diff["mov"]

    changed = make_snap(["A"], {"A": {"k1": 1, "k2": [2, 1]}})
    diff = generate_diff(old, changed)
    assert len(diff["set"]) == 1
    assert apply_diff(old, diff) == changed
    assert revert_diff(changed, diff) == old


def test_json_roundtrip_restores_both_ways(tmp_path):
    props_old = {i: {"v": i} for i in "ABCDEF"}
    props_new = {"A": {"v": "A"}, "C": {"v": "C2"}, "D": {"v": "D"},
                 "F": {"v": "F"}, "G": {"v": "G"}}
    old = make_snap(list("ABCDEF"), props_old)
    new = make_snap(list("GACFD"), props_new)
    diff = generate_diff(old, new)

    path = str(tmp_path / "diff.json")
    save_diff(diff, path)
    loaded = load_diff(path)
    # 仅凭旧快照+差异得到新快照；仅凭新快照+差异恢复旧快照
    assert apply_diff(old, loaded) == new
    assert revert_diff(new, loaded) == old
    # 差异本身必须可 JSON 序列化
    json.dumps(diff)


def test_reverse_stress_small_orders():
    """小规模乱序：移动数等于 n - LCS，正反向均可还原。"""
    import itertools
    import random

    rng = random.Random(42)
    base = list("ABCDE")
    for _ in range(50):
        new_order = list(base)
        rng.shuffle(new_order)
        old = make_snap(base)
        new = make_snap(new_order)
        diff = check_roundtrip(old, new)
        assert len(diff["mov"]) == len(base) - lcs_len(base, new_order)


def test_identical_snapshots_empty_diff():
    snap = make_snap(list("ABC"), {"A": {"x": 1}})
    diff = generate_diff(snap, [dict(c) for c in snap])
    assert diff == {"v": 1, "add": [], "del": [], "set": [], "mov": []}
    assert apply_diff(snap, diff) == snap
