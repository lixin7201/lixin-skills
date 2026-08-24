import unittest

from dayibin_auto_publisher.openclaw import AgentError, parse_agent_json


class OpenClawTests(unittest.TestCase):
    def test_parse_agent_json_extracts_fenced_payload_from_cli_envelope(self) -> None:
        stdout = """{
          "result": {
            "payloads": [
              {"text": "完成。\\n```json\\n{\\\"selected\\\":[{\\\"item_id\\\":\\\"a\\\"}]}\\n```"}
            ]
          }
        }"""

        parsed = parse_agent_json(stdout)

        self.assertEqual(parsed, {"selected": [{"item_id": "a"}]})

    def test_parse_agent_json_rejects_output_without_json_object(self) -> None:
        with self.assertRaisesRegex(AgentError, "JSON object"):
            parse_agent_json('{"result":{"payloads":[{"text":"没有结构化结果"}]}}')

    def test_parse_agent_json_reports_llm_failure_even_when_cli_status_is_ok(self) -> None:
        stdout = """{
          "status": "ok",
          "result": {
            "payloads": [{"text": "LLM request failed."}],
            "meta": {"stopReason": "error"}
          }
        }"""

        with self.assertRaisesRegex(AgentError, "LLM request failed"):
            parse_agent_json(stdout)


if __name__ == "__main__":
    unittest.main()
