from datetime import UTC, datetime
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dayibin_auto_publisher.comment_dispatcher import dispatch_comments
from dayibin_auto_publisher.config import CommenterConfig, PipelineConfig
from dayibin_auto_publisher.storage import atomic_write_json


NOW = datetime(2026, 8, 19, 8, 0, tzinfo=UTC)


class StaticRng:
    def randint(self, start: int, end: int) -> int:
        return start

    def choice(self, values):
        return values[0]

    def sample(self, values, count: int):
        return list(values[:count])


class FlowAgent:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.publish_calls = 0

    def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
        self.calls.append(prompt)
        if "review/thread/index" in prompt:
            return {"posts": [_post(str(index)) for index in range(1, 7)]}
        if "生成评论区回复" in prompt:
            return {
                "comments": [
                    {
                        "thread_id": str(index),
                        "profile_id": "observer",
                        "post_understanding": "原帖说叙州区新增公交站，大家关心换乘距离。",
                        "reply_hook": "新增公交站与换乘距离之间有具体落差。",
                        "comment": "叙州区新增公交站后通勤会有变化，大家最想先改善哪一段换乘距离？",
                        "post_fact_refs": ["F1", "F2"],
                        "adds_value": "指出通勤影响并追问换乘距离",
                        "risk_flags": [],
                    }
                    for index in range(1, 7)
                ]
            }
        if "/review/vest-reply/add" in prompt:
            self.publish_calls += 1
            ids = ["1", "2", "3", "4", "5"] if self.publish_calls == 1 else ["6"]
            return {
                "publish_results": [
                    {
                        "thread_id": thread_id,
                        "status": "published",
                        "url": f"https://dayibin.cn/wap/thread/view-thread/tid/{thread_id}",
                        "vest_id": "88",
                        "reply_id": f"reply-{thread_id}",
                    }
                    for thread_id in ids
                ]
            }
        raise AssertionError("unexpected prompt")


class FakePostSource:
    def __init__(self) -> None:
        self.calls = 0

    def fetch_approved_posts(self, *, now, lookback_hours: int, max_items: int):
        self.calls += 1
        return [_post(str(index)) for index in range(1, 7)]


class EighteenPostSource:
    def fetch_approved_posts(self, *, now, lookback_hours: int, max_items: int):
        return [_post(str(index)) for index in range(1, 19)]


class ConciseNewsSource:
    def fetch_approved_posts(self, *, now, lookback_hours: int, max_items: int):
        return [
            {
                "thread_id": "news-1",
                "pid": "pid-news-1",
                "fid": "49",
                "forum": "大美宜宾",
                "title": "宜宾新增一个充电站",
                "content": "翠屏区中坝公园新增充电站，今天正式开放。",
                "published_at": "2026-08-19T07:00:00Z",
                "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=news-1",
            }
        ]


class PatrolSource:
    def fetch_approved_posts(self, *, now, lookback_hours: int, max_items: int):
        return []

    def fetch_history_posts(
        self,
        *,
        now,
        lookback_days: int,
        page: int,
        max_items: int,
        exclude_thread_ids: set[str],
    ):
        return {
            "page": page,
            "total_pages": 3,
            "posts": [
                {
                    "thread_id": "300",
                    "pid": "pid-300",
                    "fid": "75",
                    "forum": "酒都播报",
                    "title": "宜宾公园新步道开放，周末出行多了选择",
                    "content": (
                        "宜宾公园的新步道已经开放，入口和开放时间都已说明。"
                        "周边居民周末出行时，大家更在意停车还是步行距离？"
                    ),
                    "published_at": "2026-08-10T07:00:00Z",
                    "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=300",
                }
            ],
        }

    def fetch_reply_candidates(self, **_kwargs):
        return [
            {
                "thread_id": "200",
                "target_reply_id": "555",
                "pid": "555",
                "fid": "67",
                "forum": "城市更新",
                "title": "宜宾新增一个充电站",
                "content": "服务费是重点",
                "target_comment": "服务费是重点",
                "published_at": "2026-08-19T07:30:00Z",
                "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=200",
                "facts": [
                    {"id": "F1", "text": "宜宾新增一个充电站"},
                    {"id": "C1", "text": "服务费是重点"},
                ],
            }
        ]


def _post(thread_id: str) -> dict[str, str]:
    return {
        "thread_id": thread_id,
        "pid": f"pid-{thread_id}",
        "fid": "75",
        "forum": "酒都播报",
        "title": "宜宾叙州区新增公交站，通勤线路有变化",
        "content": (
            "叙州区新增公交站后，早晚通勤的乘客会受到影响。"
            "目前大家更关心换乘距离和高峰时段，哪一段最需要优化？"
        ),
        "published_at": "2026-08-19T07:00:00Z",
        "url": f"https://dayibin.cn/wap/thread/view-thread/tid/{thread_id}",
    }


def _config(root: Path, *, enabled: bool) -> PipelineConfig:
    profiles = (
        {
            "id": "observer",
            "role": "社区观察员",
            "instruction": "点出一个影响，再问一个具体问题",
            "vest_name": "观察号" if enabled else "",
            "vest_id": "88" if enabled else "",
            "per_run_min": 6,
            "per_run_max": 9,
        },
        {
            "id": "helper",
            "role": "宜宾实用派",
            "instruction": "补一条可核实信息或操作提醒",
            "vest_name": "实用号" if enabled else "",
            "vest_id": "89" if enabled else "",
            "per_run_min": 6,
            "per_run_max": 9,
        },
        {
            "id": "counterpoint",
            "role": "克制不同意见",
            "instruction": "承认合理处，再补一个不同变量",
            "vest_name": "不同意见号" if enabled else "",
            "vest_id": "90" if enabled else "",
            "per_run_min": 6,
            "per_run_max": 9,
        },
    )
    return PipelineConfig(
        source_db=root / "unused.db",
        data_dir=root / "data",
        agent_id="hotspot-writer",
        model="easyai/gpt-5.5",
        commenter=CommenterConfig(enabled=enabled, profiles=profiles),
    )


class CommentScheduleTests(unittest.TestCase):
    def test_not_due_makes_zero_agent_calls(self) -> None:
        with TemporaryDirectory() as tmp:
            config = _config(Path(tmp), enabled=False)
            state_path = config.data_dir / "commenter-state.json"
            atomic_write_json(
                state_path,
                {
                    "schema_version": 1,
                    "next_run_at": "2026-08-19T10:00:00+00:00",
                    "circuit_open": False,
                    "consecutive_errors": 0,
                },
            )
            agent = FlowAgent()

            report = dispatch_comments(config, agent, now=NOW, send=False, rng=StaticRng())

            self.assertEqual(report["status"], "NOT_DUE")
            self.assertEqual(agent.calls, [])

    def test_live_round_uses_one_profile_and_splits_five_plus_one(self) -> None:
        with TemporaryDirectory() as tmp:
            config = _config(Path(tmp), enabled=True)
            agent = FlowAgent()
            sleeps: list[int] = []

            report = dispatch_comments(
                config,
                agent,
                now=NOW,
                send=True,
                force=True,
                rng=StaticRng(),
                sleeper=sleeps.append,
            )

            self.assertEqual(report["status"], "PUBLISHED")
            self.assertEqual(report["profile_id"], "observer")
            self.assertEqual(report["generated_count"], 6)
            self.assertEqual(report["published_count"], 6)
            self.assertEqual(agent.publish_calls, 2)
            self.assertEqual(sleeps, [60])
            state = json.loads((config.data_dir / "commenter-state.json").read_text())
            self.assertEqual(state["last_profile_id"], "observer")
            self.assertEqual(state["next_run_at"], "2026-08-19T09:30:00+00:00")

    def test_canary_limit_publishes_exactly_one_comment(self) -> None:
        class CanaryAgent(FlowAgent):
            def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
                if "生成评论区回复" in prompt:
                    self.calls.append(prompt)
                    return {
                        "comments": [
                            {
                                "thread_id": "1",
                                "profile_id": "observer",
                                "post_understanding": "原帖说叙州区新增公交站，大家关心换乘距离。",
                                "reply_hook": "新增公交站与换乘距离之间有具体落差。",
                                "comment": "叙州区新增公交站后通勤会有变化，大家最想先改善哪一段换乘距离？",
                                "post_fact_refs": ["F1", "F2"],
                                "adds_value": "指出通勤影响并追问换乘距离",
                                "risk_flags": [],
                            }
                        ]
                    }
                if "/review/vest-reply/add" in prompt:
                    self.calls.append(prompt)
                    self.publish_calls += 1
                    return {
                        "publish_results": [
                            {
                                "thread_id": "1",
                                "status": "published",
                                "url": "https://dayibin.cn/wap/thread/view-thread/tid/1",
                                "vest_id": "88",
                                "reply_id": "reply-1",
                            }
                        ]
                    }
                return super().run_json(prompt, session_id=session_id)

        with TemporaryDirectory() as tmp:
            config = _config(Path(tmp), enabled=True)
            agent = CanaryAgent()

            report = dispatch_comments(
                config,
                agent,
                now=NOW,
                send=True,
                force=True,
                max_comments=1,
                rng=StaticRng(),
                sleeper=lambda _seconds: None,
            )

            self.assertEqual(report["selected_count"], 1)
            self.assertEqual(report["published_count"], 1)
            self.assertEqual(agent.publish_calls, 1)

    def test_direct_post_source_bypasses_agent_fetch_prompt(self) -> None:
        with TemporaryDirectory() as tmp:
            config = _config(Path(tmp), enabled=False)
            agent = FlowAgent()
            source = FakePostSource()

            report = dispatch_comments(
                config,
                agent,
                now=NOW,
                send=False,
                force=True,
                post_source=source,
                rng=StaticRng(),
            )

            self.assertEqual(source.calls, 1)
            self.assertEqual(report["status"], "DRY_RUN_READY")
            self.assertFalse(any("review/thread/index" in prompt for prompt in agent.calls))

    def test_short_opinion_comment_is_accepted_without_format_repair(self) -> None:
        class RepairAgent(FlowAgent):
            def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
                self.calls.append(prompt)
                if "生成评论区回复" in prompt:
                    return {
                        "comments": [
                            {
                                "thread_id": "1",
                                "profile_id": "observer",
                                "post_understanding": "原帖说叙州区新增公交站，大家关心换乘距离。",
                                "reply_hook": "新增公交站与换乘距离之间有具体落差。",
                                "comment": "叙州区公交变化值得关注。",
                                "post_fact_refs": ["F1"],
                                "adds_value": "追问",
                                "risk_flags": [],
                            }
                        ]
                    }
                raise AssertionError("unexpected prompt")

        with TemporaryDirectory() as tmp:
            config = _config(Path(tmp), enabled=False)
            agent = RepairAgent()
            source = FakePostSource()

            report = dispatch_comments(
                config,
                agent,
                now=NOW,
                send=False,
                force=True,
                max_comments=1,
                post_source=source,
                rng=StaticRng(),
            )

            self.assertEqual(report["status"], "DRY_RUN_READY")
            self.assertEqual(report["safety_rejected_count"], 0)
            self.assertEqual(len(agent.calls), 1)

    def test_concise_news_is_researched_before_generation(self) -> None:
        class ResearchAgent(FlowAgent):
            def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
                self.calls.append(prompt)
                if "补充可核验背景" in prompt:
                    return {
                        "research": [
                            {
                                "thread_id": "news-1",
                                "status": "grounded",
                                "facts": [
                                    {
                                        "text": "宜宾官方资料显示该充电站设置12个充电位",
                                        "url": "https://www.yibin.gov.cn/xxgk/charging.html",
                                        "source_name": "宜宾市政府",
                                        "source_tier": "primary",
                                    }
                                ],
                            }
                        ]
                    }
                if "生成评论区回复" in prompt:
                    if '"id": "R1"' not in prompt:
                        raise AssertionError("research fact was not merged into generation input")
                    return {
                        "comments": [
                            {
                                "thread_id": "news-1",
                                "profile_id": "observer",
                                "post_understanding": "原帖说宜宾新增一个充电站。",
                                "reply_hook": "新增一个充电站的充电位数量值得回应。",
                                "comment": "宜宾新增一个充电站值得肯定，12个充电位能否真正改善周边补能体验？",
                                "post_fact_refs": ["F1", "R1"],
                                "adds_value": "肯定新增设施，并判断其价值要看实际补能改善",
                                "risk_flags": [],
                            }
                        ]
                    }
                raise AssertionError("unexpected prompt")

        with TemporaryDirectory() as tmp:
            config = _config(Path(tmp), enabled=False)
            config = replace(
                config,
                commenter=replace(
                    config.commenter,
                    research_enabled=True,
                    research_max_posts=3,
                ),
            )
            agent = ResearchAgent()

            report = dispatch_comments(
                config,
                agent,
                now=NOW,
                send=False,
                force=True,
                post_source=ConciseNewsSource(),
                rng=StaticRng(),
            )

            self.assertEqual(report["status"], "DRY_RUN_READY")
            self.assertEqual(report["research_requested_count"], 1)
            self.assertEqual(report["research_grounded_count"], 1)
            research_path = config.data_dir / "2026-08-19" / "comments" / "research.json"
            saved = json.loads(research_path.read_text())
            self.assertEqual(saved["results"][0]["facts"][0]["id"], "R1")
            self.assertEqual(len(agent.calls), 2)

    def test_news_with_insufficient_research_is_skipped_without_generation(self) -> None:
        class InsufficientResearchAgent(FlowAgent):
            def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
                self.calls.append(prompt)
                if "补充可核验背景" in prompt:
                    return {
                        "research": [
                            {
                                "thread_id": "news-1",
                                "status": "insufficient",
                                "facts": [],
                            }
                        ]
                    }
                raise AssertionError("generation must not run without grounded research")

        with TemporaryDirectory() as tmp:
            config = _config(Path(tmp), enabled=False)
            config = replace(
                config,
                commenter=replace(config.commenter, research_enabled=True),
            )
            agent = InsufficientResearchAgent()

            report = dispatch_comments(
                config,
                agent,
                now=NOW,
                send=False,
                force=True,
                post_source=ConciseNewsSource(),
                rng=StaticRng(),
            )

            self.assertEqual(report["status"], "NO_CANDIDATES")
            self.assertEqual(report["research_requested_count"], 1)
            self.assertEqual(report["research_grounded_count"], 0)
            self.assertEqual(report["research_skipped_count"], 1)
            self.assertEqual(len(agent.calls), 1)

    def test_history_patrol_adds_one_old_post_and_one_targeted_reply(self) -> None:
        class PatrolAgent(FlowAgent):
            def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
                self.calls.append(prompt)
                if "生成评论区回复" in prompt:
                    return {
                        "comments": [
                            {
                                "thread_id": "300",
                                "profile_id": "observer",
                                "post_understanding": "原帖说宜宾公园新步道开放。",
                                "reply_hook": "新步道与步行距离之间有具体体验差异。",
                                "comment": "宜宾公园新步道值得关注，因为步行距离会影响周边居民的出行体验。",
                                "post_fact_refs": ["F1"],
                                "adds_value": "指出步行距离对居民出行的影响",
                                "risk_flags": [],
                            }
                        ]
                    }
                if "只能回复目标网友评论" in prompt:
                    return {
                        "replies": [
                            {
                                "thread_id": "200",
                                "target_reply_id": "555",
                                "profile_id": "observer",
                                "post_understanding": "原帖说宜宾新增一个充电站，网友关心服务费。",
                                "reply_hook": "服务费会改变网友对充电站的判断。",
                                "comment": "服务费确实是重点，因为它会直接影响用户的长期使用体验。",
                                "post_fact_refs": ["C1"],
                                "adds_value": "补充长期使用成本变量",
                                "risk_flags": [],
                            }
                        ]
                    }
                raise AssertionError("unexpected prompt")

        with TemporaryDirectory() as tmp:
            config = _config(Path(tmp), enabled=False)
            config = replace(
                config,
                commenter=replace(
                    config.commenter,
                    history_patrol_enabled=True,
                    history_reply_enabled=True,
                ),
            )
            prior_path = config.data_dir / "2026-08-19" / "comments" / "publish-results.json"
            atomic_write_json(
                prior_path,
                {
                    "schema_version": 1,
                    "business_date": "2026-08-19",
                    "results": [
                        {
                            "thread_id": "200",
                            "status": "published",
                            "vest_id": "88",
                            "reply_id": "444",
                        }
                    ],
                },
            )

            report = dispatch_comments(
                config,
                PatrolAgent(),
                now=NOW,
                send=False,
                force=True,
                max_comments=3,
                post_source=PatrolSource(),
                rng=StaticRng(),
            )

            self.assertEqual(report["status"], "DRY_RUN_READY")
            self.assertEqual(report["history_selected_count"], 1)
            self.assertEqual(report["reply_generated_count"], 1)
            self.assertEqual(report["reply_safety_rejected_count"], 0)
            state = json.loads((config.data_dir / "commenter-state.json").read_text())
            self.assertEqual(state["history_page_cursor"], 2)
            day_dir = config.data_dir / "2026-08-19" / "comments"
            self.assertTrue((day_dir / "history-patrol.json").exists())
            self.assertTrue((day_dir / "generated-replies.json").exists())

    def test_all_three_profiles_each_receive_six_distinct_threads(self) -> None:
        import re

        class MultiProfileAgent(FlowAgent):
            def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
                self.calls.append(prompt)
                profile_id = next(
                    profile_id
                    for profile_id in ("observer", "helper", "counterpoint")
                    if f'"id": "{profile_id}"' in prompt
                )
                thread_ids = list(dict.fromkeys(re.findall(r'"thread_id": "(\d+)"', prompt)))
                return {
                    "comments": [
                        {
                            "thread_id": thread_id,
                            "profile_id": profile_id,
                            "post_understanding": "原帖说叙州区新增公交站，大家关心换乘距离。",
                            "reply_hook": "新增公交站与换乘距离之间有具体落差。",
                            "comment": "叙州区新增公交站值得关注，因为换乘距离会影响通勤用户的实际体验。",
                            "post_fact_refs": ["F1"],
                            "adds_value": "说明换乘距离对通勤用户的影响",
                            "risk_flags": [],
                        }
                        for thread_id in thread_ids
                    ]
                }

        with TemporaryDirectory() as tmp:
            config = _config(Path(tmp), enabled=False)
            profiles = tuple({**profile, "per_run_max": 6} for profile in config.commenter.profiles)
            config = replace(
                config,
                commenter=replace(
                    config.commenter,
                    all_profiles_each_round=True,
                    profiles=profiles,
                ),
            )

            report = dispatch_comments(
                config,
                MultiProfileAgent(),
                now=NOW,
                send=False,
                force=True,
                max_comments=18,
                post_source=EighteenPostSource(),
                rng=StaticRng(),
            )

            self.assertEqual(report["selected_count"], 18)
            self.assertEqual(report["generated_count"], 18)
            self.assertEqual(
                report["profile_target_counts"],
                {"observer": 6, "helper": 6, "counterpoint": 6},
            )
            generated = json.loads(
                (config.data_dir / "2026-08-19" / "comments" / "generated-comments.json").read_text()
            )["comments"]
            self.assertEqual(len({item["thread_id"] for item in generated}), 18)

    def test_dispatcher_uses_direct_qianfan_publisher_when_available(self) -> None:
        class DirectSource(FakePostSource):
            def __init__(self) -> None:
                super().__init__()
                self.publish_calls = 0

            def publish_replies(self, **kwargs):
                self.publish_calls += 1
                item = kwargs["pending"][0]
                return {
                    "publish_results": [
                        {
                            "thread_id": item["thread_id"],
                            "status": "published",
                            "url": item["url"],
                            "vest_id": kwargs["vest_id"],
                            "reply_id": "direct-1",
                        }
                    ]
                }

        class GenerationOnlyAgent(FlowAgent):
            def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
                if "/review/vest-reply/add" in prompt:
                    raise AssertionError("publisher Agent path must not run")
                self.calls.append(prompt)
                return {
                    "comments": [
                        {
                            "thread_id": "1",
                            "profile_id": "observer",
                            "post_understanding": "原帖说叙州区新增公交站，大家关心换乘距离。",
                            "reply_hook": "新增公交站与换乘距离之间有具体落差。",
                            "comment": "叙州区新增公交站值得关注，因为换乘距离会影响通勤用户的实际体验。",
                            "post_fact_refs": ["F1"],
                            "adds_value": "说明通勤影响",
                            "risk_flags": [],
                        }
                    ]
                }

        with TemporaryDirectory() as tmp:
            config = _config(Path(tmp), enabled=True)
            source = DirectSource()
            report = dispatch_comments(
                config,
                GenerationOnlyAgent(),
                now=NOW,
                send=True,
                force=True,
                max_comments=1,
                post_source=source,
                rng=StaticRng(),
            )

            self.assertEqual(report["published_count"], 1)
            self.assertEqual(source.publish_calls, 1)

    def test_history_patrol_scans_multiple_pages_to_fill_eighteen_targets(self) -> None:
        import re

        class PagedHistorySource:
            def __init__(self) -> None:
                self.pages: list[int] = []

            def fetch_approved_posts(self, **_kwargs):
                return []

            def fetch_history_posts(self, *, page: int, **_kwargs):
                self.pages.append(page)
                posts = []
                for index in range(6):
                    item = _post(str(page * 100 + index))
                    item["published_at"] = "2026-08-10T07:00:00Z"
                    posts.append(item)
                return {"page": page, "total_pages": 10, "posts": posts}

            def fetch_reply_candidates(self, **_kwargs):
                return []

        class MultiProfileAgent(FlowAgent):
            def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
                self.calls.append(prompt)
                profile_id = next(
                    profile_id
                    for profile_id in ("observer", "helper", "counterpoint")
                    if f'"id": "{profile_id}"' in prompt
                )
                thread_ids = list(dict.fromkeys(re.findall(r'"thread_id": "(\d+)"', prompt)))
                return {
                    "comments": [
                        {
                            "thread_id": thread_id,
                            "profile_id": profile_id,
                            "post_understanding": "原帖说叙州区新增公交站，大家关心换乘距离。",
                            "reply_hook": "新增公交站与换乘距离之间有具体落差。",
                            "comment": "叙州区新增公交站值得关注，因为换乘距离会影响通勤用户的实际体验。",
                            "post_fact_refs": ["F1"],
                            "adds_value": "说明通勤影响",
                            "risk_flags": [],
                        }
                        for thread_id in thread_ids
                    ]
                }

        with TemporaryDirectory() as tmp:
            config = _config(Path(tmp), enabled=False)
            profiles = tuple({**profile, "per_run_max": 6} for profile in config.commenter.profiles)
            config = replace(
                config,
                commenter=replace(
                    config.commenter,
                    all_profiles_each_round=True,
                    profiles=profiles,
                    history_patrol_enabled=True,
                    history_pages_per_round=6,
                    history_new_posts_per_round=18,
                    history_reply_enabled=False,
                ),
            )
            source = PagedHistorySource()

            report = dispatch_comments(
                config,
                MultiProfileAgent(),
                now=NOW,
                send=False,
                force=True,
                max_comments=18,
                post_source=source,
                rng=StaticRng(),
            )

            self.assertEqual(source.pages, [1, 2, 3])
            self.assertEqual(report["history_selected_count"], 18)
            self.assertEqual(
                report["profile_target_counts"],
                {"observer": 6, "helper": 6, "counterpoint": 6},
            )


if __name__ == "__main__":
    unittest.main()
