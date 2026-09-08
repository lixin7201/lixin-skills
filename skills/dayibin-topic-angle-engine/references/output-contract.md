# 输出契约：先给可选择的标题

## angle-only

先一句说明平台和力度（已有上下文可省）。默认4—6个真正不同的角度；明确要求数量则尽量满足，材料不成立不能凑数。

每题：

**1. 推荐标题**
- 另一个钩子：一条标题备选。
- 怎么展开：2—4句，说清要写什么、新在哪里，避免把标题扩写一遍。
- 读者为什么想看：一个具体理由，可含能贡献的经验或选择。
- 依据/待做：一句。若待采访/实测，标“策划标题，待执行”。

不把推荐标题与“更大胆”固定绑定成两个强弱级别；大胆且能兑现的标题放推荐位。推荐第一题，必要时另指出值得补采的一题，不锁唯一选题。没有材料给5条就给更少，不堆低质陪跑。

## headline-only

“选题已锁定：……”一句；随后5个完整标题按推荐顺序排列，第一条标推荐。

标题在同一角度内分别尝试不同关注点，不能重选题。不要求固定数量的问句、数字、情绪词；不要5个近义句。最后用1—2句说明第一条为什么最值得点、资料是否能兑现；用户只要标题时不额外展开。

## review-angle

先给改好的角度＋标题，再简述旧稿最主要的问题。只改标题请求按headline-only，不回头换主张。

## 兼容交接卡（选定/自动写稿/请求结构化时才展示）

```yaml
angle_card:
  angle_id: A1
  locked_angle_id: A1
  idea_value: strong
  status: READY # 或 HOLD_FOR_EVIDENCE / NO_GO
  source_facts: [] # 带来源与时间
  audience_relationship: {audience: '', scene: '', consequence: ''}
  why_now: '' # 普通常青题可说明真实需求；不编热点
  core_tension: '' # 也可为发现、期待、参与机会，不硬造冲突
  non_obvious_judgment: null # 探索题可空，不能强定反常识结论
  core_question: ''
  explicit_exclusions: []
  evidence_and_gaps: {supporting: [], unknown: [], forbidden_claims: []}
  strongest_counterargument: null # 服务/记忆可不适用；争议题填替代解释
  reader_payoff: ''
  comment_share_trigger: {comment: '', share: ''} # 预期动机，不冒充实际评论
  risk_boundary: {level: low, controls: []}
  headline_options:
    headline_primary: ''
    headline_alt_change: '' # 不适用可null
    headline_alt_scene: '' # 不适用可null
  selected_headline: ''
  headline_promise:
    reader_expects: ''
    pay_off_with: [] # 支撑标题承诺的材料或正文段落任务
    necessary_conditions: []
    unresolved: []
  angle_exposition: ''
  suggested_structure: [] # 按素材自然展开，不固定三段
  score: {total: null, breakdown: {angle_value: strong, headline_pull: strong}, deductions: []}
  writer_handoff:
    locked_angle_id: A1
    selected_writing_skill: undecided
    article_type: ''
    channel: ''
    must_preserve: [核心问题, selected_headline的主钩子, headline_promise, 事实状态]
    may_optimize: [标题顺句, 段落节奏]
    must_not_do: [重新选题, 添加无来源事实, 第二写稿人混写, 为了稳妥抹掉已成立的标题钩子]
```

未选择角度时locked_angle_id为空，writer_handoff不启动。选定但证据不足时作者保持undecided。

交接指令：你是唯一正文作者，保留已选角度和标题承诺，用现有事实兑现钩子；本卡覆盖默认重新选题及标题固定分组。允许优化措辞，不允许换主钩子或假造体验；兑付不了时退回改标题/补采。不得把内部方法、状态或字段写进公开正文。
