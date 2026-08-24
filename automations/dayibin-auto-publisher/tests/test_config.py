import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from dayibin_auto_publisher.config import ConfigError, load_config


class ConfigTests(unittest.TestCase):
    def test_load_config_resolves_relative_data_directory(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "source_db": "/tmp/radar.db",
                        "data_dir": "data",
                        "agent": {
                            "id": "hotspot-writer",
                            "model": "easyai/gpt-5.5",
                        },
                    }
                ),
                encoding="utf-8",
            )

            config = load_config(config_path)

            self.assertEqual(config.source_db, Path("/tmp/radar.db"))
            self.assertEqual(config.data_dir, (root / "data").resolve())
            self.assertEqual(config.agent_id, "hotspot-writer")
            self.assertEqual(config.model, "easyai/gpt-5.5")
            self.assertFalse(config.publish_enabled)

    def test_load_config_rejects_missing_source_database(self) -> None:
        with TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "data_dir": "data",
                        "agent": {
                            "id": "hotspot-writer",
                            "model": "easyai/gpt-5.5",
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ConfigError, "source_db"):
                load_config(config_path)

    def test_loads_production_scale_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "source_db": "/tmp/radar.db",
                        "data_dir": "data",
                        "agent": {"id": "writer", "model": "openai/gpt-5.5"},
                        "production": {
                            "daily_soft_target": 10,
                            "daily_regular_min": 8,
                            "daily_regular_max": 12,
                            "daily_hard_cap": 15,
                            "max_pending_batches": 5,
                            "batch_max_items": 3,
                            "active_start": "08:20",
                            "active_end": "22:30",
                            "global_interval_min_minutes": 45,
                            "global_interval_max_minutes": 120,
                            "same_vest_interval_minutes": 150,
                            "dispatcher_check_minutes": 5,
                        },
                    }
                ),
                encoding="utf-8",
            )

            config = load_config(config_path)

            self.assertEqual((config.production.daily_regular_min, config.production.daily_soft_target, config.production.daily_regular_max), (8, 10, 12))
            self.assertEqual(config.production.daily_hard_cap, 15)
            self.assertEqual(config.production.dispatcher_check_minutes, 5)


if __name__ == "__main__":
    unittest.main()
