from __future__ import annotations

from datetime import datetime
import hashlib
import json
from typing import Any


IMMUTABLE_GATES = (
    "fact_gate", "risk_gate", "rights_gate", "review_gate", "human_confirmation_gate"
)


def build_evolution_dry_run(
    reviews: list[dict[str, Any]],
    *,
    current_weights: dict[str, float],
    now: datetime,
) -> dict[str, Any]:
    eligible = [
        item for item in reviews
        if item.get("checkpoint") == "24h"
        and item.get("status") == "COMPLETED"
        and item.get("metrics", {}).get("operator_exclusion_status") == "PASS"
        and isinstance(item.get("metrics", {}).get("non_vest_reply_count"), int)
    ]
    canonical = json.dumps(current_weights, sort_keys=True, separators=(",", ":"))
    current_version = hashlib.sha256(canonical.encode()).hexdigest()[:12]
    result = {
        "schema_version": "dayibin-evolution-dry-run-v1",
        "generated_at": now.isoformat(),
        "status": "DRY_RUN_READY" if eligible else "FUTURE_GATED",
        "eligible_24h_sample_count": len(eligible),
        "current_version": current_version,
        "proposed_version": f"dry-run-{now:%Y%m%d%H%M}",
        "max_abs_delta": 0.05,
        "proposed_weights": dict(current_weights),
        "changes": [],
        "immutable_gates": list(IMMUTABLE_GATES),
        "auto_write": False,
        "rollback": {"version": current_version, "weights": dict(current_weights)},
    }
    if not eligible:
        result["reason"] = "真实24小时自然互动尚未到齐或运营账号剔除未通过"
        return result
    best = max(
        eligible,
        key=lambda item: int(item["metrics"]["non_vest_reply_count"]),
    )
    key = str(best.get("metadata", {}).get("persona") or "")
    if key and key in current_weights:
        old = float(current_weights[key])
        new = round(min(2.0, old + 0.05), 4)
        result["proposed_weights"][key] = new
        result["changes"] = [{"key": key, "old": old, "new": new, "delta": round(new - old, 4),
                              "reason": "24小时非运营账号回复数在合格样本中最高"}]
    return result
