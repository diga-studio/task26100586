"""画布版本差异库：公共类型定义。

快照（Snapshot）表示为从底到顶排列的组件列表，每个组件是 (id, props) 二元组：
- id: 全页唯一、跨版本稳定的字符串
- props: JSON 属性对象（dict，键次序不影响相等判断）

差异（Diff）是一个纯 JSON 可序列化的 dict，结构如下：
{
    "v": 1,
    "del":  [{"id": str, "at": int, "props": dict}, ...],
    "upd":  [{"id": str, "old": dict, "new": dict}, ...],
    "move": [{"id": str, "from": int, "to": int}, ...],
    "add":  [{"id": str, "at": int, "props": dict}, ...],
}

索引语义：
- del.at   : 被删组件在旧快照完整序列中的下标
- move.from: 移动组件在“旧序列去掉被删组件后”的公共序列中的名次
- move.to  : 移动组件在新快照完整序列中的下标
- add.at   : 新增组件在新快照完整序列中的下标
"""

from typing import Any, Dict, List, Tuple

Component = Tuple[str, Dict[str, Any]]
Snapshot = List[Component]
Diff = Dict[str, Any]

DIFF_VERSION = 1
