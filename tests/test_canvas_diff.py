"""canvas_diff 功能测试：生成、正向应用、反向应用、序列化。"""

import json
import os
import tempfile
import unittest
from collections import deque
from itertools import permutations

from canvas_diff import apply_diff, dump_diff, generate_diff, load_diff, revert_diff


def snap(ids, props=None):
    """构造快照；默认属性与组件 ID 绑定，跨版本稳定。"""
    props = props or {}
    return [(cid, props.get(cid, {"ref": cid})) for cid in ids]


def ids_of(snapshot):
    return [cid for cid, _ in snapshot]


def brute_force_min_moves(old_ids, new_ids):
    """BFS 独立求最少移动次数：一次移动 = 取出一个元素插入任意间隙。"""
    assert set(old_ids) == set(new_ids)
    start, goal = tuple(old_ids), tuple(new_ids)
    if start == goal:
        return 0
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        state, dist = queue.popleft()
        for i in range(len(state)):
            elem = state[i]
            rest = state[:i] + state[i + 1:]
            for j in range(len(state)):
                nxt = rest[:j] + (elem,) + rest[j:]
                if nxt == goal:
                    return dist + 1
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, dist + 1))
    raise AssertionError("unreachable")


class TestAcceptance(unittest.TestCase):
    def test_rotate_abcd_produces_single_move(self):
        old, new = snap("ABCD"), snap("BCDA")
        diff = generate_diff(old, new)
        self.assertEqual(len(diff["move"]), 1)
        self.assertEqual(diff["move"][0]["id"], "A")
        self.assertEqual(diff["del"], [])
        self.assertEqual(diff["add"], [])
        self.assertEqual(diff["upd"], [])
        self.assertEqual(apply_diff(old, diff), new)
        self.assertEqual(revert_diff(new, diff), old)

    def test_pure_insertion_reports_no_moves(self):
        old, new = snap("ABCD"), snap("AXBCYD")
        diff = generate_diff(old, new)
        self.assertEqual(diff["move"], [])
        self.assertEqual(sorted(op["id"] for op in diff["add"]), ["X", "Y"])
        self.assertEqual(apply_diff(old, diff), new)
        self.assertEqual(revert_diff(new, diff), old)

    def test_pure_deletion_reports_no_moves(self):
        old, new = snap("AXBCYD"), snap("ABCD")
        diff = generate_diff(old, new)
        self.assertEqual(diff["move"], [])
        self.assertEqual(sorted(op["id"] for op in diff["del"]), ["X", "Y"])
        self.assertEqual(apply_diff(old, diff), new)
        self.assertEqual(revert_diff(new, diff), old)

    def test_mixed_add_del_move_update(self):
        old = [
            ("keep", {"fill": "red", "n": 1}),
            ("gone", {"x": [1, 2]}),
            ("moveme", {"w": 10}),
            ("alsogone", {}),
            ("stay", {"k": {"nested": [True, None]}}),
        ]
        new = [
            ("fresh", {"a": 1}),
            ("stay", {"k": {"nested": [True, None]}}),
            ("moveme", {"w": 20}),
            ("keep", {"fill": "red", "n": 1}),
            ("another", [1, {"b": 2}]),
        ]
        diff = generate_diff(old, new)

        self.assertEqual([op["id"] for op in diff["del"]], ["gone", "alsogone"])
        self.assertEqual(sorted(op["id"] for op in diff["add"]), ["another", "fresh"])
        self.assertEqual([op["id"] for op in diff["upd"]], ["moveme"])
        self.assertEqual(diff["upd"][0]["old"], {"w": 10})
        self.assertEqual(diff["upd"][0]["new"], {"w": 20})
        self.assertEqual([op["id"] for op in diff["move"]], ["moveme", "keep"])

        self.assertEqual(apply_diff(old, diff), new)
        self.assertEqual(revert_diff(new, diff), old)

    def test_update_and_move_on_same_component(self):
        # ABC -> CAB：C 是唯一必须移动的组件，同时其属性被修改
        old = snap("ABC", {"C": {"v": 1}})
        new = snap("CAB", {"C": {"v": 2}})
        diff = generate_diff(old, new)
        self.assertEqual([op["id"] for op in diff["move"]], ["C"])
        self.assertEqual([op["id"] for op in diff["upd"]], ["C"])
        self.assertEqual(apply_diff(old, diff), new)
        self.assertEqual(revert_diff(new, diff), old)

    def test_unchanged_components_carry_no_props_copy(self):
        # 未改属性的组件默认带 {"ref": cid}，差异中不得出现任何 ref 属性副本
        old = snap("ABCDE", {"C": {"v": 1}})
        new = snap("AEBCD", {"C": {"v": 2}})
        diff = generate_diff(old, new)
        blob = json.dumps(diff, ensure_ascii=False)
        self.assertNotIn("ref", blob)
        self.assertEqual(diff["upd"], [{"id": "C", "old": {"v": 1}, "new": {"v": 2}}])
        for op in diff["move"]:
            self.assertNotIn("props", op)

    def test_common_ids_never_deleted_and_readded(self):
        old = snap("ABC")
        new = snap("CBA")
        diff = generate_diff(old, new)
        touched = {op["id"] for op in diff["del"]} & {op["id"] for op in diff["add"]}
        self.assertEqual(touched, set())
        self.assertEqual({op["id"] for op in diff["del"]} & set("ABC"), set())

    def test_key_order_does_not_affect_equality(self):
        old = [("A", {"x": 1, "y": 2})]
        new = [("A", {"y": 2, "x": 1})]
        diff = generate_diff(old, new)
        self.assertEqual(diff["upd"], [])
        self.assertEqual(diff["move"], [])


class TestMinimalMoves(unittest.TestCase):
    def test_move_count_matches_brute_force_optimum(self):
        import itertools

        base = ["A", "B", "C", "D", "E"]
        checked = 0
        for new_ids in itertools.permutations(base):
            old, new = snap(base), snap(list(new_ids))
            diff = generate_diff(old, new)
            optimum = brute_force_min_moves(base, list(new_ids))
            self.assertEqual(len(diff["move"]), optimum, f"ids={new_ids}")
            self.assertEqual(apply_diff(old, diff), new)
            self.assertEqual(revert_diff(new, diff), old)
            checked += 1
        self.assertEqual(checked, 120)

    def test_move_count_with_adds_and_dels(self):
        # 公共子序列上的最优移动数不受新增/删除影响
        old = snap(["A", "X", "B", "C", "Y", "D"])
        new = snap(["D", "Z", "C", "B", "A"])
        diff = generate_diff(old, new)
        common_optimum = brute_force_min_moves(["A", "B", "C", "D"], ["D", "C", "B", "A"])
        self.assertEqual(len(diff["move"]), common_optimum)
        self.assertEqual(apply_diff(old, diff), new)
        self.assertEqual(revert_diff(new, diff), old)


class TestSerializeRoundTrip(unittest.TestCase):
    def test_file_round_trip_restores_both_directions(self):
        old = [("A", {"w": 1}), ("B", {"h": 2}), ("C", {"深": "值"})]
        new = [("C", {"深": "值"}), ("A", {"w": 9}), ("D", {"z": [1, 2]})]
        diff = generate_diff(old, new)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "diff.json")
            dump_diff(diff, path)
            loaded = load_diff(path)
        self.assertEqual(apply_diff(old, loaded), new)
        self.assertEqual(revert_diff(new, loaded), old)

    def test_load_rejects_bad_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"v": 999}, f)
            with self.assertRaises(ValueError):
                load_diff(path)


if __name__ == "__main__":
    unittest.main()
