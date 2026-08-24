import unittest

from dayibin_auto_publisher.comment_safety import comment_quality_score, validate_comment


POST = {
    "thread_id": "100",
    "title": "宜宾叙州区新增公交站，通勤线路有变化",
    "content": "叙州区新增公交站后，大家更关心换乘距离。",
    "facts": [
        {"id": "F1", "text": "宜宾叙州区新增公交站"},
        {"id": "F2", "text": "大家更关心换乘距离"},
    ],
}


def generated(
    comment: str,
    *,
    refs: list[str] | None = None,
    understanding: str = "原帖说叙州区新增公交站后，大家更关心换乘距离。",
    hook: str = "新增公交站之后，换乘距离是不是更近才是具体看点。",
    adds_value: str = "用实际换乘体验补充判断",
) -> dict[str, object]:
    return {
        "thread_id": "100",
        "profile_id": "observer",
        "post_understanding": understanding,
        "reply_hook": hook,
        "comment": comment,
        "post_fact_refs": refs if refs is not None else ["F1", "F2"],
        "adds_value": adds_value,
        "risk_flags": [],
    }


class CommentSafetyTests(unittest.TestCase):
    def test_accepts_comment_that_reuses_post_facts_without_new_claims(self) -> None:
        reasons = validate_comment(
            generated("叙州区新增公交站后通勤会有变化，大家最想先改善哪一段换乘距离？"),
            POST,
        )

        self.assertEqual(reasons, [])

    def test_rejects_new_number_place_fake_experience_and_sensitive_content(self) -> None:
        cases = {
            "NEW_NUMBER": "叙州区新增公交站后通勤会有变化，预计2天就能改善换乘距离。",
            "NEW_NAMED_ENTITY": "翠屏山公园新增公交站后更方便，大家最想先改善哪一段换乘距离？",
            "FAKE_EXPERIENCE": "我亲眼看见叙州区新增公交站，昨天去过以后觉得换乘距离更近了。",
            "HIGH_RISK_CONTENT": "叙州区新增公交站值得讨论，这背后是否存在政治利益和违法问题？",
            "PRODUCTION_TERM": "叙州区新增公交站后通勤有变化，这条运营马甲评论最该追问换乘距离。",
        }
        for expected, comment in cases.items():
            with self.subTest(expected=expected):
                self.assertIn(expected, validate_comment(generated(comment), POST))

    def test_rejects_missing_fact_reference(self) -> None:
        self.assertIn(
            "UNKNOWN_FACT_REF",
            validate_comment(generated("叙州区公交有变化，大家怎么看？", refs=["F9"]), POST),
        )

    def test_accepts_specific_two_character_fact_terms(self) -> None:
        movie_post = {
            "thread_id": "200",
            "title": "宜宾电影院为《牛来》加场",
            "content": "宜宾电影院开始加场，热度来自网友评论、玩梗和围观。",
            "facts": [
                {"id": "F3", "text": "宜宾电影院现在开始加场"},
                {"id": "F5", "text": "网友评论和玩梗带来围观"},
            ],
        }
        comment = {
            "thread_id": "200",
            "profile_id": "counterpoint",
            "post_understanding": "原帖说《牛来》加场，热度与网友玩梗有关。",
            "reply_hook": "加场与玩梗围观之间有反差。",
            "comment": "加场可以理解，但热度也可能来自玩梗与围观。",
            "post_fact_refs": ["F3", "F5"],
            "adds_value": "补充热度来源变量",
            "risk_flags": [],
        }

        reasons = validate_comment(comment, movie_post)

        self.assertNotIn("FACT_NOT_USED", reasons)
        self.assertEqual(reasons, [])

    def test_accepts_both_short_and_long_comments_without_forced_keywords_or_question(self) -> None:
        short = "站是多了，少走两步才算真方便。"
        long = (
            "叙州区新增公交站后通勤会有变化，这件事值得关注。"
            "换乘距离是否改善，比单纯增加数量更重要，建议后续继续观察通勤人群的实际选择和变化，"
            "也可以看看大家最关心的换乘距离有没有变化。"
        )

        self.assertEqual(validate_comment(generated(short, refs=["F1"]), POST), [])
        self.assertEqual(validate_comment(generated(long), POST), [])

    def test_quality_rewards_grounded_understanding_hook_and_value_not_question_marks(self) -> None:
        strong = generated(
            "站是多了，少走两步才算真方便。"
        )
        shallow = generated(
            "大家怎么看？",
            understanding="",
            hook="",
            adds_value="",
        )

        strong_score = comment_quality_score(strong, POST)
        shallow_score = comment_quality_score(shallow, POST)

        self.assertGreaterEqual(strong_score["score"], 80)
        self.assertLess(shallow_score["score"], 60)
        self.assertIn("UNDERSTANDING_REQUIRED", validate_comment(shallow, POST))

    def test_rejects_recurring_ai_template_skeleton(self) -> None:
        reasons = validate_comment(
            generated("这个影响不小，更关键的变量是换乘距离。"),
            POST,
        )

        self.assertIn("AI_TEMPLATE", reasons)

    def test_rejects_editorial_stamp_and_meaning_translation_voice(self) -> None:
        cases = [
            "车停着，货也跟着停，这个细节挺真实。",
            "路面变宽这事，听着像工程量，落到路上就是少一点互相将就。",
            "这种就舒服在不用专门安排一大趟。",
            "这种画面比单独说宜宾造走出去更实在。",
            "一个城市的名片，有时候就是这么一边跑、一边装出来的。",
            "街头和车间这一前一后挺有画面。",
            "分幅分段修这个点还是关键。",
            "低于22一斤这个线很具体。",
            "原料绕了好几个国家，这个跨度还挺大。",
            "街上一列车间一列，这节奏确实有点忙。",
        ]

        for text in cases:
            with self.subTest(text=text):
                self.assertIn("EDITORIAL_VOICE", validate_comment(generated(text), POST))

    def test_rejects_packing_three_post_facts_into_one_comment(self) -> None:
        reasons = validate_comment(
            generated("车、货、线路都齐了，最后还是卡在排队。"),
            POST,
        )

        self.assertIn("FACT_PACKING", reasons)

    def test_generic_words_ending_in_road_or_station_are_not_named_entities(self) -> None:
        charging_post = {
            "thread_id": "300",
            "title": "宜宾新增一个充电站",
            "content": "充电十分钟左右就能将电量补至九成，新增站点方便临时补电。",
            "facts": [
                {"id": "F1", "text": "充电十分钟左右就能将电量补至九成"},
            ],
        }
        comment = {
            "thread_id": "300",
            "profile_id": "observer",
            "post_understanding": "原帖说充电十分钟左右可以补到九成。",
            "reply_hook": "补电速度和是否顺路是两个不同使用尺度。",
            "comment": (
                "充电十分钟左右就能将电量补至九成很实用，但对普通用户来说，"
                "新增站点的价值还在于能不能把临时补电变成顺路补电。"
            ),
            "post_fact_refs": ["F1"],
            "adds_value": "补充顺路补电的使用价值",
            "risk_flags": [],
        }

        self.assertNotIn("NEW_NAMED_ENTITY", validate_comment(comment, charging_post))


if __name__ == "__main__":
    unittest.main()
