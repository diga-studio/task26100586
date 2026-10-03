"""类型定义：快照、组件与差异结构。

快照（Snapshot）是一列从底到顶排列的组件，每个组件为：
    {"id": <str>, "props": <JSON 对象>}

差异（Diff）是一个可 JSON 序列化的 dict，结构为：
    {
        "v": 1,
        "add": [{"i": id, "p": props, "a": 前驱id 或 None}, ...],   # 按新版自底向上
        "del": [{"i": id, "p": props, "b": 前驱id 或 None}, ...],   # 按旧版自底向上
        "set": [{"i": id, "o": 旧props, "n": 新props}, ...],
        "mov": [{"i": id, "a": 新序列前驱 或 None, "b": 旧序列前驱 或 None}, ...],
    }
"""

from typing import Any, Dict, List, Union

# 一个组件：{"id": str, "props": dict}
Component = Dict[str, Any]
# 快照：自底向上的组件列表
Snapshot = List[Component]
# 差异：可直接 json.dumps 的字典
Diff = Dict[str, Any]

DIFF_VERSION = 1
