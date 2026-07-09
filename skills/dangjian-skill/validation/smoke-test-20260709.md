# Smoke Test 2026-07-09

- `openclaw skills info dangjian-skill --agent main`: Ready, visible to model, available as command.
- `openclaw agent --local --agent main /dangjian-skill ...`: loaded skill and produced leader-publicity brief.
- Tool summary in native run: failures = 0.
- Note: omitting `--agent main` routed to `workspace-default`, where the skill was not loaded; use main agent for validation and normal OpenClaw workspace use.
