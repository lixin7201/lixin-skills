# 原则候选（阶段 1 · principle-extractor）

> 独立扫描范围：`corpus/train/` 的 101 篇冻结训练正文；`cangjie/stage0-evidence/` 仅作篇目导航。未读取冻结训练范围外语料或其他 extractor 输出。本阶段只收集候选，不做 V1/V2/V3 筛选。

```yaml
- id: p01
  title: 先求不出局，再求多次获利
  type: principle
  source_chapter: "BXSF-001-20211205 · 2021-12-05 · 我建议你不要看完；BXSF-009-20220316 · 2022-03-16 · 中概互联网，财富本质，时间奥秘，风险感知，次数理论，热战能源战金融战"
  source_quote: |
    [BXSF-001] “说到底，不亏钱就是王道，任何时候都要记住，不亏钱，不亏钱。”
    [BXSF-009] “如果你能够熬过一万次狙杀，都不死，那你一定能够学会风险管理。”
  summary: |
    先把单次失败限制在不会出局的范围内，再谈收益率。
    只要系统允许继续参与，经验、数据和修正机会才会累积；一次重伤足以令此前优势归零。
    这是作者在交易语境中反复强调、也可迁移到职业试错与创业实验的行动底线。
  tags: [principle, survival, risk-control, repeatability]

- id: p02
  title: 用足够大的安全边际换取反应时间
  type: principle
  source_chapter: "BXSF-001-20211205 · 2021-12-05 · 我建议你不要看完"
  source_quote: |
    “任何时候，买的足够低，卖的足够高，都是王道。”
  summary: |
    入场价或承诺条件要留下足够宽的安全区，而不是把结果押在精确预测上。
    安全边际的价值不只在价格差，也在于它延长了发现错误、退出或调整的时间。
    适用于有明确成本位、退出条件和对手盘的决策。
  tags: [principle, margin-of-safety, time, entry-condition]

- id: p03
  title: 用大量尝试校准风险收益平衡
  type: principle
  source_chapter: "BXSF-001-20211205 · 2021-12-05 · 我建议你不要看完"
  source_quote: |
    “第二点、通过大量的尝试与数据，构建翻台率与风险的平衡点。”
  summary: |
    不从少数成败直接归纳规律，而要用足量数据和重复尝试寻找可接受的风险—收益组合。
    单次利润、参与频率、机会成本与生存概率要一起权衡。
    规则应由样本反馈逐步校准，而不是由一次好运确认。
  tags: [principle, experimentation, data, calibration, risk-reward]

- id: p04
  title: 高杠杆行动只进入可对冲环境
  type: principle
  source_chapter: "BXSF-001-20211205 · 2021-12-05 · 我建议你不要看完"
  source_quote: |
    “第三点、一定要待在有办法对冲的环境下。”
  summary: |
    当决策使用高杠杆、暴露于黑天鹅或单边变化时，必须预先拥有锁定风险或争取时间的手段。
    对冲不是消灭成本，而是在判断正确但时间错位时避免被迫出局。
    若没有可操作的缓冲机制，应降低杠杆或不入场。
  tags: [principle, hedge, leverage, optionality, tail-risk]

- id: p05
  title: 先建规则，再参加博弈
  type: principle
  source_chapter: "BXSF-016-20220701 · 2022-07-01 · 从26个美股坐庄被罚5亿的中国牛散，来聊职业量化对冲套利交易；BXSF-037-20230301 · 2023-03-01 · 已有6亿栋房屋"
  source_quote: |
    [BXSF-016] “你必须先建立规则，规则不等于完善，能够长期稳定盈利的交易系统，也许最初建立出来之后，是稳定亏损的。”
    [BXSF-037] “下场博弈之前一定要敲定双方的游戏规则，就好比马走日，象走田，只能这么走。”
  summary: |
    在投入资源之前，先确认参与者是否受同一套规则约束，并建立自己的可复用行动规则。
    初版规则可以不完善，甚至暂时表现不佳，但必须能够被记录、检验和修正。
    若对方可任意改规则，风险就不可管理，不应把它伪装成投资或系统决策。
  tags: [principle, rules, system, precommitment, game-boundary]

- id: p06
  title: 用实践培养能力，不把现实当选择题
  type: principle
  source_chapter: "BXSF-012-20220501 · 2022-05-01 · 是什么阻碍了我们跨越阶层？"
  source_quote: |
    “教育的作用就是选拔，实践的作用才是培养人才。”
    “当你习惯性的，下意识地去寻找ABCD里面正确的那一个的时候，你已经输了。”
  summary: |
    知识和考试最多提供入场券，真正的能力要在开放情境中通过行动、反馈与修正形成。
    现实问题通常没有预制的唯一答案，不能用寻找标准选项代替承担结果。
    学习安排应尽早纳入真实实践，而不是等全部知识学完才行动。
  tags: [principle, practice, learning, open-world, anti-test-thinking]

- id: p07
  title: 任何策略都不能先骗过自己
  type: principle
  source_chapter: "BXSF-006-20220211 · 2022-02-11 · 趁风控不在，在结婚这个话题上，跟女读者们说两句掏心窝子的话；BXSF-115-20260423 · 2026-04-23 · 这辈子还能有出路么？"
  source_quote: |
    [BXSF-006] “销售名言，骗谁都可以，千万不要骗自己。”
    [BXSF-115] “所谓骗谁，都不能骗自己。”
  summary: |
    即使外部沟通包含包装、谈判或预期管理，内部判断也必须保留真实事实、目的和代价。
    一旦把对外叙事当成现实，策略就失去校正能力。
    这是语料跨四年重复出现的自我审计底线；对外欺骗本身仍需另行接受事实与伦理边界审查。
  tags: [principle, self-honesty, reality-check, boundary-sensitive]

- id: p08
  title: 按单位时间价值决定是否花钱换时间
  type: principle
  source_chapter: "BXSF-011-20220405 · 2022-04-05 · 与其每天聊上海，还不如让一部分读者先成就自己"
  source_quote: |
    “任何事情我第一反应都是计算自己的单位时间成本预期，能用钱解决的，优先用钱。”
  summary: |
    比较自己一单位时间的机会价值与外包、工具或加价购买速度的成本。
    当花钱能保护更高价值的目标或释放稀缺时间时，不能只因票面价格高就拒绝。
    规则的前提是额外支出确实带来更大的净收益，而非把消费合理化。
  tags: [principle, time-value, opportunity-cost, delegation]

- id: p09
  title: 尽快进入成果能被决策者看见的位置
  type: principle
  source_chapter: "BXSF-028-20221102 · 2022-11-02 · 机会在于人事变动"
  source_quote: |
    “所以职场第一课是什么？是你必须要离开这种岗位，你必须要走到一个被看得见的岗位上去。”
  summary: |
    长期停在成果只会被上级汇总、个人贡献不可识别的位置，努力容易成为他人的信用资产。
    职业早期应争取成为某项结果的可识别负责人，不等同于盲目追求带人职位。
    这一原则强调贡献与归因的连接，不授权虚报或抢夺他人成果。
  tags: [principle, career, visibility, ownership, attribution]

- id: p10
  title: 行动前先弄清委托者真正要什么
  type: principle
  source_chapter: "BXSF-010-20220401 · 2022-04-01 · 你看不懂人心，会什么都是白会；BXSF-053-20230918 · 2023-09-18 · 你飘了，连这种话题都敢聊了"
  source_quote: |
    [BXSF-010] “人一定要明白人家为啥提拔你，人家提拔你是去干啥的。”
    [BXSF-053] “最重要的不是盲目地干，而是一定要想明白，领导究竟希望自己干什么。”
  summary: |
    接受职位、资源或任务时，先确认授权者期待你解决的问题、优先级和角色边界。
    只把事情做多，不等于把委托完成；努力方向错位还可能制造冲突。
    适用时应通过明确沟通验证，不能仅凭揣测上意替代事实。
  tags: [principle, principal-agent, role-clarity, workplace]

- id: p11
  title: 先对齐对方需求，再判断自身筹码
  type: principle
  source_chapter: "BXSF-044-20230525 · 2023-05-25 · 女人不要点进去看哦，给男人留点优势吧；BXSF-115-20260423 · 2026-04-23 · 这辈子还能有出路么？"
  source_quote: |
    [BXSF-044] “你必须做精准定位，你一定要弄清楚人家要什么，然后看看你有什么，有些什么是可以踮起脚来够一够的，这就有可能成交。”
    [BXSF-115] “一个优秀的商人，一定是能够抓住客人的真实需求的。”
  summary: |
    交易、求职或合作不能从“我有什么想卖”单向出发，要先识别对方真实需求。
    再盘点自己已有、可补齐和无法满足的条件，决定是否成交及如何呈现价值。
    需求识别应靠调查与验证，不能把刻板印象当作客户事实。
  tags: [principle, demand, positioning, negotiation, product-market-fit]

- id: p12
  title: 有需求再生产，不先做完再找理由
  type: principle
  source_chapter: "BXSF-058-20231215 · 2023-12-15 · 什么才是真正的百年未有之大变局"
  source_quote: |
    “你不可能先干了再说，你得有需求，再做。”
  summary: |
    产品、项目和产能投入应由可验证需求牵引，而不是先堆供给再期待市场接盘。
    在重投入、反馈慢的场景中，先证明有人需要、愿意付出资源或承担采用成本。
    可用小样、预售或访谈测试需求，避免把个人热情误当市场。
  tags: [principle, demand-first, validation, product]

- id: p13
  title: 放弃普遍机会假设，寻找结构性机会
  type: principle
  source_chapter: "BXSF-058-20231215 · 2023-12-15 · 什么才是真正的百年未有之大变局"
  source_quote: |
    “你必须放弃过去几十年养成的普遍机会的思维方式，要认识到，未来只会有结构化机会，再也没有普遍机会。”
  summary: |
    当整体增长不再平均扩散时，不应把旧时代的普涨经验外推到所有行业、城市或资产。
    决策要具体到受益结构、约束条件、位置与时间窗口。
    这是一条强时代表述，后续使用必须重新核验当前数据，不能当作永久事实。
  tags: [principle, structural-opportunity, regime-change, time-sensitive]

- id: p14
  title: 每次结果都要知道为什么赢或输
  type: principle
  source_chapter: "BXSF-046-20230619 · 2023-06-19 · 怎么看即将到来的经济刺激这个大动作？"
  source_quote: |
    “就像一个稳定盈利的职业赌客，他不在乎赢，但是他在乎，哪怕自己输，也一定要知道自己为什么输，就像自己赢，要知道为什么赢。”
  summary: |
    复盘不能只记录结果，还要把结果与原先假设、执行偏差、随机性及环境变化对应起来。
    赢而不知原因会把运气固化成规则，输而不知原因则无法修正。
    对无法区分因果与偶然的结果，应保留不确定性，而不是事后编故事。
  tags: [principle, review, attribution, learning-loop]

- id: p15
  title: 养成自我计时计费习惯
  type: principle
  source_chapter: "BXSF-054-20231013 · 2023-10-13 · 女怕嫁错郎，男怕不懂行"
  source_quote: |
    “你一定要养成自我计费的习惯，你就是一台行走的出租车，只不过你的脑门子上不显示价码表，但你心里要计数。”
  summary: |
    评估任务、关系和机会时，把投入时间视为有替代用途的稀缺资源。
    同时估算当前时间价值与未来能力提升后的时间价值，避免长期被低价值事务占满。
    计费是决策工具，不等于把全部人际关系货币化。
  tags: [principle, time-accounting, opportunity-cost, boundary]

- id: p16
  title: 让预期随数据更新
  type: principle
  source_chapter: "BXSF-066-20240410 · 2024-04-10 · 十年后的终局是什么"
  source_quote: |
    “多数人的预期必须跟着数据做调整，当然，你说你是天才，是幸运儿，那除外。”
  summary: |
    预测和规划不是一次性立场；新数据与原假设冲突时，必须调整概率和行动。
    不能因为身份、面子或既有投入而固守旧预期。
    更新幅度应与证据强度匹配，既不拒绝修正，也不被单点噪声牵着走。
  tags: [principle, updating, evidence, forecast]

- id: p17
  title: 现实规划必须留下大容错度
  type: principle
  source_chapter: "BXSF-071-20240622 · 2024-06-22 · 男怕入错行，女怕嫁错郎，人怕选错城，更怕买错房"
  source_quote: |
    “现实中你的规划一定要有非常大的容错度，否则计划永远赶不上变化快。”
  summary: |
    不把人生或项目建立在多个事件必须按固定顺序全部命中的脆弱链条上。
    路径应允许某些假设失效、时间延迟或地点变化后仍能继续。
    优先积累可迁移能力、备用路径与可逆动作，以降低单点失败。
  tags: [principle, robustness, planning, optionality]

- id: p18
  title: 同类条件下用一致规则决策
  type: principle
  source_chapter: "BXSF-069-20240528 · 2024-05-28 · 是什么在妨碍我们财富增值，工作稳定，婚姻靠谱"
  source_quote: |
    “建立系统最重要，做一个决策，你要想，是不是此后相同的条件下，你都会做同样的决策，或者说，必须这么做决策?”
  summary: |
    一项行动若无法说明在同类条件下是否会重复，就还不是可检验的系统。
    将决策条件、阈值与退出规则写清，才能识别临场情绪和事后解释。
    一致不等于僵化；条件发生实质变化时，规则本身也应按证据升级。
  tags: [principle, consistency, decision-system, reproducibility]

- id: p19
  title: 优先发挥相对最稀缺的优势
  type: principle
  source_chapter: "BXSF-083-20241218 · 2024-12-18 · 巨变已至，除了迎合，我们别无选择"
  source_quote: |
    “你智商在人群中排第几，情商排第几，家境排第几，如果有一项相对于其他两项产生了绝对优势，那就优先考虑绝对优势。”
  summary: |
    选择方向时比较能力、关系、资源等维度在人群中的相对排名，而非只看绝对分数。
    当某一维度形成显著差距，应优先把它放到能兑现的位置。
    若各项接近，则不能夸大“选对一次”对结果的作用，仍需能力和执行。
  tags: [principle, comparative-advantage, positioning, career]

- id: p20
  title: 挣钱前先回答凭什么轮到自己
  type: principle
  source_chapter: "BXSF-080-20241103 · 2024-11-03 · 美国大选的重大影响以及未来我们的经济预判分析"
  source_quote: |
    “我常说那句话：你在挣钱之前，一定要想明白这钱凭什么让你挣。”
  summary: |
    面对看似容易的收益，先找出自己的信息、成本、速度、位置或稀缺性优势。
    如果说不清价值来源，就应优先怀疑隐藏风险、拥挤交易或骗局。
    可持续收益需要可解释的价值交换，不能只以“别人赚过”作为依据。
  tags: [principle, value-capture, edge, due-diligence]

- id: p21
  title: 为必经转型预留现金跑道
  type: principle
  source_chapter: "BXSF-103-20251011 · 2025-10-11 · 阿川开启下半场？个人如何打赢这场命运之战？"
  source_quote: |
    “我必须要有一笔钱，度过转型带来的收入下降期，我才可能有勇气去迎接转型。”
  summary: |
    把未来转型期间的收入下降、学习成本和试错支出列为储蓄的优先用途。
    没有现金跑道，即使看见旧路径失效，也容易因短期生存压力而不敢行动。
    跑道规模应根据家庭责任、转型周期和最坏情形具体计算。
  tags: [principle, runway, transition, savings, resilience]

- id: p22
  title: 弄懂成功原因，并把一个策略练熟
  type: principle
  source_chapter: "BXSF-104-20251026 · 2025-10-26 · 新周期已经两年了，从不相信到不甘心，我还来得及么"
  source_quote: |
    “第一个看法：人一定要弄懂，自己到底为什么成功。”
    “听过千个不如怎么样？不如熟练一个。”
  summary: |
    不能把成功简单归因于读过某篇文章、选中某标签或碰巧使用某工具。
    要识别真正的差异变量，并在一个可承载的策略上持续回测、模拟和积累熟练度。
    在尚未成为一个领域的老手之前，频繁追逐新策略只会让熟练度长期归零。
  tags: [principle, success-attribution, focus, mastery]

- id: p23
  title: 仓位和杠杆必须匹配追加保证金能力
  type: principle
  source_chapter: "BXSF-101-20250907 · 2025-09-07 · 投资，我还来得及么？"
  source_quote: |
    “你究竟能加多大杠杆，是你追加保证金的实力决定的。只有做好了仓位与杠杆的匹配管理，你才能试图去钓中间层的鱼。”
  summary: |
    杠杆上限不能按正常波动或主观确信计算，要按异常价格持续期间自己能补充的流动性计算。
    先模拟极端浮亏、停牌或流动性断裂，再决定仓位。
    若无法承受压力情景，就缩小仓位、降低杠杆或不参与。
  tags: [principle, position-sizing, leverage, stress-test]

- id: p24
  title: 从自身够得着的支点入局
  type: principle
  source_chapter: "BXSF-108-20251221 · 2025-12-21 · 铁打的中产，流水的中产阶级"
  source_quote: |
    “而所有想要入局的人，你必须要找到一个支点，这个支点就是你自身条件能够得上的那个起点。”
  summary: |
    新领域的第一步应由现有资金、能力、身份和可承担损失决定，而不是复制强者当前的位置。
    一个小但真实可执行的起点，优于宏大却无法启动的方案。
    从支点获取反馈和资源，再逐步扩大动作半径。
  tags: [principle, starting-point, resource-fit, execution]

- id: p25
  title: 先定最高优先级，只解决当前瓶颈
  type: principle
  source_chapter: "BXSF-108-20251221 · 2025-12-21 · 铁打的中产，流水的中产阶级；BXSF-115-20260423 · 2026-04-23 · 这辈子还能有出路么？"
  source_quote: |
    [BXSF-108] “人这辈子，一定要想清楚你要什么。”
    [BXSF-115] “什么卡你，做什么，而不是什么简单，做什么。”
  summary: |
    不能同时追逐钱、权、感受和所有外部任务；先明确当下最重要的目标。
    再找出阻碍该目标的首要瓶颈，优先处理它，而不是用熟悉、简单的忙碌回避难题。
    优先级改变时应重排任务，但同一时段只追一只关键“兔子”。
  tags: [principle, priority, bottleneck, focus]

- id: p26
  title: 变局中先回答“我怎么办”
  type: principle
  source_chapter: "BXSF-114-20260409 · 2026-04-09 · 宇宙的尽头是灵活就业么"
  source_quote: |
    “永远不要去想大家怎么办，要想我怎么办。”
  summary: |
    面对技术或制度冲击，宏观同情和群体预测不能代替个人行动方案。
    先识别自己可能承担的代价、可利用的机会和能够控制的下一步。
    该原则不是否认公共责任，而是要求个人决策落到自身约束与动作上。
  tags: [principle, agency, regime-change, action]

- id: p27
  title: 学习必须连续地知行合一
  type: principle
  source_chapter: "BXSF-118-20260604 · 2026-06-04 · 你不是懒，你只是看不到这辈子的出路；BXSF-113-20260325 · 2026-03-25 · 人这辈子怎么才能拎得清"
  source_quote: |
    [BXSF-118] “这就叫学习必须是连续的，必须是知行合一的过程，而不能是分成两个阶段的。”
    [BXSF-113] “你会运用，理论能结合实际，实际还反哺理论，才叫真懂了，真知行合一了。”
  summary: |
    不把人生切成“先多年只学、以后再做”的两个隔离阶段。
    每轮学习都要尽快用于实践，再让实践结果反哺理论，形成连续循环。
    只有能在新情境中使用并修正的知识，才算真正掌握。
  tags: [principle, learning-loop, practice, iteration]

- id: p28
  title: 选择前先说明基于什么
  type: principle
  source_chapter: "BXSF-116-20260507 · 2026-05-07 · 财富大洗牌，我该选择，还是努力？"
  source_quote: |
    “选择不是重点，基于什么选择才是。”
    “地球上不存在选择，只存在基于什么选择。”
  summary: |
    不直接争论选行业 A 还是 B、买还是卖，而先列出概率、资源、目标、期限和限制条件。
    背景条件不同，适合不同人的答案自然不同；脱离依据的选项讨论没有可迁移价值。
    对依据不充分的选择，应保留不确定性并设计小规模验证。
  tags: [principle, choice, evidence, context, probability]

- id: p29
  title: 路径要匹配自己的反馈耐受度
  type: principle
  source_chapter: "BXSF-116-20260507 · 2026-05-07 · 财富大洗牌，我该选择，还是努力？"
  source_quote: |
    “所以人要尊重自己，认识自己，根据自己的实际情况来安排一条适合自己反馈机制的道路。”
  summary: |
    先辨认自己能承受短、中还是长反馈，再选择学习、职业或投资路径。
    不能承受多年无正反馈的人，不应一开始就把全部资源押在超长周期上。
    可从较短反馈建立能力与心态，再随经验和资源增长延长周期。
  tags: [principle, feedback-cycle, self-knowledge, path-design]

- id: p30
  title: 快速学习、切入、试错，失败就重来
  type: principle
  source_chapter: "BXSF-115-20260423 · 2026-04-23 · 这辈子还能有出路么？"
  source_quote: |
    “快速学习，快速切入，快速试错，尽可能多来几局。”
    “快速迭代快速试错看看能否押中风口，不行赶紧重来。”
  summary: |
    在变化快且允许小额试错的领域，压缩从学习到真实反馈的时间。
    单次投入要可承受，失败后迅速复盘并开始下一轮，而不是守着沉没成本。
    该原则不适用于不可逆、高伤害或法律伦理风险场景。
  tags: [principle, rapid-iteration, experimentation, recovery]

- id: p31
  title: 不让沉没成本绑定未来选择
  type: principle
  source_chapter: "BXSF-115-20260423 · 2026-04-23 · 这辈子还能有出路么？"
  source_quote: |
    “我们太多人，习惯于把一切沉没成本，都当成必须伴随自己一生的东西，这种心态叫敝帚自珍。”
  summary: |
    已花掉的时间、学费、爱好支出或资产买入价，不能自动成为继续投入的理由。
    重新依据当前需求、未来收益和替代方案决定去留。
    承认损失的心理不适，但不能要求市场或他人为过去成本买单。
  tags: [principle, sunk-cost, loss-aversion, exit]

- id: p32
  title: 资源来自与真实任务绑定
  type: principle
  source_chapter: "BXSF-063-20240228 · 2024-02-28 · 时代要被颠覆了么"
  source_quote: |
    “你永远不出征，你就永远拿不到资源，你想要拿到资源，你就必须把自己和事儿绑定。”
  summary: |
    资源通常随责任、结果和风险一起分配，不能只请求资源而不承接真实任务。
    想扩大影响力，就要成为某项可验证成果的责任主体，并接受相应问责。
    绑定应建立在职责清晰和风险可承受的前提上，不能演变成无边界背锅。
  tags: [principle, ownership, responsibility, resource-allocation]
```

## 提取器自检

- 候选数：32（目标区间 15–35）。
- 时期覆盖：来源引用按年份计为 2021（4 处）、2022（7 处）、2023（7 处）、2024（6 处）、2025（5 处）、2026（10 处）；部分候选含跨期复现证据。
- 职责边界：均写成可直接决定“做 / 不做 / 先做什么”的原则；未把完整推理框架、案例、术语单独冒充原则。
- 引用：均来自冻结 train 正文，单段引用不超过 150 字；跨文复现以独立标签保留。
- 隔离：未读取或引用冻结训练正文之外的语料、评测清单正文或其他 extractor 输出。
