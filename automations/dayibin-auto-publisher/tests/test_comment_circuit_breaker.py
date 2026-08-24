from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from dayibin_auto_publisher.comment_dispatcher import CommentDispatchError, dispatch_comments
from dayibin_auto_publisher.openclaw import AgentError
from tests.test_comment_schedule import FlowAgent, NOW, StaticRng, _config


class AuthFailAgent(FlowAgent):
    def run_json(self, prompt: str, *, session_id: str) -> dict[str, object]:
        if "/review/vest-reply/add" in prompt:
            raise AgentError("HTTP 401 invalid credentials")
        return super().run_json(prompt, session_id=session_id)


class CommentCircuitBreakerTests(unittest.TestCase):
    def test_auth_failure_opens_global_circuit_and_preserves_report(self) -> None:
        with TemporaryDirectory() as tmp:
            config = _config(Path(tmp), enabled=True)

            with self.assertRaisesRegex(CommentDispatchError, "401"):
                dispatch_comments(
                    config,
                    AuthFailAgent(),
                    now=NOW,
                    send=True,
                    force=True,
                    rng=StaticRng(),
                    sleeper=lambda _seconds: None,
                )

            state = json.loads((config.data_dir / "commenter-state.json").read_text())
            report = json.loads(
                (config.data_dir / "2026-08-19" / "comments" / "run-report.json").read_text()
            )
            self.assertTrue(state["circuit_open"])
            self.assertEqual(state["circuit_reason"], "AUTH_FAILURE")
            self.assertEqual(report["status"], "CIRCUIT_OPEN")
            self.assertEqual(report["published_count"], 0)


if __name__ == "__main__":
    unittest.main()
