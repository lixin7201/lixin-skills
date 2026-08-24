# 输出契约

默认先给人类可读的编辑结论，再给结构化卡片。字段名保持稳定，便于后续写稿 Skill 直接接收。没有的信息填 `unknown` 或空数组，不得编造。

## 第一屏编辑结论

```text
【状态】READY / HOLD_FOR_EVIDENCE / NO_GO
【推荐角度】一句话
【首选标题】一句话
【为什么是它】2—4 句，明确读者关系、观点增量和证据强度
【写稿去向】angle-only 停止 / auto-handoff → <唯一写稿 Skill>
```

## 赢家角度卡

```yaml
angle_card:
  angle_id: "A1"
  status: "READY | HOLD_FOR_EVIDENCE | NO_GO"
  source_facts:
    - claim: "已确认事实"
      source: "原始来源或用户材料"
      freshness: "时间"
  audience_relationship:
    audience: "具体读者"
    scene: "他们在什么场景遇到这件事"
    consequence: "对他们的具体影响"
  why_now: "为什么是现在，而不是任何时候都能写"
  core_tension: "变化/冲突/成本/机会/风险"
  non_obvious_judgment: "全文要证明的唯一主判断"
  explicit_exclusions:
    - "这篇不写什么、不声称什么"
  evidence_and_gaps:
    supporting: ["支撑主判断的证据"]
    unknown: ["待核实信息及其影响"]
    forbidden_claims: ["无证据不得使用的说法"]
  strongest_counterargument:
    argument: "最强反方，不做稻草人"
    response_or_boundary: "回应或承认适用边界"
  reader_payoff: "读完获得的理解、决定、行动或情绪价值"
  comment_share_trigger:
    comment: "读者可以贡献的真实经验或分歧"
    share: "会转给哪一类具体对象以及为什么"
  risk_boundary:
    level: "low | medium | high"
    controls: ["核验、匿名、降级或措辞边界"]
  headline_options:
    headline_primary: "信息明确型；推荐"
    headline_alt_change: "变化/张力型"
    headline_alt_scene: "人物/场景型"
    rejected_clickbait: "更猛但因越界被拒的示例或 none"
  angle_exposition: |
    150—300 字。说明常见写法是什么、本角度新在哪里、围绕哪些事实展开、
    如何把读者带入、核心判断怎样一步步成立，以及文章不该滑向哪里。
    这不是摘要，更不是正文开头。
  suggested_structure:
    - section: "进入"
      job: "用事实变化或读者场景建立问题"
      evidence: ["可用事实"]
    - section: "展开"
      job: "解释机制、代价或人的处境"
      evidence: ["可用事实"]
    - section: "落点"
      job: "兑现主判断并给行动/讨论入口"
      evidence: ["可用事实"]
  score:
    total: 0
    breakdown: {}
    deductions: []
  writer_handoff:
    locked_angle_id: "A1"
    selected_writing_skill: "exact-skill-name | undecided"
    article_type: "建议稿型"
    channel: "大宜宾公众号或用户指定平台"
    target_length: "由写稿 Skill 和素材强度决定"
    must_preserve:
      - "non_obvious_judgment"
      - "事实状态与读者关系"
      - "strongest_counterargument 的公平边界"
    may_optimize:
      - "标题措辞"
      - "段落节奏"
      - "开头场景（不得虚构）"
    must_not_do:
      - "重新选题"
      - "增加无来源事实"
      - "调用第二写稿人混合文风"
```

## 备选角度卡

至少展示 3 个通过初筛的备选；素材确实不足时如实减少并解释。

```yaml
alternatives:
  - angle_id: "A2"
    angle_family: "六类家族之一"
    one_line_angle: "核心问题 + 非显然判断"
    headline: "一个能兑现的标题"
    angle_exposition: "80—150 字，写清如何展开，不是标题释义"
    score: 0
    lost_because: "为什么没赢"
    upgrade_needed: "补什么才可能反超"
```

## 淘汰与人物挑战记录

```yaml
editorial_trace:
  mother_topic: "母题"
  history_dedup: "已检查的范围，或 not_checked"
  persona_lenses_used:
    - persona: "最多三位；可为空"
      challenge: "提出了什么反证问题"
      change_made: "候选因此如何改变"
  knocked_out:
    - angle_id: "A6"
      gate: "K1—K7"
      reason: "具体原因"
```

## 写稿交接提示词

把以下块连同完整 `angle_card` 原样交给唯一写稿 Skill：

```text
你是本稿唯一正文作者。选题已经锁定，不得重新选题或引入第二写稿人。
围绕 locked_angle_id 和 non_obvious_judgment 成稿。
只使用 source_facts；INFERENCE 必须写成推断；UNKNOWN 不得补写。
标题可在 headline_options 内优化，但不得超过事实承诺。
必须保留 must_preserve，遵守 risk_boundary 和 explicit_exclusions。
如素材不足以支撑建议篇幅，降级为短稿/提纲并列补采清单，不得注水。
```
