from __future__ import annotations

import argparse
from datetime import UTC, date, datetime
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

from .batch_publish import BatchPublishError, publish_batch, publish_scheduled_item
from .collector import CollectorError, SnapshotOptions, collect_snapshot
from .comment_dispatcher import (
    CommentDispatchError,
    _all_operator_vest_ids,
    dispatch_comments,
    reset_comment_circuit,
)
from .config import ConfigError, load_config
from .openclaw import AgentClient, AgentError
from .pipeline import PipelineError, run_day
from .publish import PublishError
from .post_publish_review import dispatch_due_reviews, qianfan_reply_metrics_fetcher
from .production_schedule import (
    ProductionScheduleError,
    build_daily_operations_review,
    confirm_batch_schedule,
    dispatch_due_publications,
)
from .qianfan import QianfanClient, QianfanError
from .rising_dispatch import (
    RisingDispatchError,
    dispatch_rising,
    regenerate_quality_incident_batch,
    reset_rising_circuit,
)
from .storage import read_json
from .traffic_patrol import (
    TrafficPatrolError,
    TrafficPublishPreflightError,
    live_traffic_source_fetchers,
    run_public_service_branches,
    run_traffic_patrol,
    traffic_publish_plan,
    traffic_publish_prompt,
    validate_traffic_preflight,
    validate_traffic_publish_response,
)
from .weather_shadow import (
    WeatherPublishPreflightError,
    WeatherShadowError,
    live_source_fetchers,
    run_weather_shadow,
    validate_weather_publish_response,
    validate_weather_preflight,
    weather_publish_plan,
    weather_publish_prompt,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dayibin_auto_publisher")
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot_parser = subparsers.add_parser("snapshot", help="save today's hotspot snapshot")
    snapshot_parser.add_argument("--config", required=True)
    snapshot_parser.add_argument("--refresh", action="store_true")

    run_parser = subparsers.add_parser("run", help="run selection, drafting and optional publish")
    run_parser.add_argument("--config", required=True)
    run_parser.add_argument("--publish", action="store_true")
    run_parser.add_argument("--limit", type=int)
    run_parser.add_argument("--selection-limit", type=int)

    comment_parser = subparsers.add_parser(
        "comment-dispatch", help="run the APP auto-comment dispatcher"
    )
    comment_parser.add_argument("--config", required=True)
    comment_parser.add_argument("--send", action="store_true")
    comment_parser.add_argument("--force", action="store_true")
    comment_parser.add_argument("--limit", type=int)

    reset_parser = subparsers.add_parser(
        "comment-reset-circuit", help="reset the stopped comment dispatcher after review"
    )
    reset_parser.add_argument("--config", required=True)
    reset_parser.add_argument("--confirm", action="store_true")

    rising_parser = subparsers.add_parser(
        "rising-dispatch", help="run one idempotent T0 rising-monitor round"
    )
    rising_parser.add_argument("--config", required=True)
    rising_parser.add_argument("--evidence-dir")
    rising_parser.add_argument("--daily-pool", action="store_true")
    rising_parser.add_argument("--reuse-latest", action="store_true")
    rising_parser.add_argument("--collect-only", action="store_true")

    rising_reset_parser = subparsers.add_parser(
        "rising-reset-circuit", help="reset the stopped T0 dispatcher after review"
    )
    rising_reset_parser.add_argument("--config", required=True)
    rising_reset_parser.add_argument("--evidence-dir", required=True)
    rising_reset_parser.add_argument("--confirm", action="store_true")

    quality_parser = subparsers.add_parser(
        "quality-reroute", help="rewrite a paused quality-incident batch without publishing"
    )
    quality_parser.add_argument("--config", required=True)
    quality_parser.add_argument("--batch-id", required=True)

    review_parser = subparsers.add_parser(
        "post-publish-review-dispatch", help="process due post-publication reviews"
    )
    review_parser.add_argument("--config", required=True)
    review_parser.add_argument("--queue", required=True)
    review_parser.add_argument("--max-items", type=int, default=10)

    batch_publish_parser = subparsers.add_parser(
        "batch-publish", help="preflight or publish one confirmed DAILY_VALUE batch"
    )
    batch_publish_parser.add_argument("--config", required=True)
    batch_publish_parser.add_argument("--batch-id", required=True)
    batch_publish_parser.add_argument("--confirmation-phrase", required=True)
    batch_mode = batch_publish_parser.add_mutually_exclusive_group()
    batch_mode.add_argument("--dry-run", action="store_true")
    batch_mode.add_argument("--no-send", action="store_true")

    schedule_parser = subparsers.add_parser(
        "schedule-batch", help="confirm one batch into the persistent random schedule"
    )
    schedule_parser.add_argument("--config", required=True)
    schedule_parser.add_argument("--batch-id", required=True)
    schedule_parser.add_argument("--confirmation-phrase", required=True)

    publish_dispatch_parser = subparsers.add_parser(
        "publish-dispatch", help="process at most one due scheduled draft"
    )
    publish_dispatch_parser.add_argument("--config", required=True)
    publish_dispatch_parser.add_argument("--queue")
    publish_dispatch_parser.add_argument("--no-send", action="store_true")

    daily_review_parser = subparsers.add_parser(
        "daily-operations-review", help="write the deterministic daily operations review card"
    )
    daily_review_parser.add_argument("--config", required=True)
    daily_review_parser.add_argument("--business-date")

    weather_parser = subparsers.add_parser(
        "weather-shadow", help="monitor official Yibin warnings with an explicit publish mode"
    )
    weather_parser.add_argument("--config", required=True)
    weather_mode = weather_parser.add_mutually_exclusive_group(required=True)
    weather_mode.add_argument("--no-publish", action="store_true")
    weather_mode.add_argument("--publish", action="store_true")

    traffic_parser = subparsers.add_parser(
        "traffic-patrol", help="monitor official Yibin traffic disruptions"
    )
    traffic_parser.add_argument("--config", required=True)
    traffic_mode = traffic_parser.add_mutually_exclusive_group(required=True)
    traffic_mode.add_argument("--no-publish", action="store_true")
    traffic_mode.add_argument("--publish", action="store_true")

    public_service_parser = subparsers.add_parser(
        "public-service-patrol", help="run isolated weather and traffic patrol branches"
    )
    public_service_parser.add_argument("--config", required=True)
    public_service_mode = public_service_parser.add_mutually_exclusive_group(required=True)
    public_service_mode.add_argument("--no-publish", action="store_true")
    public_service_mode.add_argument("--publish", action="store_true")

    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        now = datetime.now(UTC)
        business_date = now.astimezone(ZoneInfo("Asia/Shanghai")).date()
        day_dir = config.data_dir / business_date.isoformat()
        if args.command == "snapshot":
            target = day_dir / "hotspots.json"
            if target.exists() and not args.refresh:
                snapshot = read_json(target)
            else:
                snapshot = collect_snapshot(
                    config.source_db,
                    target,
                    SnapshotOptions(
                        lookback_hours=config.lookback_hours,
                        min_body_chars=config.min_body_chars,
                        max_items=config.snapshot_limit,
                    ),
                    now=now,
                )
            result = {
                "status": "snapshot_ready",
                "business_date": business_date.isoformat(),
                "item_count": int(snapshot.get("item_count", 0)),
                "generated_at": snapshot.get("generated_at"),
                "path": str(target),
            }
        elif args.command == "run":
            if args.limit is not None and args.limit < 1:
                parser.error("--limit must be positive")
            if args.selection_limit is not None and args.selection_limit < 1:
                parser.error("--selection-limit must be positive")
            agent = AgentClient(
                executable=config.openclaw_bin,
                agent_id=config.agent_id,
                model=config.model,
                timeout_seconds=config.agent_timeout_seconds,
            )
            result = run_day(
                config,
                agent,
                business_date=business_date,
                now=now,
                publish=args.publish,
                publish_limit=args.limit,
                selection_limit=args.selection_limit,
            )
        elif args.command == "comment-dispatch":
            agent = AgentClient(
                executable=config.openclaw_bin,
                agent_id=config.agent_id,
                model=config.model,
                timeout_seconds=config.agent_timeout_seconds,
            )
            result = dispatch_comments(
                config,
                agent,
                now=now,
                send=args.send,
                force=args.force,
                max_comments=args.limit,
                post_source=QianfanClient.from_config(),
            )
        elif args.command == "comment-reset-circuit":
            if not args.confirm:
                raise CommentDispatchError(
                    "comment-reset-circuit requires --confirm after incident review"
                )
            result = reset_comment_circuit(config)
        elif args.command == "rising-dispatch":
            agent = None if args.collect_only else AgentClient(
                executable=config.openclaw_bin,
                agent_id=config.agent_id,
                model=config.model,
                timeout_seconds=config.agent_timeout_seconds,
            )
            result = dispatch_rising(
                config,
                evidence_dir=args.evidence_dir,
                now=now,
                agent=agent,
                daily_pool=args.daily_pool,
                reuse_latest=args.reuse_latest,
                collect_only=args.collect_only,
            )
        elif args.command == "rising-reset-circuit":
            if not args.confirm:
                parser.error("rising-reset-circuit requires --confirm after incident review")
            result = reset_rising_circuit(args.evidence_dir)
        elif args.command == "quality-reroute":
            agent = AgentClient(
                executable=config.openclaw_bin,
                agent_id=config.agent_id,
                model=config.model,
                timeout_seconds=config.agent_timeout_seconds,
            )
            result = regenerate_quality_incident_batch(
                config,
                source_batch_id=args.batch_id,
                agent=agent,
                now=now,
            )
        elif args.command == "post-publish-review-dispatch":
            if args.max_items < 1 or args.max_items > 10:
                parser.error("--max-items must be between 1 and 10")
            client = QianfanClient.from_config()
            try:
                operator_vest_ids = (
                    client.resolve_enabled_vest_ids({
                        str(profile.get("vest_name") or "").strip()
                        for profile in config.profiles
                        if str(profile.get("vest_name") or "").strip()
                    })
                    | {
                        str(profile.get("vest_id") or "").strip()
                        for profile in config.commenter.profiles
                        if str(profile.get("vest_id") or "").strip()
                    }
                    | _all_operator_vest_ids(config.data_dir)
                )
            except QianfanError:
                operator_vest_ids = None
            result = dispatch_due_reviews(
                args.queue,
                now=now,
                metrics_fetcher=qianfan_reply_metrics_fetcher(
                    client, now=now, operator_vest_ids=operator_vest_ids
                ),
                max_items=args.max_items,
            )
        elif args.command == "batch-publish":
            agent = None if args.dry_run or args.no_send else AgentClient(
                executable=config.openclaw_bin,
                agent_id=config.agent_id,
                model=config.model,
                timeout_seconds=config.agent_timeout_seconds,
            )
            preflight_client = None if args.dry_run else QianfanClient.from_config()
            result = publish_batch(
                config,
                batch_id=args.batch_id,
                confirmation_phrase=args.confirmation_phrase,
                agent=agent,
                dry_run=args.dry_run,
                no_send=args.no_send,
                now=now,
                preflight_resolver=(
                    preflight_client.preflight_publish_targets
                    if preflight_client is not None
                    else None
                ),
                published_metadata_resolver=(
                    preflight_client.fetch_published_thread_metadata
                    if preflight_client is not None and not args.no_send
                    else None
                ),
            )
        elif args.command == "schedule-batch":
            result = confirm_batch_schedule(
                config.data_dir,
                batch_id=args.batch_id,
                confirmation_phrase=args.confirmation_phrase,
                now=now,
                settings=config.production,
                daily_hard_cap=config.production.daily_hard_cap,
            )
        elif args.command == "publish-dispatch":
            client = QianfanClient.from_config()
            publish_agent = None if args.no_send else AgentClient(
                executable=config.openclaw_bin,
                agent_id=config.agent_id,
                model=config.model,
                timeout_seconds=config.agent_timeout_seconds,
            )

            def scheduled_publisher(item: dict[str, object], no_send: bool) -> dict[str, object]:
                return publish_scheduled_item(
                    config,
                    batch_id=str(item["batch_id"]),
                    content_id=str(item["content_id"]),
                    agent=publish_agent,
                    no_send=no_send,
                    now=now,
                    preflight_resolver=client.preflight_publish_targets,
                    published_metadata_resolver=(
                        None if no_send else client.fetch_published_thread_metadata
                    ),
                )

            result = dispatch_due_publications(
                args.queue or config.data_dir / "production-publish-queue.json",
                now=now,
                no_send=args.no_send,
                publisher=scheduled_publisher,
            )
        elif args.command in {"weather-shadow", "traffic-patrol", "public-service-patrol"}:
            agent = AgentClient(
                executable=config.openclaw_bin,
                agent_id=config.agent_id,
                model=config.model,
                timeout_seconds=config.agent_timeout_seconds,
            )
            client = QianfanClient.from_config() if args.publish else None
            weather_publisher = None
            if args.publish:
                assert client is not None

                def weather_publisher(card: dict[str, object]) -> dict[str, object]:
                    plan = weather_publish_plan(card)
                    identifier = str(plan["content_id"])
                    try:
                        preflight = validate_weather_preflight(
                            client.preflight_publish_targets([plan]), identifier
                        )
                    except QianfanError as error:
                        raise WeatherPublishPreflightError(str(error)) from error
                    response = agent.run_json(
                        weather_publish_prompt(card, preflight),
                        session_id=f"weather-publish-{identifier}",
                    )
                    item = response.get("publish_result")
                    tid = str(item.get("tid") or "") if isinstance(item, dict) else ""
                    metadata = (
                        client.fetch_published_thread_metadata({tid}).get(tid) if tid else None
                    )
                    return validate_weather_publish_response(
                        response, card, preflight, metadata
                    )

            traffic_publisher = None
            if args.publish:
                assert client is not None

                def traffic_publisher(card: dict[str, object]) -> dict[str, object]:
                    plan = traffic_publish_plan(card)
                    identifier = str(plan["content_id"])
                    try:
                        preflight = validate_traffic_preflight(
                            client.preflight_publish_targets([plan]), identifier
                        )
                    except QianfanError as error:
                        raise TrafficPublishPreflightError(str(error)) from error
                    response = agent.run_json(
                        traffic_publish_prompt(card, preflight),
                        session_id=f"traffic-publish-{identifier.replace(':', '-')}",
                    )
                    item = response.get("publish_result")
                    tid = str(item.get("tid") or "") if isinstance(item, dict) else ""
                    metadata = (
                        client.fetch_published_thread_metadata({tid}).get(tid) if tid else None
                    )
                    return validate_traffic_publish_response(
                        response, card, preflight, metadata
                    )

            draft_runner = lambda prompt, session_id: agent.run_json(
                prompt, session_id=session_id
            )

            def weather_branch() -> dict[str, object]:
                return run_weather_shadow(
                    data_dir=config.data_dir / "public-service-weather-shadow",
                    now=now,
                    source_fetchers=live_source_fetchers(),
                    draft_runner=draft_runner,
                    publish=args.publish,
                    publisher=weather_publisher,
                )

            def traffic_branch() -> dict[str, object]:
                return run_traffic_patrol(
                    data_dir=config.data_dir / "public-service-traffic-patrol",
                    now=now,
                    source_fetchers=live_traffic_source_fetchers(),
                    draft_runner=draft_runner,
                    publish=args.publish,
                    publisher=traffic_publisher,
                )

            if args.command == "weather-shadow":
                result = weather_branch()
            elif args.command == "traffic-patrol":
                result = traffic_branch()
            else:
                result = run_public_service_branches({
                    "weather": weather_branch,
                    "traffic": traffic_branch,
                })
        else:
            requested_day = args.business_date or business_date.isoformat()
            try:
                date.fromisoformat(requested_day)
            except ValueError as error:
                parser.error(f"--business-date must be ISO YYYY-MM-DD: {error}")
            result = build_daily_operations_review(
                config.data_dir,
                business_date=requested_day,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (
        ConfigError,
        BatchPublishError,
        CollectorError,
        CommentDispatchError,
        AgentError,
        PipelineError,
        PublishError,
        ProductionScheduleError,
        QianfanError,
        RisingDispatchError,
        TrafficPatrolError,
        WeatherShadowError,
        ValueError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
