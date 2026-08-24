from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import tempfile
import unittest

from dayibin_auto_publisher.traffic_patrol import (
    parse_official_detail,
    parse_official_listing,
    run_public_service_branches,
    run_traffic_patrol,
)


NOW = datetime(2026, 8, 23, 12, 10, tzinfo=UTC)
SOURCE = "yibin-traffic-police"
BASE = "https://ybjj.yibin.gov.cn/jwyw/gsgg/"


def listing(*rows: tuple[str, str, str]) -> str:
    return "<ul>" + "".join(
        f'<li><a href="{href}">{title}</a><span>{day}</span></li>'
        for href, title, day in rows
    ) + "</ul>"


def detail(title: str, body: str, day: str = "2026年08月23日") -> str:
    return f"""
    <div class="public-title-nav">
      <div class="title">{title}</div>
      <span class="time">发布时间：{day}</span>
    </div>
    <div class="font-content-box"><style>.x{{}}</style><p>{body}</p></div>
    """


def official_item(identifier: str, *, title: str, body: str) -> dict[str, object]:
    return {
        "identifier": identifier,
        "source_id": SOURCE,
        "source_url": f"{BASE}202608/t20260823_{identifier}.html",
        "observed_at": NOW.isoformat(timespec="seconds"),
        "published_date": "2026-08-23",
        "title": title,
        "body": body,
        "body_complete": True,
    }


def valid_draft(prompt: str, _session_id: str) -> dict[str, object]:
    event = json.loads(prompt.split("官方交通事实：", 1)[1].split("\n\n硬规则", 1)[0])
    evidence = "宜庆西街实施临时交通管制"
    return {"draft": {
        "item_id": event["identifier"],
        "profile_id": "forever21",
        "title": "宜庆西街将临时管制，过往车辆注意绕行",
        "html": "<p>宜庆西街实施临时交通管制，过往车辆请按现场指引绕行。</p>",
        "fact_refs": [{"claim": evidence, "evidence": evidence}],
        "editor_route": "采采呀",
    }}


class TrafficPatrolTests(unittest.TestCase):
    def test_parses_official_listing_and_detail(self) -> None:
        title = "关于对叙州区宜庆西街实施临时交通管制的通告"
        rows = parse_official_listing(
            listing(("./202608/t20260823_1.html", title, "2026-08-23")),
            source_id=SOURCE,
            base_url=BASE,
            observed_at=NOW,
        )
        item = parse_official_detail(
            detail(
                title,
                "宜庆西街实施临时交通管制。管制时间为2026年8月24日0时，车辆请绕行叙府路。"
                "管制期间禁止一切车辆通行，过往车辆应严格按照现场交通信号和工作人员指挥通行，提前规划出行路线。",
            ),
            rows[0],
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(item["published_date"], "2026-08-23")
        self.assertIn("宜庆西街实施临时交通管制", item["body"])
        self.assertTrue(item["body_complete"])
        self.assertTrue(str(item["source_url"]).startswith("https://ybjj.yibin.gov.cn/"))

    def test_bootstrap_does_not_backfill_then_new_official_control_creates_card(self) -> None:
        old = official_item(
            "old",
            title="关于对旧街实施临时交通管制的通告",
            body="旧街实施临时交通管制，时间为2026年8月23日8时，车辆绕行旧路。",
        )
        new = official_item(
            "new",
            title="关于对叙州区宜庆西街实施临时交通管制的通告",
            body="宜庆西街实施临时交通管制，时间为2026年8月24日0时，车辆请绕行叙府路。",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = run_traffic_patrol(
                data_dir=root,
                now=NOW,
                source_fetchers={SOURCE: lambda _now, _known: [old]},
                draft_runner=valid_draft,
            )
            second = run_traffic_patrol(
                data_dir=root,
                now=datetime(2026, 8, 23, 12, 11, tzinfo=UTC),
                source_fetchers={SOURCE: lambda _now, _known: [old, {**new, "observed_at": _now.isoformat()}]},
                draft_runner=valid_draft,
            )

            self.assertEqual(first["status"], "BOOTSTRAPPED")
            self.assertEqual(first["card_count"], 0)
            self.assertEqual(second["card_count"], 1)
            self.assertFalse(second["qianfan_called"])
            self.assertFalse(second["push_called"])
            card = json.loads(next((root / "confirmation-cards").glob("*.json")).read_text())
            self.assertEqual(card["document_type"], "城建交通更新")
            self.assertEqual(card["editor_route"], "采采呀")

    def test_irrelevant_or_incomplete_items_are_held_before_model(self) -> None:
        calls = 0

        def runner(_prompt: str, _session_id: str) -> dict[str, object]:
            nonlocal calls
            calls += 1
            return {}

        irrelevant = official_item(
            "news",
            title="宜宾交警开展夏季交通安全宣传",
            body="宜宾交警开展交通安全宣传活动。",
        )
        incomplete = official_item(
            "broken",
            title="关于临时交通管制的通告",
            body="将实施交通管制。",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_traffic_patrol(
                data_dir=root,
                now=NOW,
                source_fetchers={SOURCE: lambda _now, _known: []},
                draft_runner=runner,
            )
            result = run_traffic_patrol(
                data_dir=root,
                now=NOW,
                source_fetchers={SOURCE: lambda _now, _known: [irrelevant, incomplete]},
                draft_runner=runner,
            )

        self.assertEqual(calls, 0)
        self.assertEqual(result["card_count"], 0)
        self.assertEqual(set(result["held_reasons"]), {"incomplete_facts", "not_traffic_disruption"})

    def test_model_failure_fails_closed(self) -> None:
        item = official_item(
            "new",
            title="关于对叙州区宜庆西街实施临时交通管制的通告",
            body="宜庆西街实施临时交通管制，时间为2026年8月24日0时，车辆请绕行叙府路。",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_traffic_patrol(
                data_dir=root,
                now=NOW,
                source_fetchers={SOURCE: lambda _now, _known: []},
                draft_runner=lambda _prompt, _session: {},
            )
            result = run_traffic_patrol(
                data_dir=root,
                now=NOW,
                source_fetchers={SOURCE: lambda _now, _known: [item]},
                draft_runner=lambda _prompt, _session: {},
            )

        self.assertEqual(result["card_count"], 0)
        self.assertIn("draft_failed", result["held_reasons"])

    def test_auto_publish_arms_then_publishes_once_and_never_pushes(self) -> None:
        item = official_item(
            "new",
            title="关于对叙州区宜庆西街实施临时交通管制的通告",
            body="宜庆西街实施临时交通管制，时间为2026年8月24日0时，车辆请绕行叙府路。",
        )
        calls = 0

        def publisher(_card: dict[str, object]) -> dict[str, object]:
            nonlocal calls
            calls += 1
            return {
                "status": "PUBLISHED_VERIFIED",
                "tid": "950101",
                "url": "https://dayibin.cn/forum.php?mod=viewthread&tid=950101",
                "vest_name": "forever21",
                "forum_name": "大美宜宾",
                "type_name": "无",
                "published_at": "2026-08-23T20:12:00+08:00",
            }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            armed = run_traffic_patrol(
                data_dir=root,
                now=NOW,
                source_fetchers={SOURCE: lambda _now, _known: []},
                draft_runner=valid_draft,
                publish=True,
                publisher=publisher,
            )
            published = run_traffic_patrol(
                data_dir=root,
                now=datetime(2026, 8, 23, 12, 11, tzinfo=UTC),
                source_fetchers={SOURCE: lambda _now, _known: [{**item, "observed_at": _now.isoformat()}]},
                draft_runner=valid_draft,
                publish=True,
                publisher=publisher,
            )
            repeated = run_traffic_patrol(
                data_dir=root,
                now=datetime(2026, 8, 23, 12, 12, tzinfo=UTC),
                source_fetchers={SOURCE: lambda _now, _known: [{**item, "observed_at": _now.isoformat()}]},
                draft_runner=valid_draft,
                publish=True,
                publisher=publisher,
            )

        self.assertEqual(armed["status"], "AUTO_PUBLISH_ARMED")
        self.assertEqual(published["published_count"], 1)
        self.assertEqual(repeated["published_count"], 0)
        self.assertEqual(calls, 1)
        self.assertFalse(published["push_called"])

    def test_public_service_branches_are_isolated(self) -> None:
        result = run_public_service_branches({
            "weather": lambda: {"status": "AUTO_PUBLISH_COMPLETE"},
            "traffic": lambda: (_ for _ in ()).throw(RuntimeError("source down")),
        })

        self.assertEqual(result["status"], "PARTIAL_SUCCESS")
        self.assertIn("weather", result["branches"])
        self.assertIn("traffic", result["branch_errors"])


if __name__ == "__main__":
    unittest.main()
