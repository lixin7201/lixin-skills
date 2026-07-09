# Smoke Test 2026-07-09

## Discoverability

- `openclaw skills info 36kr-skill --agent main`: PASS
- Status: `36kr-skill ✓ Ready`
- Source: `openclaw-workspace`
- Path: `~/.openclaw/workspace/skills/36kr-skill/SKILL.md`
- Visible to model: yes
- Available as command: yes

## Fleet Check

- `openclaw skills check --agent main --json`: PASS
- `36kr-skill` in `eligible`: true
- `36kr-skill` in `modelVisible`: true
- `36kr-skill` in `commandVisible`: true

## Real Agent Smoke

Command:

```text
openclaw agent --local --agent main --json --timeout 180 --message '/36kr-skill 按36氪最前线写一个短稿...'
```

Result: PASS. The main agent loaded `36kr-skill`, routed the task as `最前线/快讯分析`, produced title options, a short 36氪-style draft, and a `待核实` list.

Safety check: PASS. The output did not invent a company name, price, customer, integration partner, source, or deployment detail. It kept unconfirmed items in `待核实`.

Runtime note: OpenClaw emitted unrelated legacy state/plugin warnings and symlink-skip warnings for other skills; no `36kr-skill` failure appeared.
