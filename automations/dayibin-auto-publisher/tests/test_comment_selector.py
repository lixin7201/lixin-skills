from datetime import UTC, datetime
import unittest

from dayibin_auto_publisher.comment_selector import (
    assess_reply_substance,
    select_comment_candidates,
)


NOW = datetime(2026, 8, 19, 8, 0, tzinfo=UTC)


def post(thread_id: str, *, title: str, content: str, published_at: str = "2026-08-19T07:00:00Z") -> dict[str, object]:
    return {
        "thread_id": thread_id,
        "pid": f"pid-{thread_id}",
        "fid": "75",
        "forum": "酒都播报",
        "title": title,
        "content": content,
        "published_at": published_at,
        "url": f"https://dayibin.cn/wap/thread/view-thread/tid/{thread_id}",
    }


class CommentSelectorTests(unittest.TestCase):
    def test_high_risk_posts_are_all_skipped(self) -> None:
        cases = [
            ("政治", "涉及政治政策争议，大家怎么看？"),
            ("事故", "道路发生事故并有人员伤亡。"),
            ("洪峰", "新一轮洪峰过境宜宾，当前仍处于汛情应对阶段。"),
            ("宴席后续", "宜宾升学宴后续，目前5死多伤，主家的孩子刚参加高考。"),
            ("育儿建议", "宝宝频繁夜醒需要排查原因，新生儿是否喂水要听医生建议。"),
            ("产检建议", "孕妈产检时担心数值异常，这里分享孕期调整办法。"),
            ("校园内容", "宜宾小学教师守护童年，家长和学生参加学习活动。"),
            ("失窃求助", "大学生挣学费时摩托车被偷，车牌是川Q233176，求大家帮忙留意。"),
            ("未成年人", "未成年人失踪求助，请扩散。"),
            ("指控", "曝光某商家欺诈，要求追责。"),
            ("删帖", "事情已经解决，发帖人自愿申请删帖。"),
            ("娃娃退费", "给娃娃报了游泳班，现在退费要扣违约金，合理吗？"),
            ("医院表彰", "宜宾医院举行医师表彰大会，多名医务工作者获奖。"),
        ]

        result = select_comment_candidates(
            [
                post(str(index), title=f"宜宾{label}消息", content=content)
                for index, (label, content) in enumerate(cases, start=1)
            ],
            now=NOW,
            score_threshold=75,
        )

        self.assertEqual(result["eligible"], [])
        self.assertEqual(
            {item["reason"] for item in result["skipped"]},
            {"SKIP_HIGH_RISK"},
        )

    def test_deduplicates_and_selects_only_complete_high_value_posts(self) -> None:
        safe = post(
            "100",
            title="宜宾叙州区新增公交站，通勤线路有变化",
            content=(
                "叙州区这条公交线路新增了一个站点，早晚通勤的乘客会受到影响。"
                "目前大家最关心的是换乘距离和高峰时段，哪一段最需要继续优化？"
            ),
        )
        low_value = post("101", title="随手记", content="今天天气不错。")

        result = select_comment_candidates(
            [safe, safe.copy(), low_value],
            now=NOW,
            score_threshold=75,
            already_commented_thread_ids={"999"},
        )

        self.assertEqual([item["thread_id"] for item in result["eligible"]], ["100"])
        self.assertGreaterEqual(result["eligible"][0]["score"], 75)
        self.assertEqual(
            [(item["thread_id"], item["reason"]) for item in result["skipped"]],
            [("100", "SKIP_DUPLICATE"), ("101", "SKIP_LOW_INFORMATION")],
        )

    def test_previously_commented_thread_never_reenters_candidates(self) -> None:
        candidate = post(
            "200",
            title="宜宾公园新步道开放，周末出行多了选择",
            content=(
                "宜宾这个公园的新步道已经开放，入口和开放时间都已在帖子中说明。"
                "周末带家人出行时，大家更在意停车还是步行距离？"
            ),
        )

        result = select_comment_candidates(
            [candidate],
            now=NOW,
            score_threshold=75,
            already_commented_thread_ids={"200"},
        )

        self.assertEqual(result["eligible"], [])
        self.assertEqual(result["skipped"][0]["reason"], "SKIP_ALREADY_COMMENTED")

    def test_forum_membership_alone_does_not_count_as_local_specificity(self) -> None:
        national = post(
            "300",
            title="国家发布城市公共设施管理标准",
            content=(
                "市场监管总局批准发布城市公共设施管理通用要求，明确设施规划建设和运行维护要求。"
                "这项标准将影响城市公共设施管理，大家更关心实施细节和公开解读。"
            ),
        )

        result = select_comment_candidates(
            [national],
            now=NOW,
            score_threshold=75,
        )

        self.assertEqual(result["eligible"], [])
        self.assertEqual(result["skipped"][0]["reason"], "SKIP_NON_LOCAL")

    def test_promotional_contact_post_is_skipped_before_scoring(self) -> None:
        promotion = post(
            "400",
            title="筠连县商业综合体招商预热",
            content="超市可整租分割，诚邀实地考察洽谈合作，联系电话13056659199。",
        )

        result = select_comment_candidates(
            [promotion],
            now=NOW,
            score_threshold=75,
        )

        self.assertEqual(result["eligible"], [])
        self.assertEqual(result["skipped"][0]["reason"], "SKIP_PROMOTION")

    def test_job_recruitment_is_skipped_as_promotion(self) -> None:
        recruitment = post(
            "401",
            title="宜宾临港有没有找工作的",
            content="早九晚六，一个月四天假，工资3500，有没有一起的小伙伴？",
        )

        result = select_comment_candidates([recruitment], now=NOW, score_threshold=75)

        self.assertEqual(result["eligible"], [])
        self.assertEqual(result["skipped"][0]["reason"], "SKIP_PROMOTION")

    def test_water_posts_are_skipped_before_model_scoring(self) -> None:
        water_posts = [
            post("501", title="宜宾今天怎么样", content="如题，大家怎么看？"),
            post("502", title="宜宾打卡", content="哈哈哈哈哈哈哈哈哈哈哈哈。"),
            post("503", title="宜宾新增充电站", content="宜宾新增充电站"),
            post("504", title="宜宾随手说", content="宜宾宜宾宜宾宜宾宜宾宜宾宜宾宜宾宜宾宜宾。"),
        ]

        result = select_comment_candidates(
            water_posts,
            now=NOW,
            score_threshold=75,
        )

        self.assertEqual(result["eligible"], [])
        self.assertEqual(
            [(item["thread_id"], item["reason"]) for item in result["skipped"]],
            [(str(index), "SKIP_LOW_INFORMATION") for index in range(501, 505)],
        )

    def test_short_fact_dense_local_post_is_not_treated_as_water(self) -> None:
        concise_news = post(
            "510",
            title="宜宾新增充电站",
            content="翠屏区中坝公园8月20日新增12个充电位，今天正式开放。",
        )

        result = select_comment_candidates(
            [concise_news],
            now=NOW,
            score_threshold=75,
        )

        self.assertEqual([item["thread_id"] for item in result["eligible"]], ["510"])
        self.assertGreaterEqual(result["eligible"][0]["substance_score"], 60)
        self.assertGreaterEqual(len(result["eligible"][0]["information_signals"]), 2)

    def test_reply_substance_skips_acknowledgements_but_keeps_viewpoints(self) -> None:
        self.assertFalse(assess_reply_substance("晓得了晓得了")["eligible"])
        self.assertFalse(assess_reply_substance("哈哈")["eligible"])
        self.assertFalse(assess_reply_substance("好丑啊哈哈哈哈")["eligible"])
        self.assertFalse(assess_reply_substance("挺期待这次大会的成果的")["eligible"])
        self.assertTrue(assess_reply_substance("服务费是重点")["eligible"])
        self.assertTrue(assess_reply_substance("大手洋是哪？")["eligible"])


if __name__ == "__main__":
    unittest.main()
