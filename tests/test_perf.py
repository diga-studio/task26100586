"""规模与差异体积测试：报告组件数量、移动次数、差异字节数和实际耗时。"""

import json
import time

from canvas_diff import apply_diff, generate_diff, revert_diff


def make_snap(ids, props=None):
    props = props or {}
    return [{"id": i, "props": props.get(i, {"t": "rect", "x": 1})} for i in ids]


def test_full_reverse_200k():
    n = 200_000
    ids = [f"c{i:07d}" for i in range(n)]  # ID 8 字节 <= 16 字节
    old = make_snap(ids)
    new = make_snap(list(reversed(ids)))  # 顺序完全颠倒，属性不变

    t0 = time.perf_counter()
    diff = generate_diff(old, new)
    t1 = time.perf_counter()
    out = apply_diff(old, diff)
    t2 = time.perf_counter()
    back = revert_diff(new, diff)
    t3 = time.perf_counter()

    assert [c["id"] for c in out] == [c["id"] for c in new]
    assert out == new
    assert back == old

    diff_bytes = len(json.dumps(diff, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    total = t3 - t0
    print(
        f"\n[perf] 组件数={n} 移动次数={len(diff['mov'])} "
        f"差异字节数={diff_bytes} "
        f"生成={t1 - t0:.2f}s 正向={t2 - t1:.2f}s 反向={t3 - t2:.2f}s 总耗时={total:.2f}s"
    )
    assert total <= 15, f"总耗时 {total:.2f}s 超过 15s"


def test_single_move_diff_size_100k():
    n = 100_000
    ids = [f"c{i:07d}" for i in range(n)]
    old = make_snap(ids)
    # 仅把最底层组件移到最顶层，无其他变化
    new_ids = ids[1:] + ids[:1]
    new = make_snap(new_ids)

    diff = generate_diff(old, new)
    assert len(diff["mov"]) == 1
    assert not diff["add"] and not diff["del"] and not diff["set"]
    assert apply_diff(old, diff) == new
    assert revert_diff(new, diff) == old

    diff_bytes = len(json.dumps(diff, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    print(f"\n[size] 组件数={n} 移动次数={len(diff['mov'])} 差异字节数={diff_bytes}")
    assert diff_bytes <= 2048, f"差异 {diff_bytes} 字节超过 2KiB"
