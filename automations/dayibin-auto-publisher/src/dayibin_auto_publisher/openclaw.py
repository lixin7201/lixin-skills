from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any


class AgentError(RuntimeError):
    pass


class AgentClient:
    def __init__(
        self,
        *,
        executable: str,
        agent_id: str,
        model: str,
        timeout_seconds: int,
    ) -> None:
        self.executable = executable
        self.agent_id = agent_id
        self.model = model
        self.timeout_seconds = timeout_seconds

    def run_json(self, prompt: str, *, session_id: str) -> dict[str, Any]:
        with tempfile.TemporaryDirectory(prefix="dayibin-agent-") as tmp:
            prompt_path = Path(tmp) / "prompt.txt"
            prompt_path.write_text(prompt, encoding="utf-8")
            argv = [
                self.executable,
                "agent",
                "--agent",
                self.agent_id,
                "--model",
                self.model,
                "--message-file",
                str(prompt_path),
                "--session-id",
                session_id,
                "--thinking",
                "off",
                "--timeout",
                str(self.timeout_seconds),
                "--json",
            ]
            try:
                result = subprocess.run(
                    argv,
                    capture_output=True,
                    text=True,
                    shell=False,
                    timeout=self.timeout_seconds + 30,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as error:
                raise AgentError(f"OpenClaw could not run: {_redact(str(error))}") from error
        if result.returncode != 0:
            detail = _redact((result.stderr or result.stdout or "").strip())
            raise AgentError(f"OpenClaw exited with {result.returncode}: {detail[:500]}")
        return parse_agent_json(result.stdout)


def parse_agent_json(stdout: str) -> dict[str, Any]:
    candidates: list[str] = []
    try:
        envelope = json.loads(stdout)
    except json.JSONDecodeError:
        envelope = None
    if isinstance(envelope, dict):
        _collect_text_candidates(envelope, candidates)
        result = envelope.get("result")
        if isinstance(result, dict):
            meta = result.get("meta")
            failed = isinstance(meta, dict) and (
                meta.get("stopReason") == "error"
                or meta.get("livenessState") == "blocked"
            )
            failure_text = next(
                (
                    text
                    for text in reversed(candidates)
                    if "request failed" in text.lower()
                    or "turn failed" in text.lower()
                ),
                None,
            )
            if failed or failure_text:
                raise AgentError(
                    f"OpenClaw agent failed: {_redact(failure_text or 'stopReason=error')}"
                )
    candidates.append(stdout)
    for candidate in reversed(candidates):
        decoded = _decode_object(candidate)
        if decoded is not None and not _looks_like_cli_envelope(decoded):
            return decoded
    raise AgentError("agent response did not contain a JSON object")


def _collect_text_candidates(value: Any, output: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"text", "content", "message", "reply", "response", "output"} and isinstance(child, str):
                output.append(child)
            else:
                _collect_text_candidates(child, output)
    elif isinstance(value, list):
        for child in value:
            _collect_text_candidates(child, output)


def _decode_object(text: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    stripped = text.strip()
    try:
        direct = json.loads(stripped)
    except json.JSONDecodeError:
        direct = None
    if isinstance(direct, dict):
        return direct
    for match in re.finditer(r"\{", stripped):
        try:
            value, _end = decoder.raw_decode(stripped[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def _looks_like_cli_envelope(value: dict[str, Any]) -> bool:
    return "result" in value and not any(
        key in value for key in ("selected", "drafts", "publish_results", "tid")
    )


def _redact(value: str) -> str:
    value = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", value)
    value = re.sub(r"\bsk-[A-Za-z0-9_-]{8,}\b", "sk-[REDACTED]", value)
    value = re.sub(
        r'(?i)("?(?:token|password|secret|api[_-]?key)"?\s*[:=]\s*")[^"]+"',
        r'\1[REDACTED]"',
        value,
    )
    return value
