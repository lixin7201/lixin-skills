import unittest

from dayibin_auto_publisher.safety import validate_draft


SOURCE_ITEM = {
    "id": "item-1",
    "title": "宜宾新增3条公交线路",
    "summary": "8月18日起，宜宾新增3条公交线路。",
    "body": "宜宾公交发布消息：8月18日起，新增3条公交线路，方便市民出行。",
    "source_url": "https://example.com/news/1",
    "content_sha256": "a" * 64,
}


class SafetyTests(unittest.TestCase):
    def test_validate_draft_accepts_referenced_facts_and_existing_numbers(self) -> None:
        draft = {
            "item_id": "item-1",
            "profile_id": "city",
            "title": "宜宾新增3条公交线，出门方便了",
            "html": "<p>8月18日起，宜宾新增3条公交线路。</p><p>你最期待哪一条？</p>",
            "fact_refs": [
                {
                    "claim": "宜宾新增3条公交线路",
                    "evidence": "8月18日起，新增3条公交线路",
                }
            ],
            "editor_route": "练团长",
        }

        self.assertEqual(validate_draft(draft, SOURCE_ITEM), [])

    def test_validate_draft_rejects_new_number(self) -> None:
        draft = {
            "item_id": "item-1",
            "profile_id": "city",
            "title": "宜宾新增5条公交线，出门方便了",
            "html": "<p>宜宾新增5条公交线路。</p>",
            "fact_refs": [
                {
                    "claim": "宜宾新增公交线路",
                    "evidence": "新增3条公交线路",
                }
            ],
            "editor_route": "练团长",
        }

        reasons = validate_draft(draft, SOURCE_ITEM)

        self.assertIn("unsupported_number:5条", reasons)

    def test_validate_draft_rejects_missing_evidence_and_fake_identity(self) -> None:
        draft = {
            "item_id": "item-1",
            "profile_id": "city",
            "title": "宜宾公交变化值得大家关注",
            "html": "<p>我亲眼看到现场非常热闹。</p>",
            "fact_refs": [{"claim": "现场很热闹", "evidence": "现场非常热闹"}],
            "editor_route": "练团长",
        }

        reasons = validate_draft(draft, SOURCE_ITEM)

        self.assertIn("evidence_not_in_source:0", reasons)
        self.assertIn("forbidden_identity_claim:我亲眼看到", reasons)

    def test_validate_draft_rejects_secondary_source_marker(self) -> None:
        draft = {
            "item_id": "item-1",
            "profile_id": "city",
            "title": "宜宾新增3条公交线",
            "html": "<p>宜宾融媒报道，8月18日起新增3条公交线路。</p>",
            "fact_refs": [{"claim": "新增3条公交线路", "evidence": "新增3条公交线路"}],
            "editor_route": "练团长",
        }

        self.assertIn(
            "ai_writing_pattern:secondary_source_marker",
            validate_draft(draft, SOURCE_ITEM),
        )

    def test_validate_draft_rejects_public_information_displayed_phrase(self) -> None:
        draft = {
            "item_id": "item-1", "profile_id": "city", "title": "宜宾公交变化",
            "html": "<p>公开信息显示，宜宾新增3条公交线路。</p>",
            "fact_refs": [{"claim": "新增3条公交线路", "evidence": "新增3条公交线路"}],
            "editor_route": "练团长",
        }

        self.assertIn(
            "ai_writing_pattern:secondary_source_marker",
            validate_draft(draft, SOURCE_ITEM),
        )

    def test_validate_draft_rejects_material_boundary_exposure(self) -> None:
        for phrase in (
            "公开材料给出的信息不多",
            "南溪视频新闻题名中的秋粮归仓",
            "这条消息目前能支撑的边界",
            "现有文字信息不多",
            "目前公开文字信息有限",
            "目前官方公开内容为标题级视频新闻",
            "现在可以确认的事实边界很清楚",
            "视频里提到的三景具体怎么展开",
        ):
            with self.subTest(phrase=phrase):
                draft = {
                    "item_id": "item-1", "profile_id": "city", "title": "宜宾变化",
                    "html": f"<p>{phrase}</p>",
                    "fact_refs": [{"claim": "新增线路", "evidence": "新增3条公交线路"}],
                    "editor_route": "练团长",
                }
                self.assertIn(
                    "ai_writing_pattern:material_boundary_exposure",
                    validate_draft(draft, SOURCE_ITEM),
                )


if __name__ == "__main__":
    unittest.main()
