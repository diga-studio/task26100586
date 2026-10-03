# canvas_diff

单页画布快照的版本差异库（纯 Python，无第三方依赖，无接口层）。
快照在内存中处理，差异可保存为本地 JSON 文件。

## 数据模型

- 快照：从底到顶排列的组件列表，每个组件是 `(id, props)` 二元组。
  `id` 为全页唯一、跨版本稳定的字符串；`props` 为 JSON 属性对象。
- 差异：纯 JSON dict，只包含四类操作：
  - `del`：删除（携带旧属性与旧位置，供反向恢复）
  - `upd`：属性整体替换（携带旧、新两份属性）
  - `move`：移动（`from` 为旧公共序列名次，`to` 为新序列下标）
  - `add`：新增（携带属性与插入位置）
- 未改属性的组件，差异中不携带其属性副本。

## 用法

```python
from canvas_diff import generate_diff, apply_diff, revert_diff, dump_diff, load_diff

old = [("A", {"w": 1}), ("B", {"h": 2}), ("C", {})]
new = [("C", {}), ("A", {"w": 9}), ("D", {"z": [1, 2]})]

diff = generate_diff(old, new)          # 生成差异（移动次数最少）
assert apply_diff(old, diff) == new     # 正向应用：旧快照 + 差异 -> 新快照
assert revert_diff(new, diff) == old    # 反向应用：新快照 + 差异 -> 旧快照

dump_diff(diff, "change.json")          # 保存为本地 JSON 文件
diff2 = load_diff("change.json")        # 重新读取后仍可双向应用
```

## 最小移动次数

移动次数 = 公共组件数 − 两版中相对顺序保持不变的最长公共子序列长度
（对公共组件的新版名次序列求 LIS，O(n log n)）。
新增/删除造成的自然位移不计为移动；小规模案例由 BFS 独立验证最优值。

## 运行测试

```bash
python3 -m unittest discover -s tests -v
```

功能测试覆盖：新增、删除、移层、属性修改交织；正反向完整还原；
移动次数与 BFS 独立最优值一致；未变组件不携带属性副本；序列化往返。

规模测试（随测试套件自动运行并打印报告）：

- 20 万组件完全颠倒：生成 + 正向 + 反向总耗时远低于 15 秒上限。
- 10 万组件仅移动一个组件：差异 JSON 约 80 字节，远低于 2KiB 上限。
