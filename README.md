# canvas-diff

画布单页版本差异库（纯 Python，无第三方依赖，快照在内存中处理，差异可保存为本地 JSON 文件）。

## 能力

- `generate_diff(old, new)`：由旧、新两份快照生成差异，移动操作总数最少。
- `apply_diff(old, diff)`：旧快照 + 差异 -> 新快照（完整组件内容 + 完整叠放顺序）。
- `revert_diff(new, diff)`：新快照 + 差异 -> 旧快照（还原）。
- `save_diff(diff, path)` / `load_diff(path)`：差异的本地 JSON 存取；重新读取后仅凭快照与差异即可双向还原，不依赖生成时的其他状态。

## 数据约定

- 快照是一列**从底到顶**排列的组件：`[{"id": "a", "props": {...}}, ...]`。
- 组件 ID 全页唯一、跨版本稳定；`props` 为 JSON 对象，键次序不影响相等判断，数组顺序与值保真。
- 差异只表达四种操作：新增 `add`、删除 `del`、属性替换 `set`、移动 `mov`；
  移动以“直接前驱”为锚点（`null` 表示最底层），新增/删除造成的自然位移不算移动。
- 属性未变的组件，差异中不携带其属性副本；删除/替换操作携带旧属性以支持还原。

## 使用示例

```python
from canvas_diff import generate_diff, apply_diff, revert_diff, save_diff, load_diff

old = [{"id": c, "props": {}} for c in "ABCD"]
new = [{"id": c, "props": {}} for c in "BCDA"]

diff = generate_diff(old, new)   # 仅 1 次移动：A 从最底层移到最顶层
save_diff(diff, "diff.json")

diff = load_diff("diff.json")
assert apply_diff(old, diff) == new   # 正向
assert revert_diff(new, diff) == old  # 反向
```

## 运行测试

```bash
python3 -m pytest tests/ -q -s
```

- `tests/test_diff.py`：功能测试（新增/删除/移层/属性修改交织、JSON 存取、
  小规模移动次数与独立 DP 求得的最优值一致）。
- `tests/test_perf.py`：规模与体积测试，输出组件数量、移动次数、差异字节数与实际耗时。

本机实测（Python 3.14）：

| 场景 | 组件数 | 移动次数 | 差异字节数 | 总耗时 |
| --- | --- | --- | --- | --- |
| 顺序完全颠倒、属性不变 | 200,000 | 199,999 | 9,399,989 | ≈1.3s（生成 0.87s + 正向 0.24s + 反向 0.19s） |
| 仅移动一个组件 | 100,000 | 1 | 83 | <0.1s |

## 实现要点

- 最少移动数 = 共有组件数 − 最长公共子序列长度；用 LIS（耐心排序）O(n log n) 求出一条 LCS，
  其余共有组件各产生一次移动，不把整段搬移算作一次移动。
- 应用差异时用“前驱链归并 + 链表插入”重建完整顺序，整体 O(n)，
  避免大列表按下标插入的 O(n²)。
