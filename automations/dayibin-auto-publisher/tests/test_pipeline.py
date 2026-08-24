from datetime import UTC, date, datetime
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from dayibin_auto_publisher.config import PipelineConfig
from dayibin_auto_publisher.openclaw import AgentError
from dayibin_auto_publisher.pipeline import PipelineError, run_day


class FakeAgent:
    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, str]] = []

    def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
        self.calls.append((prompt, session_id))
        return self.responses.pop(0)


class FailingAgent:
    def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
        raise AgentError("OpenClaw agent failed: LLM request failed")


class PipelineTests(unittest.TestCase):
    def test_run_day_persists_selection_failure_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "radar.db"
            self._create_source_db(db_path)
            config = PipelineConfig(
                source_db=db_path,
                data_dir=root / "data",
                agent_id="hotspot-writer",
                model="easyai/gpt-5.5",
                profiles=({"id": "city", "name": "宜宾路上见"},),
            )

            with self.assertRaises(AgentError):
                run_day(
                    config,
                    FailingAgent(),
                    business_date=date(2026, 8, 18),
                    now=datetime(2026, 8, 18, 9, 0, tzinfo=UTC),
                )

            report_path = root / "data" / "2026-08-18" / "run-report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "selection_failed")
            self.assertEqual(report["failed_stage"], "selection")

    def test_run_day_rejects_publish_before_any_agent_call_when_disabled(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "radar.db"
            self._create_source_db(db_path)
            config = PipelineConfig(
                source_db=db_path,
                data_dir=root / "data",
                agent_id="hotspot-writer",
                model="easyai/gpt-5.5",
                profiles=({"id": "city", "name": "宜宾路上见"},),
            )
            agent = FakeAgent([])

            with self.assertRaisesRegex(PipelineError, "publisher.enabled"):
                run_day(
                    config,
                    agent,
                    business_date=date(2026, 8, 18),
                    now=datetime(2026, 8, 18, 9, 0, tzinfo=UTC),
                    publish=True,
                )

            self.assertEqual(agent.calls, [])

    def test_run_day_creates_snapshot_selection_draft_and_reuses_completed_stages(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "radar.db"
            self._create_source_db(db_path)
            config = PipelineConfig(
                source_db=db_path,
                data_dir=root / "data",
                agent_id="hotspot-writer",
                model="easyai/gpt-5.5",
                lookback_hours=48,
                min_body_chars=120,
                snapshot_limit=20,
                selection_limit=1,
                profiles=(
                    {
                        "id": "city",
                        "name": "宜宾路上见",
                        "persona": "关注城市交通变化",
                    },
                ),
            )
            agent = FakeAgent(
                [
                    {
                        "selected": [
                            {
                                "item_id": "item-1",
                                "profile_id": "city",
                                "angle": "新增线路对通勤的影响",
                                "reason": "本地、具体、可讨论",
                            }
                        ]
                    },
                    {
                        "draft": {
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
                    },
                ]
            )
            now = datetime(2026, 8, 18, 9, 0, tzinfo=UTC)

            report = run_day(
                config,
                agent,
                business_date=date(2026, 8, 18),
                now=now,
            )

            day_dir = root / "data" / "2026-08-18"
            self.assertEqual(report["status"], "ready_to_publish")
            self.assertEqual(report["accepted_drafts"], 1)
            self.assertEqual(len(agent.calls), 2)
            for name in ("hotspots.json", "selected.json", "drafts.json", "run-report.json"):
                self.assertTrue((day_dir / name).is_file(), name)
            drafts = json.loads((day_dir / "drafts.json").read_text(encoding="utf-8"))
            self.assertTrue(drafts["drafts"][0]["accepted"])

            second = run_day(
                config,
                agent,
                business_date=date(2026, 8, 18),
                now=now,
            )

            self.assertEqual(second["accepted_drafts"], 1)
            self.assertEqual(len(agent.calls), 2)

    @staticmethod
    def _create_source_db(path: Path) -> None:
        conn = sqlite3.connect(path)
        conn.execute(
            """
            CREATE TABLE raw_items (
                id TEXT PRIMARY KEY, source_id TEXT NOT NULL, canonical_url TEXT,
                title TEXT NOT NULL, summary TEXT, raw_text TEXT, author TEXT,
                published_at TEXT, first_seen_at TEXT NOT NULL, last_seen_at TEXT NOT NULL,
                geo_scope TEXT, source_nature TEXT, verification_state TEXT,
                content_hash TEXT, dedupe_key TEXT NOT NULL,
                is_noise INTEGER NOT NULL DEFAULT 0, noise_reason TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO raw_items VALUES (
                'item-1','source-1','https://example.com/1','宜宾新增3条公交线路',
                '8月18日起，宜宾新增3条公交线路。',
                ?, '作者','2026-08-18T08:00:00Z','2026-08-18T08:05:00Z',
                '2026-08-18T08:05:00Z','yibin','official','verified','hash-1',
                'dedupe-1',0,NULL
            )
            """,
            ("宜宾公交发布消息：8月18日起，新增3条公交线路，方便市民出行。" * 4,),
        )
        conn.commit()
        conn.close()


if __name__ == "__main__":
    unittest.main()
