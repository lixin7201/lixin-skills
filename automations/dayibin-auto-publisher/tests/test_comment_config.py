import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dayibin_auto_publisher.config import ConfigError, load_config


BASE_CONFIG = {
    "source_db": "source.db",
    "data_dir": "data",
    "agent": {"id": "hotspot-writer", "model": "easyai/gpt-5.5"},
    "publisher": {"enabled": False, "profiles": []},
}


def comment_profiles(
    *, with_vests: bool, per_run_min: int = 6, per_run_max: int = 9
) -> list[dict[str, object]]:
    names = ["观察号", "实用号", "不同意见号"] if with_vests else ["", "", ""]
    ids = ["88", "89", "90"] if with_vests else ["", "", ""]
    return [
        {
            "id": "observer",
            "vest_name": names[0],
            "vest_id": ids[0],
            "per_run_min": per_run_min,
            "per_run_max": per_run_max,
            "rotation_weight": 1,
        },
        {
            "id": "helper",
            "vest_name": names[1],
            "vest_id": ids[1],
            "per_run_min": per_run_min,
            "per_run_max": per_run_max,
            "rotation_weight": 1,
        },
        {
            "id": "counterpoint",
            "vest_name": names[2],
            "vest_id": ids[2],
            "per_run_min": per_run_min,
            "per_run_max": per_run_max,
            "rotation_weight": 1,
        },
    ]


class CommentConfigTests(unittest.TestCase):
    def write_config(self, root: Path, commenter: dict[str, object]) -> Path:
        source = root / "source.db"
        source.touch()
        payload = {**BASE_CONFIG, "commenter": commenter}
        path = root / "config.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_loads_comment_contract_with_safe_disabled_default(self) -> None:
        with TemporaryDirectory() as tmp:
            path = self.write_config(
                Path(tmp),
                {
                    "enabled": False,
                    "profiles": comment_profiles(with_vests=False),
                    "schedule": {
                        "active_start": "08:00",
                        "active_end": "23:00",
                        "interval_min_minutes": 90,
                        "interval_max_minutes": 150,
                        "daily_hard_cap": 72,
                        "check_every_minutes": 15,
                    },
                },
            )

            config = load_config(path)

            self.assertFalse(config.commenter.enabled)
            self.assertEqual(
                [profile["id"] for profile in config.commenter.profiles],
                ["observer", "helper", "counterpoint"],
            )
            self.assertEqual(config.commenter.active_start, "08:00")
            self.assertEqual(config.commenter.active_end, "23:00")
            self.assertEqual(config.commenter.interval_min_minutes, 90)
            self.assertEqual(config.commenter.interval_max_minutes, 150)
            self.assertEqual(config.commenter.daily_hard_cap, 72)
            self.assertEqual(config.commenter.check_every_minutes, 15)
            self.assertEqual(config.commenter.fetch_max_items, 30)
            self.assertFalse(config.commenter.research_enabled)
            self.assertEqual(config.commenter.research_max_posts, 3)
            self.assertFalse(config.commenter.history_patrol_enabled)
            self.assertFalse(config.commenter.history_reply_enabled)
            self.assertEqual(config.commenter.publish_min_interval_seconds, 31)

    def test_enabled_commenter_requires_three_unique_vest_names(self) -> None:
        with TemporaryDirectory() as tmp:
            path = self.write_config(
                Path(tmp),
                {
                    "enabled": True,
                    "profiles": comment_profiles(with_vests=False),
                    "schedule": {},
                },
            )

            with self.assertRaisesRegex(ConfigError, "vest_name"):
                load_config(path)

    def test_rejects_schedule_that_violates_execution_plan(self) -> None:
        with TemporaryDirectory() as tmp:
            path = self.write_config(
                Path(tmp),
                {
                    "enabled": False,
                    "profiles": comment_profiles(with_vests=False),
                    "schedule": {"daily_hard_cap": 73},
                },
            )

            with self.assertRaisesRegex(ConfigError, "daily_hard_cap"):
                load_config(path)

    def test_rejects_comment_fetch_limit_above_first_page_cap(self) -> None:
        with TemporaryDirectory() as tmp:
            path = self.write_config(
                Path(tmp),
                {
                    "enabled": False,
                    "profiles": comment_profiles(with_vests=False),
                    "schedule": {},
                    "selection": {"fetch_max_items": 31},
                },
            )

            with self.assertRaisesRegex(ConfigError, "fetch_max_items"):
                load_config(path)

    def test_loads_and_caps_news_research_configuration(self) -> None:
        with TemporaryDirectory() as tmp:
            path = self.write_config(
                Path(tmp),
                {
                    "enabled": False,
                    "profiles": comment_profiles(with_vests=False),
                    "schedule": {},
                    "research": {"enabled": True, "max_posts_per_round": 3},
                },
            )
            config = load_config(path)
            self.assertTrue(config.commenter.research_enabled)
            self.assertEqual(config.commenter.research_max_posts, 3)

            path = self.write_config(
                Path(tmp),
                {
                    "enabled": False,
                    "profiles": comment_profiles(with_vests=False),
                    "schedule": {},
                    "research": {"enabled": True, "max_posts_per_round": 4},
                },
            )
            with self.assertRaisesRegex(ConfigError, "max_posts_per_round"):
                load_config(path)

    def test_loads_and_caps_history_patrol(self) -> None:
        with TemporaryDirectory() as tmp:
            path = self.write_config(
                Path(tmp),
                {
                    "enabled": False,
                    "profiles": comment_profiles(with_vests=False),
                    "schedule": {},
                    "history_patrol": {
                        "enabled": True,
                        "lookback_days": 14,
                        "pages_per_round": 6,
                        "new_posts_per_round": 18,
                        "reply_enabled": True,
                        "reply_comments_per_round": 18,
                    },
                },
            )
            config = load_config(path)
            self.assertTrue(config.commenter.history_patrol_enabled)
            self.assertEqual(config.commenter.history_lookback_days, 14)
            self.assertEqual(config.commenter.history_pages_per_round, 6)
            self.assertEqual(config.commenter.history_new_posts_per_round, 18)
            self.assertTrue(config.commenter.history_reply_enabled)
            self.assertEqual(config.commenter.history_reply_comments_per_round, 18)

            payload = json.loads(path.read_text())
            payload["commenter"]["history_patrol"]["reply_comments_per_round"] = 19
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ConfigError, "reply_comments_per_round"):
                load_config(path)

    def test_all_profiles_mode_requires_exactly_six_per_profile(self) -> None:
        with TemporaryDirectory() as tmp:
            path = self.write_config(
                Path(tmp),
                {
                    "enabled": True,
                    "all_profiles_each_round": True,
                    "profiles": comment_profiles(with_vests=True, per_run_max=6),
                    "schedule": {},
                },
            )
            self.assertTrue(load_config(path).commenter.all_profiles_each_round)

            path = self.write_config(
                Path(tmp),
                {
                    "enabled": True,
                    "all_profiles_each_round": True,
                    "profiles": comment_profiles(with_vests=True, per_run_max=9),
                    "schedule": {},
                },
            )
            with self.assertRaisesRegex(ConfigError, "exactly 6"):
                load_config(path)

    def test_all_profiles_mode_allows_zero_to_three_instead_of_forcing_quota(self) -> None:
        with TemporaryDirectory() as tmp:
            path = self.write_config(
                Path(tmp),
                {
                    "enabled": True,
                    "all_profiles_each_round": True,
                    "profiles": comment_profiles(
                        with_vests=True, per_run_min=0, per_run_max=3
                    ),
                    "schedule": {"daily_hard_cap": 24},
                },
            )

            config = load_config(path)

            self.assertEqual(config.commenter.profiles[0]["per_run_min"], 0)
            self.assertEqual(config.commenter.profiles[0]["per_run_max"], 3)
            self.assertEqual(config.commenter.daily_hard_cap, 24)

    def test_rejects_publish_interval_below_platform_limit(self) -> None:
        with TemporaryDirectory() as tmp:
            path = self.write_config(
                Path(tmp),
                {
                    "enabled": False,
                    "profiles": comment_profiles(with_vests=False),
                    "schedule": {},
                    "publish": {"min_comment_interval_seconds": 29},
                },
            )

            with self.assertRaisesRegex(ConfigError, "min_comment_interval_seconds"):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
