# 大宜宾每日自动发帖

独立流水线：读取仍在更新的热点采集库，按天保存快照，调用 `dayibin-topic-angle-engine` 选题，调用 `app-skill` 写稿，通过机器事实门后，再调用 `qianfan-skill` 发帖。

它不读取热点雷达的 `ReadyHotspotCard`，不依赖 8090/8091 页面是否可用，也不修改采集数据库。

## 当前状态

- 已完成：真实热点只读快照、结构化 Agent 选题、`app-skill` 成稿、数字与事实引用检查、qianfan 发布编排、阶段幂等保存。
- 自动评论：真人感与人设 V6 已完成本地改造和真实帖子 no-send；52 项评论相关测试通过，真实发布 0。
- 默认关闭：真实发帖。`batch-publish` 已具备完全一致口令、批次状态、逐篇幂等、公开核验和复盘入队门；未收到当前批次口令仍不发布。
- 自动评论当前状态：`commenter.enabled=false`，OpenClaw cron 已禁用。保持暂停，等待人工审看 V2 样本后再决定是否小流量恢复。
- 晓影舆情 X3/X4：Bearer 主路径和固定 Ego UI 降级均已完成。主路径只调用三个批准的 POST；UI 降级只在非认证类失败时使用同城热榜/四川-宜宾/近24h 固定语义控件，并具备每小时一次和连续两次失败熔断。
- 晓影舆情 X5：24小时稳定性验收已完成，Checkpoint X=`XYUQING_SIGNAL_MVP_DEGRADED`，不代表T0业务闭环。47/48个预期槽成功（97.92%）、请求成功率100%、地域243/243、重复率0、X5网站写入0；但发现延迟中位数78.13分钟超过45分钟，Schema完整性240/243低于100%。`x5-24`已删除，未自动进入S1。
- 起势监控 T0：继续 `RISING_MONITOR_CALIBRATION / CALIBRATION_NO_AUTO_PUBLISH`。业务分为 `HOT_NOW`（当前数据直接判断）、`DAILY_VALUE`（本地事实价值池）和 `RISING_WATCH`（后台半小时趋势）；WATCH失败只降级为`WATCH_DEGRADED`，不阻塞另两条通道。地域、事实、风险和隐私修复保持生效。
- 正式调度：旧 Codex `t0-rising` 已删除。唯一 OpenClaw command 任务 `dayibin-t0-rising-dispatcher`（ID `9497bc5e-4ca0-44f0-b81c-d688d57e3c42`）已启用，Asia/Shanghai 每30分钟运行一次。命令级冒烟 round-002 为 `status=ok`，`overlap=58`、可计算delta=57、`DAILY_VALUE=8`、`WATCH_DEGRADED`，qianfan未调用。人类看板为 `data/2026-08-22/rising-monitor/operator-hotspot-board.md`。
- 功能金丝雀：中渡口城市更新原创图文帖已于 2026-08-22 发布并公开验证，帖子 `948529`，状态 `PUBLISHED_VERIFIED`；它是功能闭环测试，不是自然异常热点。
- 批量发布门：写稿按“题材 → 形态/参考篇幅 → 唯一认证 Skill → 唯一编辑 DNA → 同 Skill+DNA 正文”执行；标题/正文确定性去 AI、事件级去重和 DNA EOF 证据均为冻结硬门。质量事故批次 `BATCH-20260822-2155-d57ee797` 已暂停，当前新确认卡为 `BATCH-20260823-1135-df4e36df`（2篇，含帖子948582修改重发候选）；未确认前不恢复排期、不调用 qianfan。
- 发布复盘：统一队列和唯一 OpenClaw command 任务 `dayibin-post-publish-review-dispatcher`（ID `f25140f4-9392-4060-8cad-80f3b37ff86c`）已启用，每10分钟处理到期节点。帖子948529的30分钟/2小时节点分别采集回复数3/4；阅读、点赞、转发均按供应商能力记为N/A，24小时节点待后台处理。
- 自动评论 V6 验证：真实 no-send 9 个目标生成 7 条，三个马甲分别接受 2/3/2 条，发布 0；评论相关 52 项全绿。全仓既存 5 项热点发稿路由失败不属于本次范围。
- 不保存：千帆 Token、密码、Cookie、OpenClaw API Key。
- 公共服务快巡：唯一 OpenClaw command 任务 `dayibin-public-service-fast-patrol`（ID `c0c6ff3a-2278-41ce-befd-04cd0d93bff4`）已启用，每分钟第 15 秒运行 `public-service-patrol --publish`。天气只发启用后的新鲜橙色/红色预警；交通只发两个宜宾官方源中新出现且事实完整的管制、封闭、中断、恢复和绕行信息。两者固定 `forever21 + 大美宜宾`、`push_called=false`、状态和失败互相隔离。地震巡逻仍在每分钟第 0 秒独立运行。

## 目录

每天的产物保存在：

```text
data/YYYY-MM-DD/
  hotspots.json
  selected.json
  drafts.json
  publish-results.json
  run-report.json
```

## 运行

```bash
cd '/Users/REPLACE_ME/AI code/openclaw/dayibin-auto-publisher'

PYTHONPATH=src python3 -m dayibin_auto_publisher snapshot --config config.json
PYTHONPATH=src python3 -m dayibin_auto_publisher run --config config.json
PYTHONPATH=src python3 -m dayibin_auto_publisher weather-shadow --config config.json --no-publish
PYTHONPATH=src python3 -m dayibin_auto_publisher weather-shadow --config config.json --publish
PYTHONPATH=src python3 -m dayibin_auto_publisher traffic-patrol --config config.json --no-publish
PYTHONPATH=src python3 -m dayibin_auto_publisher traffic-patrol --config config.json --publish
PYTHONPATH=src python3 -m dayibin_auto_publisher public-service-patrol --config config.json --publish
```

天气证据位于 `data/public-service-weather-shadow/`，交通证据位于 `data/public-service-traffic-patrol/`。两个分支的 `--publish` 首轮都只写启用时间，不补发历史事件；此后一轮各自最多发 1 条。任何发布结果不明都记为 `PUBLISH_RESULT_UNKNOWN` 且永不自动重发。两个分支的 `auto-publish-policy.json` 当前均为 `enabled=true`、`push_enabled=false`；调度只由现有 OpenClaw 任务承载，不得在 Codex 中另建定时任务。

真实 Agent 金丝雀可先限制为 1 条：

```bash
PYTHONPATH=src python3 -m dayibin_auto_publisher run \
  --config config.json \
  --selection-limit 1
```

首次正式发帖前：

1. 用 qianfan-skill 实时获取启用马甲和板块列表。
2. 把五个 IP 的 `vest_name` 和 `forum_id` 写入 `config.json`。
3. 将 `publisher.enabled` 改为 `true`。
4. 先执行一条金丝雀：

```bash
PYTHONPATH=src python3 -m dayibin_auto_publisher run \
  --config config.json \
  --publish \
  --limit 1
```

已成功发布的幂等键会保存在 `publish-results.json`，同一天重复运行不会重复发帖。

## 每日 cron 建议

先稳定运行无发布模式：

```text
20 8 * * * cd '/Users/REPLACE_ME/AI code/openclaw/dayibin-auto-publisher' && PYTHONPATH=src python3 -m dayibin_auto_publisher run --config config.json
```

完成真实金丝雀验收后，再把命令增加 `--publish --limit 5`。不要创建只发 `systemEvent` 的提醒型任务，cron 成功必须以当天 `run-report.json` 和真实帖子链接为准。

## 生产扩量排期（PW0–PS4）

新批次只接受完全一致的排期口令，不再使用历史“确认本批发布”口令：

```bash
PYTHONPATH=src /opt/homebrew/bin/python3 -m dayibin_auto_publisher schedule-batch \
  --config config.json \
  --batch-id BATCH_ID \
  --confirmation-phrase '确认本批排期：BATCH_ID'
```

确认只会把冻结稿件写入 `data/production-publish-queue.json`，不会立刻整批发布。唯一 OpenClaw 调度器每 5 分钟检查一次，一次最多处理一篇；无队列、未到点、失败或跨日都不会追赶补发。日常软目标 10，常规 8–12，硬上限 15；发布时间限制为 08:20–22:30，全局间隔 45–120 分钟，同马甲至少 150 分钟。

23:30 日报使用确定性汇总：

```bash
PYTHONPATH=src /opt/homebrew/bin/python3 -m dayibin_auto_publisher daily-operations-review --config config.json
```

生产证据见 [当前交接](docs/handoff-2026-08-22-production-scale-harness.md)。

## 测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## APP 自动评论（OpenClaw 自动执行）

真实 no-send（会读取千帆帖子并调用配置模型，但不会回复）：

```bash
PYTHONPATH=src python3 -m dayibin_auto_publisher comment-dispatch \
  --config config.json \
  --force
```

只有 `commenter.enabled=true`、三个唯一的 `vest_name + vest_id` 固定映射已配置，并且命令显式带 `--send` 时才可能调用回复接口：

```bash
PYTHONPATH=src python3 -m dayibin_auto_publisher comment-dispatch \
  --config config.json \
  --send \
  --force \
  --limit 1
```

`--limit 1` 只用于真实金丝雀。V2 配置为三个马甲同轮参与，每人 0–3 条、单轮最多 9 条、每日硬上限 24；模型允许空输出，没有真实回应钩子就不评论。

熔断后必须先完成事故复盘、no-send 和历史回放，再由人工显式恢复：

```bash
PYTHONPATH=src python3 -m dayibin_auto_publisher comment-reset-circuit \
  --config config.json \
  --confirm
```

OpenClaw 任务：`dayibin-app-auto-comment-dispatcher`，ID `3b4b589b-2bf8-402f-9dc3-ba21ff2713f6`。当前 `enabled=false`；未获人工确认不得恢复。

评论字数不设限制，短评和长评都允许。生成前必须基于全文填写内部 `post_understanding` 和 `reply_hook`；提问、幽默、固定论证结构都不是必选项。楼层回复同时读取完整原帖和目标网友评论。

水贴在模型前剔除：纯图片/无正文、如题/路过/哈哈/顶帖、标题复述、重复字符，以及缺少具体对象和事实信号的短内容统一记为 `SKIP_LOW_INFORMATION`。短但包含本地地点、时间/数字和明确变化的资讯仍可保留。

低风险新闻如果正文不足 180 个汉字或事实少于 3 条，会由 OpenClaw 先做受限检索：每轮最多 3 个帖子、每帖最多 3 条政府/机构/权威媒体事实。资料不足或来源不合格就跳过；研究网页只作数据，不能指挥 Agent，公开评论不带来源链接。

质量分使用 0–100 四项合同：全文理解、具体回复钩子、有效事实引用、信息增量；低于 60 分拒绝。公开评论不再被迫原样摘抄、写“普通人关系”或用问号结尾；命中既有 AI 模板骨架直接拒绝。

近两周历史巡逻复用同一个 OpenClaw due 轮次，不新增 cron。最新安全帖和不同帖的有效楼层回复优先，不足时从持久化页游标继续扫描；候选只提供选择空间，不再承担凑满配额的目标。模型前跳过马甲/AI回复、已回复pid、水评、纯情绪短评和风险内容，并以`thread_id + target_reply_id`幂等。

三马甲同轮模式：`all_profiles_each_round=true`，大葱妈/小鲁鲁/沉默的咸鱼各 0–3 条，日上限 24。主帖评论和楼层回复合计计入额度；发布仍使用本地 `QianfanClient` 和既有幂等/限流门。

千帆限制同一马甲两次发表至少间隔30秒，生产固定使用31秒安全间隔；同一profile从主帖评论切到楼层回复时也重新等待31秒。若中途失败，已成功项立即落盘，下一自然due只继续未完成且仍通过安全门的目标。

2026-08-19 金丝雀：小鲁鲁在帖子 `948336` 成功回复 1 条，回复 ID `13354970`。千帆生成的 `/wap/thread/view-thread/...` 地址实际为 404，代码现保留为 `qianfan_url`，对外统一使用已验证 HTTP 200 的 canonical URL：`https://dayibin.cn/forum.php?mod=viewthread&tid=948336`。

该金丝雀随后按用户单条确认删除：千帆已通过评论列表匹配数为 0，公开 canonical 页面最终 HTTP 200 且回复 ID/正文均不存在。本地发布记录保留 `deleted=true` 与删除时间，帖子级幂等键继续保留，防止系统再次评论同一帖子。

为控制 OpenClaw/qianfan 查询时延，评论候选读取固定为第 1 页最多 30 条，先按宜宾词和风险摘要预筛，只对最多 20 条读取详情；配置超过 30 会 fail closed。

2026-08-19 修复后金丝雀：小鲁鲁在宜宾养老帖子 `948320` 发布回复 `13355013`，评论为“文中提到‘防跌倒报警’，后续可关注这些适老化设计的实际使用情况。”；canonical 页面 HTTP 200，回复 ID、马甲和正文均可见。该条作为当前 live 链路验收证据保留。

OpenClaw cron 使用 `/opt/homebrew/bin/python3`（3.14.6）；`/usr/bin/python3` 是不兼容的 3.9，不得回退。2026-08-19 18:15 自动调度真实运行成功并返回 `NOT_DUE`，证明非手动 scheduler 路径可用。

2026-08-19 20:30 自动恢复轮次：cron 自然触发，读取4、合格4、选中4、生成2、安全拒绝0、发布2，马甲“大葱妈”，熔断关闭。回复 `13355165`（电影加场）和 `13355166`（翠屏区充电站）在各自 canonical 页面 HTTP 200，马甲、回复 ID 和正文均可见。下一业务轮次由系统恢复为 22:31，仍遵守 90–150 分钟间隔。

2026-08-20 12:30 历史巡逻升级后的 OpenClaw cron 自然恢复运行：读取3、合格2、生成并安全通过1、发布1，`大葱妈 / 948413 / 13355635` 在 canonical 页面可见；cron `status=ok`、业务熔断关闭、连续错误0。历史页游标从1推进到2，下一业务 due 将继续历史第2页；楼层回复传输开关仍关闭。

2026-08-20 12:54 楼层回复金丝雀：用户明确授权网友评论正文发送给 `openai/gpt-5.5`。系统只选1条并通过100分质量门，沉默的咸鱼在 `948365` 定向回复目标 `13355640`，新回复 `13355651`；findpost 公开页 HTTP 200，目标、新回复、马甲和正文均可见。按约定金丝雀后先关闭，用户随后确认“没问题”；系统增加“！，”等标点碰撞归一化回归门后，`reply_enabled=true` 正式启用。

2026-08-20 14:45 三马甲模式首个自然due进入新分支，4个不同目标按observer/helper/counterpoint=`2/2/1`分配，模型实际生成并安全通过3条；本地千帆直接发布2条后触发平台30秒限流并停止，成功项已幂等落盘。系统随后固定31秒间隔，并增加娃娃/退费违约金、医院医师医务、招聘找工作工资硬过滤。15:00原OpenClaw cron自然恢复，只剩2个安全楼层目标，observer/helper/counterpoint=`1/1/0`，发布2条并全部公开可见；cron status=ok、业务熔断关闭、连续错误0。扩大6页的真实no-send得到17个候选，2个被研究门淘汰，最终目标5/5/5、生成10、安全通过8；因此继续升级为最多10页+3个研究备选。当前55项相关测试通过。

2026-08-20 17:00/17:15 暴露千帆POST成功但回复ID延迟同步：`948421`两次真实发布未及时落盘，导致重试。已从千帆审核列表补证`13355793/13355808`并写回幂等台账；代码改为接口明确成功时立即按published落盘，即使reply_id暂为空也不重发。56项相关测试通过。18:15原OpenClaw cron自然恢复，18个不同目标按6/6/6分配，安全门通过9条并全部发布：大葱妈3、小鲁鲁2、沉默的咸鱼4；九个findpost页面均HTTP200且ID/马甲/正文可见，日累计23<72，cron和业务熔断均关闭。

详细边界见 [docs/spec.md](docs/spec.md)，实施状态见 [tasks/todo.md](tasks/todo.md)。
