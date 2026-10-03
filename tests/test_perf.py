"""canvas_diff 规模与差异体积测试（验收口径，运行时会打印报告）。"""

import json
import time
import unittest

from canvas_diff import apply_diff, generate_diff, revert_diff

N_REVERSE = 200_000
N_SINGLE_MOVE = 100_000
TIME_LIMIT_S = 15.0
SIZE_LIMIT_BYTES = 2 * 1024


def make_snapshot(n):
    # ID 最长 16 字节；属性对象序列化后不超过 128 字节
    return [(f"c{i:06d}", {"x": i % 1000, "y": i % 997, "w": 100, "h": 50}) for i in range(n)]


class TestPerf(unittest.TestCase):
    def test_reversed_200k(self):
        old = make_snapshot(N_REVERSE)
        new = list(reversed(old))

        t0 = time.perf_counter()
        diff = generate_diff(old, new)
        t1 = time.perf_counter()
        result_new = apply_diff(old, diff)
        t2 = time.perf_counter()
        result_old = revert_diff(new, diff)
        t3 = time.perf_counter()

        self.assertEqual(result_new, new)
        self.assertEqual(result_old, old)
        total = t3 - t0
        diff_bytes = len(json.dumps(diff, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        print(
            f"\n[perf] 完全颠倒: 组件数={N_REVERSE}, 移动次数={len(diff['move'])}, "
            f"差异字节数={diff_bytes}, 生成={t1 - t0:.3f}s, 正向={t2 - t1:.3f}s, "
            f"反向={t3 - t2:.3f}s, 总耗时={total:.3f}s (上限 {TIME_LIMIT_S}s)"
        )
        self.assertLessEqual(total, TIME_LIMIT_S)

    def test_single_move_100k_diff_size(self):
        old = make_snapshot(N_SINGLE_MOVE)
        new = old[1:] + old[:1]  # 仅把最底层组件移到最顶层

        t0 = time.perf_counter()
        diff = generate_diff(old, new)
        result_new = apply_diff(old, diff)
        result_old = revert_diff(new, diff)
        total = time.perf_counter() - t0

        self.assertEqual(result_new, new)
        self.assertEqual(result_old, old)
        diff_bytes = len(json.dumps(diff, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        print(
            f"\n[perf] 单次移动: 组件数={N_SINGLE_MOVE}, 移动次数={len(diff['move'])}, "
            f"差异字节数={diff_bytes} (上限 {SIZE_LIMIT_BYTES}), 总耗时={total:.3f}s"
        )
        self.assertEqual(len(diff["move"]), 1)
        self.assertLessEqual(diff_bytes, SIZE_LIMIT_BYTES)


if __name__ == "__main__":
    unittest.main()
