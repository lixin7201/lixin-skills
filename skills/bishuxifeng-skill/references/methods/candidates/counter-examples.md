# 反例 / 失败模式候选（阶段 1）

> 输入边界：仅使用冻结的 101 篇 `corpus/train/` 正文与阶段 0 导航。以下为反例提取器的独立候选，不作阶段 1.5 筛选。

- id: ce01
  title: 把易失效招数当成永久秘籍
  type: counter-example
  source_chapter: "BXSF-001-20211205 · 2021-12-05 · 我建议你不要看完"
  source_quote: |
    市场里没有降龙十八掌。并不存在什么一招鲜吃遍天。高招当然是有的，但是高招不停的在变，可能几个月就失效了，而你学习高招的周期则可能长达几年。
  failure_mode: |
    追求可照抄的一招鲜，把学习周期很长的固定技巧用于快速变化的市场，学成时方法已经失效。
  mechanism: |
    技巧的半衰期短于掌握它的时间；学习者又依赖别人嚼过的结论，缺少从数据、反馈和迁移中自行更新规则的能力。
  warning_signs:
    - 反复追问“有没有一招制胜的方法”
    - 只收藏技巧，不记录方法何时失效
    - 环境变化后仍按原步骤执行
  bound_to:
    - "交易系统与赌博分界"
    - "可迁移能力与职业选择权"
  tags: [counter-example, fixed-trick, decay, transfer]

- id: ce02
  title: 只判断方向，不管理仓位与风险
  type: counter-example
  source_chapter: "BXSF-007-20220216 · 2022-02-16 · 普通人改变命运，要靠神秘的康波周期么？"
  source_quote: |
    点位，仓位，风险管理。你抓着一头有什么用啊，卵用都没有。市场里很多人都有预测行情的本事，问题是，后面俩没法解决。
  failure_mode: |
    把“看对方向”当作完整决策，在时间点不确定、仓位过重或杠杆过高时，即使长期判断正确也会先出局。
  mechanism: |
    方向、时间、仓位和损失承受力共同决定能否兑现判断；只看方向会把路径风险和生存约束从模型中删掉。
  warning_signs:
    - 讨论观点时从不提仓位
    - 把长期趋势直接等同于近期入场信号
    - 没有最大损失和退出条件
  bound_to:
    - "毁灭性风险与选择权保护"
    - "周期—个体路径匹配"
  tags: [counter-example, position-sizing, timing, ruin-risk]

- id: ce03
  title: 把周期叙事当作必然反弹公式
  type: counter-example
  source_chapter: "BXSF-007-20220216 · 2022-02-16 · 普通人改变命运，要靠神秘的康波周期么？"
  source_quote: |
    衰退期之后一定是再投资期么？这意思就是说，只要你蹲在坑里足够久，马桶里总会冒出一股神秘的洪荒之力，把你弹出去的，是这样吗？
  failure_mode: |
    从少数经济体的历史序列抽象出固定周期，然后假定任何地区、行业和个人只要等待就会自动进入繁荣阶段。
  mechanism: |
    样本选择、地区差异和技术冲击被压扁成单一循环；周期标签提供了确定感，却没有给出可证伪条件和个体兑现路径。
  warning_signs:
    - 用“早晚会轮到”代替条件分析
    - 无法解释长期停滞地区或消失行业
    - 把等待本身当成策略
  bound_to:
    - "周期—个体路径匹配"
    - "终局倒推与隐藏选项构造"
  tags: [counter-example, cycle-determinism, extrapolation, falsifiability]

- id: ce04
  title: 因一局输赢临时改规则
  type: counter-example
  source_chapter: "BXSF-016-20220701 · 2022-07-01 · 从26个美股坐庄被罚5亿的中国牛散，来聊职业量化对冲套利交易"
  source_quote: |
    这个方法是规则，规则是不能改的，除非规则本身是错的。如果规则本身错了，那么也是重新换一整套新规则，整个换掉，而不是让自己的方法离散化。
  failure_mode: |
    每次根据上一局的结果更换打法，把偶然输赢当成规则好坏的证据，最终形成没有一致性的随机决策。
  mechanism: |
    点状结果放大了后悔和恐惧，使决策者对样本外噪声过拟合；规则没有获得足够样本验证，也无法复盘其长期期望。
  warning_signs:
    - 一次亏损后立刻反向操作
    - 同类情境下前后标准不同
    - 无法说清“改规则”需要什么证据
  bound_to:
    - "交易系统与赌博分界"
    - "能力—反馈周期匹配"
  tags: [counter-example, outcome-bias, overfitting, rule-drift]

- id: ce05
  title: 好靠山变成融资与信任陷阱
  type: counter-example
  source_chapter: "BXSF-021-20220817 · 2022-08-17 · 问某地大学城的，实际上就是在问，回报怎么才能对得起自己的付出"
  source_quote: |
    这是个非常好的开局对吧？但是这个开局就是结局。
  failure_mode: |
    过早绑定一个强势股东或客户，只看到它带来的资源，没有计算它对后续融资、市场准入和团队共担风险的排斥效应。
  mechanism: |
    强标签改变了第三方预期：新资本担心控制权冲突，其他客户担心阵营归属，伙伴则因创始人有退路而降低共同承担风险的意愿。
  warning_signs:
    - 单一股东接近控制线
    - 其他客户把公司视为某方附属
    - 团队认为核心人物随时可以退回靠山
  bound_to:
    - "利益—成本—激励换位审计"
    - "生态位与资源稳定性审计"
  tags: [counter-example, financing, dependency, trust]

- id: ce06
  title: 正确结论掩盖错误过程
  type: counter-example
  source_chapter: "BXSF-046-20230619 · 2023-06-19 · 怎么看即将到来的经济刺激这个大动作？"
  source_quote: |
    结果有可能你对了，我错了，但是你这种没有过程的结果，毫无价值。
  failure_mode: |
    因为一次结论碰巧正确，就把拍脑袋的方法认作有效能力，之后无法区分可重复优势与运气。
  mechanism: |
    结果偏误跳过了指标、因果链和反事实；没有可检查的过程，就没有办法定位误差、迁移经验或在环境变化时修正。
  warning_signs:
    - 复盘只说“我早就说过”
    - 事前没有记录条件和指标
    - 结论错误时归因运气，正确时归因能力
  bound_to:
    - "信息差与事实/推断边界"
    - "能力—反馈周期匹配"
  tags: [counter-example, result-bias, verification, luck]

- id: ce07
  title: 用战术疲惫掩盖战略懒惰
  type: counter-example
  source_chapter: "BXSF-050-20230814 · 2023-08-14 · 月亮还是那个月亮，人已不再是那个人"
  source_quote: |
    很多人以为的努力并不是努力，那只是用无效努力，用战术上的疲惫，来掩盖自己战略上的懒惰。
  failure_mode: |
    用大量未经筛选的动作制造勤奋感，却不做背景研究、对象过滤、成本收益比较和失败样本积累。
  mechanism: |
    忙碌提供即时的自我肯定，战略筛选则会暴露不确定性与能力缺口；人因此偏好重复低认知负担动作。
  warning_signs:
    - 工作量很大但命中率从不改善
    - 不记录拒绝原因和筛选条件
    - 以“我已经很努力”终止路径审计
  bound_to:
    - "终局倒推与隐藏选项构造"
    - "能力—反馈周期匹配"
  tags: [counter-example, busywork, strategy, selection]

- id: ce08
  title: 沿用旧路径却不重算时机与盈亏比
  type: counter-example
  source_chapter: "BXSF-050-20230814 · 2023-08-14 · 月亮还是那个月亮，人已不再是那个人"
  source_quote: |
    人家出国自己跟着出国，人家上岸自己跟着上岸，人家下海自己跟着下海。
  failure_mode: |
    因为某条路曾被身边人走通，就在不同周期中继续复制，而不重新计算进入时机、成本和自身条件。
  mechanism: |
    熟悉路径降低心理成本，群体行为又不断强化它；表面相同的选择掩盖了供需、价格和窗口期已经改变。
  warning_signs:
    - 主要理由是“大家都这么走”
    - 只引用早期成功者，不看当前进入者
    - 没有重新计算机会成本
  bound_to:
    - "周期—个体路径匹配"
    - "可迁移能力与职业选择权"
  tags: [counter-example, path-dependence, timing, herd]

- id: ce09
  title: 把局部稳定规律外推到周期之外
  type: counter-example
  source_chapter: "BXSF-059-20231227 · 2023-12-27 · 跨年演讲：若能提前看到未来，你会写给自己什么"
  source_quote: |
    他们误以为的规律，每天鸡笼上方的窗口会投放食物这个规律，会在感恩节前一天戛然而止。
  failure_mode: |
    将一个周期内长期成立的经验视为自然定律，没有识别决定该规律的上层制度和终止条件。
  mechanism: |
    高频重复让经验看似可靠，但观察者只看到系统输出，没看到控制系统的角色、目标和重启时点。
  warning_signs:
    - 依据是“过去一直如此”
    - 模型中没有制度切换或终止事件
    - 无法回答谁在维持这条规律
  bound_to:
    - "周期—个体路径匹配"
    - "信息差与事实/推断边界"
  tags: [counter-example, regime-change, induction, hidden-controller]

- id: ce10
  title: 一言堂制造信息茧房
  type: counter-example
  source_chapter: "BXSF-059-20231227 · 2023-12-27 · 跨年演讲：若能提前看到未来，你会写给自己什么"
  source_quote: |
    你一言堂习惯了，别人就不敢把真相告诉你，或者被迫告诉你，也不及时，他怕被你斥责。久而久之，你实际上构建了一个信息茧房，把自己给包裹起来了。
  failure_mode: |
    领导者用权威压制异议，最终只收到经过延迟、粉饰或筛选的信息，却误以为组织没有问题。
  mechanism: |
    说真话的个人成本上升后，理性成员会自我审查；决策者的信息优势随权力增加反而下降，错误又难以及时纠正。
  warning_signs:
    - 会议上总是迅速一致
    - 坏消息越来越晚出现
    - 反对意见被解释为态度问题
  bound_to:
    - "利益—成本—激励换位审计"
    - "信息差与事实/推断边界"
  tags: [counter-example, information-cocoon, authority, feedback]

- id: ce11
  title: 把赚到一笔钱等同于长期有钱
  type: counter-example
  source_chapter: "BXSF-059-20231227 · 2023-12-27 · 跨年演讲：若能提前看到未来，你会写给自己什么"
  source_quote: |
    我们很多时候最大的问题在于我想赚一笔钱，而不是我想有钱。好好品，这是两件事。我想赚一笔钱，我真赚到了一笔钱，不等于我就能有钱。
  failure_mode: |
    把单次高收益、奖金或资产上涨当成财富状态，忽略守住、再生产和跨周期配置能力。
  mechanism: |
    一次性结果显眼且即时，长期资产负债、现金流和风险暴露不显眼；人因而高估收入事件、低估财富系统。
  warning_signs:
    - 财富目标只写一次性金额
    - 没有收益来源的可重复性说明
    - 获利后同步扩大固定支出和杠杆
  bound_to:
    - "生态位与资源稳定性审计"
    - "毁灭性风险与选择权保护"
  tags: [counter-example, windfall, wealth-system, durability]

- id: ce12
  title: 自我评估在自负与自卑间摆动
  type: counter-example
  source_chapter: "BXSF-064-20240309 · 2024-03-09 · 2024经济大戏的序幕，已经拉开"
  source_quote: |
    我们很多人最大的问题就是一会儿极度自卑，一会儿又极度自负，你没有一个正确的评估。
  failure_mode: |
    评价自己时只有“换我也行”和“我没那个命”两个极端，无法形成能指导行动的能力—资源基线。
  mechanism: |
    极端评价都能逃避具体测量：自负省去准备，自卑省去尝试；二者都不要求把能力拆成可验证的小任务。
  warning_signs:
    - 同一人随结果在“天才/废物”间切换
    - 说不出自己能独立完成的最小成果
    - 不做小范围阶段性验证
  bound_to:
    - "能力—反馈周期匹配"
    - "生态位与资源稳定性审计"
  tags: [counter-example, calibration, overconfidence, learned-helplessness]

- id: ce13
  title: 倾巢出动导致流动性死亡
  type: counter-example
  source_chapter: "BXSF-069-20240528 · 2024-05-28 · 是什么在妨碍我们财富增值，工作稳定，婚姻靠谱"
  source_quote: |
    另一部分是盾，就是现金，保持流动性，做生意最忌讳倾巢出动，像胡雪岩那样的，也挡不住被挤兑。
  failure_mode: |
    为追求最大收益把现金和可退空间全部押上，遇到回款延迟、挤兑或周期切换时，被迫在最差时点退出。
  mechanism: |
    资产价值不等于即时支付能力；资金期限错配会把暂时波动变成永久出局，并夺走等待和谈判的选择权。
  warning_signs:
    - 方案需要所有资金同时到位
    - 没有覆盖固定支出的现金缓冲
    - 退出依赖“到时一定有人接手”
  bound_to:
    - "毁灭性风险与选择权保护"
    - "交易系统与赌博分界"
  tags: [counter-example, liquidity, all-in, forced-exit]

- id: ce14
  title: 把短期发薪误认作岗位稳定
  type: counter-example
  source_chapter: "BXSF-069-20240528 · 2024-05-28 · 是什么在妨碍我们财富增值，工作稳定，婚姻靠谱"
  source_quote: |
    他给你连续发叁个月工资，你就会误以为自己活在稳定的环境里。
  failure_mode: |
    因为短期收入连续，就停止监测公司、产品线、行业和技能周期，把暂时未发生风险当成永久稳定。
  mechanism: |
    人会把近期重复外推到未来；组织支付的平稳表象遮蔽了需求、技术和人口结构对岗位的上层约束。
  warning_signs:
    - 职业安全只用“现在没问题”证明
    - 技能多年未在外部市场验证
    - 收入来源完全绑定单一组织
  bound_to:
    - "可迁移能力与职业选择权"
    - "周期—个体路径匹配"
  tags: [counter-example, stability-illusion, recency, employability]

- id: ce15
  title: 训练方式与最终角色南辕北辙
  type: counter-example
  source_chapter: "BXSF-076-20240902 · 2024-09-02 · 远离这九个陷阱，你这辈子才会变好"
  source_quote: |
    慕容复的培养方式与他最终要实现的那个目标，是脱节的，甚至可以讲，是完全背离的。
  failure_mode: |
    想成为资源组织者或规则设计者，却长期只训练个人排名、服从标准和同层竞争。
  mechanism: |
    旧训练形成思维惯性：把获得老师认可等同于获得权力，把击败同伴等同于建立联盟，导致核心能力与目标角色错配。
  warning_signs:
    - 晋升规划只是把每项执行技能依次做到第一
    - 只靠评分者表扬判断接近目标
    - 没有练习担责、用人和资源连接
  bound_to:
    - "玩游戏/开发游戏跃迁评估"
    - "终局倒推与隐藏选项构造"
  tags: [counter-example, goal-misalignment, training, role-transition]

- id: ce16
  title: 把考勤与控制误当成经营管理
  type: counter-example
  source_chapter: "BXSF-076-20240902 · 2024-09-02 · 远离这九个陷阱，你这辈子才会变好"
  source_quote: |
    答案只有一个，他根本不懂得经营。岳不群会的那点东西，搁在今天讲，就叫考勤。
  failure_mode: |
    管理者把抓纪律、抓形式和亲自保持最强当成经营，长期没有形成基本盘、人才梯队和可让强者发挥的舞台。
  mechanism: |
    控制行为即时可见，组织能力建设回报滞后；小基本盘又让管理者害怕人才超过自己，进一步排斥强者并恶化组织。
  warning_signs:
    - 管理议题主要是打卡和纪律
    - 关键能力集中在负责人一人
    - 优秀下属越强，负责人越想限制他
  bound_to:
    - "利益—成本—激励换位审计"
    - "玩游戏/开发游戏跃迁评估"
  tags: [counter-example, management, control, talent-system]

- id: ce17
  title: 过度自我保护放大误解
  type: counter-example
  source_chapter: "BXSF-076-20240902 · 2024-09-02 · 远离这九个陷阱，你这辈子才会变好"
  source_quote: |
    这个错误就是早年成长环境引起的自卑，自卑引起的过度自尊，过度自尊引起的过度自我保护，过度自我保护引起的误解。
  failure_mode: |
    因过去解释无效而彻底拒绝沟通，用沉默和强硬保护自尊，结果让本可澄清的误会升级并牵连合作伙伴。
  mechanism: |
    旧伤把“解释”编码为示弱；当事人以为自己只承担误解成本，却忽略关系中的其他人也承受外溢伤害。
  warning_signs:
    - 常说“懂我的自然懂”
    - 明知可以澄清仍拒绝说明
    - 把所有追问理解成恶意审判
  bound_to:
    - "利益—成本—激励换位审计"
    - "角色选择与叙事剪辑边界"
  tags: [counter-example, self-protection, communication, spillover]

- id: ce18
  title: 自我感动替代因果充分性
  type: counter-example
  source_chapter: "BXSF-076-20240902 · 2024-09-02 · 远离这九个陷阱，你这辈子才会变好"
  source_quote: |
    这个世界遵循能量守恒定律，你首先要想到的是，你愿意付出的那一切，和你想要得到的那一切，是否等价?
  failure_mode: |
    相信自己的善意、牺牲或热爱足以改变对方和系统，却不检查投入是否能作用于真正的因果约束。
  mechanism: |
    付出带来强烈道德满足，容易让人把“我很真诚”错当成“这个手段有效”；角色、功能和结构约束并不因动机良善而消失。
  warning_signs:
    - 论证中心是“我已经付出很多”
    - 没有说明投入如何改变关键变量
    - 失败后持续追加同类牺牲
  bound_to:
    - "利益—成本—激励换位审计"
    - "信息差与事实/推断边界"
  tags: [counter-example, self-righteousness, causal-gap, sunk-cost]

- id: ce19
  title: 选择时拒绝承认取舍
  type: counter-example
  source_chapter: "BXSF-076-20240902 · 2024-09-02 · 远离这九个陷阱，你这辈子才会变好"
  source_quote: |
    决定不是你要什么,决定是一揽子决策，当你说出自己要什么的时候，就等于你同时说出了自己不要什么。
  failure_mode: |
    把选择理解成只增加好处、不放弃任何东西，导致迟迟不能落子，或落子后不断反悔。
  mechanism: |
    机会成本在决策当下不可见，损失厌恶却会放大被放弃选项；决策者因此想保留互相冲突的承诺。
  warning_signs:
    - 需求表里全是“既要又要”
    - 无法写出明确放弃项
    - 决定后持续按未选路径评价自己
  bound_to:
    - "终局倒推与隐藏选项构造"
    - "毁灭性风险与选择权保护"
  tags: [counter-example, tradeoff, opportunity-cost, indecision]

- id: ce20
  title: 把一时念头误认作长期理想
  type: counter-example
  source_chapter: "BXSF-077-20240920 · 2024-09-20 · 什么是天机？什么又是泄露天机"
  source_quote: |
    我们很多时候产生一个念头，就误把它当理想。其实这不是的，这是幻想。
  failure_mode: |
    把环境刺激下短暂出现的愿望当成稳定目标，在下一次群体压力或任务变化时又迅速切换方向。
  mechanism: |
    念头尚未经过持续行动、代价承担和环境反作用检验；外部“场力”比个人内部目标更强，因而轻易同化行为。
  warning_signs:
    - 目标随社交圈和热点频繁变化
    - 从未为目标持续付出代价
    - 无法说明即使无人赞同为何仍要做
  bound_to:
    - "终局倒推与隐藏选项构造"
    - "角色选择与叙事剪辑边界"
  tags: [counter-example, fantasy, identity, social-pressure]

- id: ce21
  title: 把意识到问题当成已经具备动作
  type: counter-example
  source_chapter: "BXSF-077-20240920 · 2024-09-20 · 什么是天机？什么又是泄露天机"
  source_quote: |
    你去健身房练拳击，教练会告诉你，意识到了和动作到了，是两码事。你意识到了是说你知道要出拳，可你到底能不能及时出拳，准确有力，这就是动作。
  failure_mode: |
    能清楚描述问题和正确方向，却没有把认知转化为及时、准确、可被他人接受的行动。
  mechanism: |
    理解产生“已经进步”的错觉，但动作还受技能、关系、时机和对方利益约束；没有实战反馈，知与行会长期脱节。
  warning_signs:
    - 同一问题反复讲得很清楚却从未改变
    - 行动请求只表达自身焦虑
    - 没有演练关键场景
  bound_to:
    - "能力—反馈周期匹配"
    - "预期价值呈现"
  tags: [counter-example, knowing-doing-gap, execution, practice]

- id: ce22
  title: 把基本面判断当成短期价格信号
  type: counter-example
  source_chapter: "BXSF-084-20250102 · 2025-01-02 · 2025，不要一年到头又白忙"
  source_quote: |
    他们很多时候，听过某个分析师的基本面分析，就误以为那是价格走势图，然后就拿着那个，当成自己做交易的依据去了。
  failure_mode: |
    混淆基本面、消息面、情绪和价格时点，把回答“长期价值如何”的分析直接用于“下个月怎么买卖”。
  mechanism: |
    不同层级变量作用于不同反馈周期；分类错误会让正确的长期分析产生错误的短期动作，随后又因价格波动否定全部分析。
  warning_signs:
    - 听完宏观观点立刻问买卖点
    - 无法区分价值、情绪和催化剂
    - 用一个时间尺度的证据回答另一个尺度的问题
  bound_to:
    - "周期—个体路径匹配"
    - "信息差与事实/推断边界"
  tags: [counter-example, category-error, fundamentals, time-horizon]

- id: ce23
  title: 零一思维抹掉所有中间态
  type: counter-example
  source_chapter: "BXSF-084-20250102 · 2025-01-02 · 2025，不要一年到头又白忙"
  source_quote: |
    01思维的人他误以为这个世界是没有中间态的，殊不知，人人天天都活在中间态里。
  failure_mode: |
    只接受彻底成功或彻底失败，因无法一步抵达终局而拒绝能延长时间、降低损失或获得下一次机会的过渡方案。
  mechanism: |
    二元分类降低思考成本，却把0到1之间的迭代路径全部删掉；行动门槛被抬到“不可能一次完成”的高度。
  warning_signs:
    - 方案被问成“能不能彻底解决”
    - 小幅改善被视为毫无意义
    - 等待完美条件才开始
  bound_to:
    - "能力—反馈周期匹配"
    - "终局倒推与隐藏选项构造"
  tags: [counter-example, binary-thinking, intermediate-state, iteration]

- id: ce24
  title: 复制成功路径却不追溯其生成条件
  type: counter-example
  source_chapter: "BXSF-085-20250116 · 2025-01-16 · 谁能给我的孩子一个出路"
  source_quote: |
    参考过去的路径依赖不是错，错的是，你在一味的依赖它之前，有没有研究过它的前世今生？
  failure_mode: |
    父母或后来者复制过去的专业、行业和城市选择，却不追溯当时的需求缺口、收入差和供给扩张条件。
  mechanism: |
    成功路径留下了容易观察的标签，真正产生超额回报的供需背景却已消失；复制标签只会进入拥挤后的赛道。
  warning_signs:
    - 用前一代职业名称代替需求分析
    - 只问“什么专业热门”
    - 不比较当年与当前的供需缺口
  bound_to:
    - "周期—个体路径匹配"
    - "可迁移能力与职业选择权"
  tags: [counter-example, path-copying, conditions, supply-demand]

- id: ce25
  title: 连续顺利触发热手加杠杆
  type: counter-example
  source_chapter: "BXSF-095-20250614 · 2025-06-14 · 普通的房子到底还有没有前途"
  source_quote: |
    这些人也是这么想的，想着趁自己手气旺，干脆加杠杆多买几套房，提前退休，将来收租。
  failure_mode: |
    因过去成长、加薪或投资连续顺利，就认为“手气旺”能够延续，借杠杆做一次决定命运的大额下注。
  mechanism: |
    个人顺利期常与共同周期重合；决策者把Beta收益归因于自身能力，并在风险最拥挤时扩大暴露。
  warning_signs:
    - 理由中出现“我一直都很顺”
    - 目标是一次下注提前退休
    - 身边人同时采用相同杠杆策略
  bound_to:
    - "毁灭性风险与选择权保护"
    - "交易系统与赌博分界"
  tags: [counter-example, hot-hand, leverage, attribution]

- id: ce26
  title: 被浮盈与踏空锚定后沦为赌徒
  type: counter-example
  source_chapter: "BXSF-101-20250907 · 2025-09-07 · 投资，我还来得及么？"
  source_quote: |
    大部分人在这样的事情重复很多次之后精神崩溃，退出市场，或者不甘心退出，实际上沦落为赌徒。
  failure_mode: |
    把未兑现的最高浮盈和卖出后的继续上涨当作“本来属于我的钱”，为追回参照点追高、扛亏和不断加码。
  mechanism: |
    锚定与损失厌恶把现实损益替换成相对峰值的心理损益；交易目标从执行系统变成消除后悔，行为随情绪漂移。
  warning_signs:
    - 反复计算“如果当时没卖会赚多少”
    - 把浮盈峰值计入个人资产
    - 重新入场的主要理由是不甘心踏空
  bound_to:
    - "交易系统与赌博分界"
    - "毁灭性风险与选择权保护"
  tags: [counter-example, anchoring, fear-of-missing-out, loss-aversion]

- id: ce27
  title: 什么都要等于主动寻找骗局
  type: counter-example
  source_chapter: "BXSF-108-20251221 · 2025-12-21 · 铁打的中产，流水的中产阶级"
  source_quote: |
    什么都要的潜台词，就是你找骗。一个说我要装修，我要装得好，还要省钱，还要不操心，那他在要求什么？他在要求被骗。
  failure_mode: |
    拒绝质量、价格、时间和责任之间的现实取舍，转而选择声称能同时满足全部要求的承诺者。
  mechanism: |
    不可能三角制造了“只有骗子愿意接单”的逆向选择；受骗者购买的是占便宜的感觉，真实成本随后以质量、风险或追加费用结算。
  warning_signs:
    - 需求里没有任何优先级
    - 报价明显低但承诺明显更多
    - 把风险与执行责任全部外包
  bound_to:
    - "利益—成本—激励换位审计"
    - "信息差与事实/推断边界"
  tags: [counter-example, impossible-triangle, adverse-selection, scam]

- id: ce28
  title: 把选择当成不改变自己的中奖彩票
  type: counter-example
  source_chapter: "BXSF-116-20260507 · 2026-05-07 · 财富大洗牌，我该选择，还是努力？"
  source_quote: |
    赌博是我不变，你注意，我不变，我没有任何变化，我就是那个满脑子浆糊，认知特 LOW 的人，但是，我赌对了，就能发财，这种想法，叫赌博。
  failure_mode: |
    把职业、投资或教育选择简化成“选中正确号码”，期待自己能力和认知不变也能因选项本身翻身。
  mechanism: |
    “选择大于努力”被误读成“选择覆盖努力”；注意力集中在选项名称，避开选择所依据的概率、能力、系统和后续执行。
  warning_signs:
    - 只问考研还是上岸、哪个公司能发财
    - 不讨论选择后的能力变化
    - 把正确路径描述为躺赢
  bound_to:
    - "周期—个体路径匹配"
    - "交易系统与赌博分界"
  tags: [counter-example, lottery-thinking, choice, self-change]

- id: ce29
  title: 用标准化二选一处理非标职业问题
  type: counter-example
  source_chapter: "BXSF-120-20260702 · 2026-07-02 · 为什么一眼看破事物本质的人，照样过不好这一生"
  source_quote: |
    你眼里只看到要接受，或者不要接受，那就是金融市场里赌徒的打法，那游戏就变成了你去赌，毒药还是清水。
  failure_mode: |
    面对包含具体老板、组织政治和个人能力的非标准职业选择，只比较“接受/不接受”的表面选项。
  mechanism: |
    二选一把利益点绑定在别人给出的棋盘上；隐藏条件、后续方案和棋盘外收益没有被构造，结果只能押注单一结局。
  warning_signs:
    - 问题被压成接受或拒绝
    - 信息主要来自公开话术
    - 成败完全取决于同一个决策者
  bound_to:
    - "终局倒推与隐藏选项构造"
    - "利益—成本—激励换位审计"
  tags: [counter-example, false-dilemma, nonstandard-decision, hidden-option]

- id: ce30
  title: 洞察不能转成价值，反而成为负担
  type: counter-example
  source_chapter: "BXSF-120-20260702 · 2026-07-02 · 为什么一眼看破事物本质的人，照样过不好这一生"
  source_quote: |
    因为到这个阶段，你只是看破了，可你看破了不等于你能提供价值。
  failure_mode: |
    以看穿问题、识别甩锅或证明别人错误为终点，却没有解决问题、完成交换或创造可被组织使用的结果。
  mechanism: |
    学校奖励识别标准答案，市场和组织奖励问题解决；单出“看破”既不产生收益，还可能暴露他人、破坏协作并被视为甩锅。
  warning_signs:
    - 输出只有问题归因，没有可执行解法
    - 以“我早看穿了”证明价值
    - 正确分析后组织处境反而更差
  bound_to:
    - "预期价值呈现"
    - "玩游戏/开发游戏跃迁评估"
  tags: [counter-example, insight-action-gap, value-creation, problem-solving]
