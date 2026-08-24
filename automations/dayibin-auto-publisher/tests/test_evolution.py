from datetime import UTC, datetime
import unittest

from dayibin_auto_publisher.evolution import build_evolution_dry_run


class EvolutionTests(unittest.TestCase):
    def test_missing_natural_24h_metrics_stays_future_gated_and_never_writes(self) -> None:
        result = build_evolution_dry_run(
            [], current_weights={"城市观察室型": 1.0},
            now=datetime(2026, 8, 23, 14, 0, tzinfo=UTC),
        )

        self.assertEqual(result["status"], "FUTURE_GATED")
        self.assertFalse(result["auto_write"])
        self.assertEqual(result["changes"], [])
        self.assertIn("rights_gate", result["immutable_gates"])

    def test_eligible_dry_run_caps_non_safety_weight_change_and_keeps_rollback(self) -> None:
        result = build_evolution_dry_run(
            [{"checkpoint": "24h", "status": "COMPLETED", "metadata": {"persona": "城市观察室型"},
              "metrics": {"operator_exclusion_status": "PASS", "non_vest_reply_count": 8}}],
            current_weights={"城市观察室型": 1.0},
            now=datetime(2026, 8, 24, 14, 0, tzinfo=UTC),
        )

        self.assertEqual(result["status"], "DRY_RUN_READY")
        self.assertEqual(result["changes"][0]["delta"], 0.05)
        self.assertEqual(result["rollback"]["weights"], {"城市观察室型": 1.0})
        self.assertFalse(result["auto_write"])


if __name__ == "__main__":
    unittest.main()
