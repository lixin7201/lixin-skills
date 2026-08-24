from __future__ import annotations

import json
from typing import Any


def selection_prompt(
    snapshot: dict[str, Any], profiles: tuple[dict[str, Any], ...], limit: int
) -> str:
    compact_items = [
        {
            "id": item["id"],
            "source_id": item["source_id"],
            "source_url": item["source_url"],
            "title": item["title"],
            "summary": item.get("summary"),
            "body_excerpt": str(item.get("body") or "")[:2500],
            "published_at": item.get("published_at"),
            "geo_scope": item.get("geo_scope"),
            "source_nature": item.get("source_nature"),
            "content_sha256": item["content_sha256"],
        }
        for item in snapshot.get("items", [])[:60]
    ]
    profile_view = [
        {
            "id": profile.get("id"),
            "name": profile.get("name"),
            "persona": profile.get("persona"),
            "topics": profile.get("topics", []),
        }
        for profile in profiles
    ]
    return f"""
使用 dayibin-topic-angle-engine，以 angle-only 模式完成大宜宾 APP 选题会。

任务：从下面真实热点快照中最多选择 {limit} 条可发新闻，分配给最匹配的内容 IP。质量不足时可以少选，严禁凑数、编造事实或选择正文不足的素材。

硬规则：
1. 只能返回输入中存在的 item_id 和 profile_id。
2. 时政、公共安全、医疗、人物指控若来源不足，直接不选。
3. 每条只锁定一个明确角度，不写正文。
4. 只输出一个 JSON 对象，不要 Markdown、解释或代码围栏。

JSON 合同：
{{"selected":[{{"item_id":"...","profile_id":"...","angle":"...","reason":"..."}}]}}

内容 IP：
{json.dumps(profile_view, ensure_ascii=False)}

热点快照：
{json.dumps(compact_items, ensure_ascii=False)}
""".strip()


def draft_prompt(
    source_item: dict[str, Any], selection: dict[str, Any], profile: dict[str, Any]
) -> str:
    material = {
        "id": source_item["id"],
        "title": source_item["title"],
        "summary": source_item.get("summary"),
        "body": source_item.get("body"),
        "source_url": source_item["source_url"],
        "published_at": source_item.get("published_at"),
        "source_id": source_item["source_id"],
        "content_sha256": source_item["content_sha256"],
    }
    profile_view = {
        "id": profile.get("id"),
        "name": profile.get("name"),
        "persona": profile.get("persona"),
        "voice": profile.get("voice"),
    }
    return f"""
调用 app-skill，为大宜宾 APP 写一篇可直接发布的帖子。app-skill 是唯一正文作者；先按它的规则只选择一位小编路线，不得混写。

锁定角度：{selection.get('angle')}
入选原因：{selection.get('reason')}
内容 IP：{json.dumps(profile_view, ensure_ascii=False)}
真实素材：{json.dumps(material, ensure_ascii=False)}

硬规则：
1. 只使用真实素材中的事实，不复制原文句段，不虚构采访、亲历、现场或用户故事。
2. 标题和正文中的每个数字必须来自素材。
3. fact_refs 的 evidence 必须逐字摘自真实素材，保持短句。
4. 正文用简单 HTML 段落；删除内部小编风格备注，不冒充真实小编署名。
5. 只输出一个 JSON 对象，不要 Markdown、解释或代码围栏。

JSON 合同：
{{"draft":{{"item_id":"{source_item['id']}","profile_id":"{profile.get('id')}","title":"...","html":"<p>...</p>","fact_refs":[{{"claim":"...","evidence":"素材原句"}}],"editor_route":"唯一小编名"}}}}
""".strip()
