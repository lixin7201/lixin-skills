# 阶段 1.5 三重验证通过单元

> 输入仅为 101 篇冻结训练语料及阶段 1 候选；holdout 与 OCR 隔离语料未参与。以下 11 个单元已通过 V1/V2/V3，仍须用户轻确认后才进入 RIA++ 技能构造。

## v01 · 可生存的重复决策系统

```yaml
id: v01
title: 可生存的重复决策系统
type: framework
merged_from: [f01, f02, f04, f05, p01, p02, p03, p04, p14, p18, p23]
V1_cross_domain:
  passed: true
  evidence:
    - "BXSF-001/BXSF-009：投资中的安全边际、次数和不出局"
    - "BXSF-031/BXSF-064：方向、点位、仓位与风险管理必须同时成立"
    - "BXSF-107/BXSF-116：从押宝转为自身可修正的交易系统"
    - "c07/c13/c14/c21：现场纠偏、跨域调试、模型失效和大量复盘"
V2_predictive_power:
  passed: true
  novel_question: "发现一个可能爆发的 AI 创业方向，是否应立即辞职全押？"
  derived_answer: "先定义单轮最大损失、现金跑道、最小可验证实验、退出条件和重复次数；若一次失败会永久出局，就缩小暴露或先不押。判断对象不是趋势猜得准不准，而是系统能否在猜错时继续学习。"
V3_exclusivity:
  passed: true
  why_not_common: "常识强调提高胜率；本单元把优先级反转为‘先保证能反复参与，再让优势在次数中显现’，并把点位、仓位、时间与模型适用域纳入同一系统。"
boundary_seeds: ["不为违法或伤害性试错提供容错", "一次性不可逆决策不能假装可重复", "规则只在适用域内有效"]
result: "进入阶段2"
```

## v02 · 周期—终局—选项倒推

```yaml
id: v02
title: 周期—终局—选项倒推
type: framework
merged_from: [f07, f08, f14, p13, p16, p17]
V1_cross_domain:
  passed: true
  evidence:
    - "BXSF-058/BXSF-066：从长期终局反推今天，并提前生成隐藏选项"
    - "BXSF-039/BXSF-120：个人、产品、行业、财富与历史周期不可混用"
    - "BXSF-066/BXSF-115：比较选择让路变宽还是变窄"
    - "c05/c12/c15/c18 与 ce03/ce09/ce14/ce24：人事窗口、关键人风险、周期绑定、旧路径复制"
V2_predictive_power:
  passed: true
  novel_question: "是否应把未来五年的学习全部押在当前最热门的大模型工具上？"
  derived_answer: "先分离工具、产品、行业与个人职业周期，再描述五至十年后仍可能存在的能力和位置；优先积累可迁移能力、现金流与关系，使工具替换后仍有选项，而不是预测某个工具必胜。"
V3_exclusivity:
  passed: true
  why_not_common: "不是泛泛长期主义，而是‘多周期分层—终局倒推—生成当下菜单外的 E 到 Z 选项—检查路变宽或变窄’的完整链条。"
boundary_seeds: ["终局是假设不是预言", "宏观趋势不能直接当短期买卖点", "新数据必须改变概率"]
result: "进入阶段2"
```

## v03 · 角色利益—成本—隐含信息审计

```yaml
id: v03
title: 角色利益—成本—隐含信息审计
type: framework
merged_from: [f09, f10, p10]
V1_cross_domain:
  passed: true
  evidence:
    - "BXSF-002：从执行者位置计算征收成本与额度"
    - "BXSF-015/BXSF-120：把未说出口的信息当待验证假设"
    - "BXSF-109：换位分析宏观行动者的目标与约束"
    - "c02/c03/c04/c10/c17 与 ce05/ce10/ce16/ce27：绩效时差、组织制衡、成本生态、联盟与逆向选择"
V2_predictive_power:
  passed: true
  novel_question: "合作方突然要求免费试点，是真重视合作还是在转嫁成本？"
  derived_answer: "分别列出双方目标、收益、执行成本、责任和可见信息；再查对方没说的预算、决策权与替代方案，用实际承诺和行为验证。未说出口只产生假设，不能直接推成恶意。"
V3_exclusivity:
  passed: true
  why_not_common: "常识只说换位思考；本单元要求把每个角色的利益、成本、权限、时间差和沉默信息写成可验证机制，并强制区分事实、推断与猜测。"
boundary_seeds: ["不把沉默解释成阴谋", "不靠刻板印象替代调查", "不把操纵和违规包装成博弈智慧"]
result: "进入阶段2"
```

## v04 · 事实边界下的未来价值与预期管理

```yaml
id: v04
title: 事实边界下的未来价值与预期管理
type: framework
merged_from: [f11, p07, p09]
V1_cross_domain:
  passed: true
  evidence:
    - "BXSF-003：评价与定价受未来能力预期影响"
    - "BXSF-082：关注‘还能做什么’而不只看已完成事项"
    - "BXSF-006/BXSF-115：对外呈现不能先骗过自己"
    - "c03/c09/c23/c24：升迁、威胁感管理、责任剪辑与定时邮件的收益和伦理风险"
V2_predictive_power:
  passed: true
  novel_question: "履历较弱但成长快的候选人，如何在谈薪时呈现价值？"
  derived_answer: "用已完成的小结果证明学习速度，再把下一阶段可解决的问题、验证节点和风险说清；呈现未来增量，不虚构经历，不把承诺写成事实。"
V3_exclusivity:
  passed: true
  why_not_common: "它把个人价值定义为可验证的未来效用折现，同时用‘骗谁都不能骗自己’限制预期管理，区别于普通包装或沟通技巧。"
boundary_seeds: ["禁止伪造经历和假信号", "人的尊严不等于市场定价", "承诺必须附验证条件"]
result: "进入阶段2"
```

## v05 · 生态位与价值链位置审计

```yaml
id: v05
title: 生态位与价值链位置审计
type: framework
merged_from: [f12, p19, p20, p32]
V1_cross_domain:
  passed: true
  evidence:
    - "BXSF-045/BXSF-120：行业重要不等于所在生态位有利润增长"
    - "BXSF-055：用谁能吞噬或替代自己界定生态位"
    - "BXSF-083/BXSF-080：比较相对稀缺优势并解释收益为何轮到自己"
    - "c01/c06/c08/c16/c20 与 ce05/ce11/ce14/ce24/ce30：技术生态、服务对象、岗位迁移、训练错位与价值输出"
V2_predictive_power:
  passed: true
  novel_question: "AI 正在自动化自己的岗位，是继续学工具还是换赛道？"
  derived_answer: "先定位岗位在价值链中的利润来源、替代压力、议价权和上游/下游关系；若位置持续被蚕食，就优先迁移到能调动资源、定义问题或承担结果的位置，而不是只在原位置提高工具熟练度。"
V3_exclusivity:
  passed: true
  why_not_common: "不是‘选好行业’，而是区分行业名称与具体价值链位置，并用谁供养、谁替代、门槛如何迁移和价值能否兑现来判断个人前途。"
boundary_seeds: ["不把人简单物化为利润点", "宏观需求不证明个人机会", "位置判断要用当前事实复核"]
result: "进入阶段2"
```

## v06 · 能力—需求—杠杆路径诊断

```yaml
id: v06
title: 能力—需求—杠杆路径诊断
type: framework
merged_from: [f16, f17, p11, p12, p24]
V1_cross_domain:
  passed: true
  evidence:
    - "BXSF-115：先有能力与需求，才轮到杠杆"
    - "BXSF-116：区分依赖窗口的 Beta 与依赖稀缺能力的 Alpha"
    - "BXSF-044/BXSF-058：先验证需求，再看自己够得着什么"
    - "c13/c16/c19 与 ce12/ce18/ce24/ce30：能力形成、目标错配、小原型容量和洞察—价值鸿沟"
V2_predictive_power:
  passed: true
  novel_question: "一个设计师想借 AI 产品赚钱，第一步应做课程、接单还是开发 SaaS？"
  derived_answer: "先验证能稳定交付什么和谁愿意付费，再判断收益来自短窗口还是长期稀缺能力；用自身够得着的小支点验证需求，能力与需求都成立后才加平台、团队或资金杠杆。"
V3_exclusivity:
  passed: true
  why_not_common: "常识常从‘找风口’或‘发挥优势’单点出发；本单元把能力、真实需求、杠杆顺序与 Alpha/Beta 的时间机制绑定，能指出当前到底缺哪一环。"
boundary_seeds: ["杠杆不能放大不存在的需求", "短窗口路线必须控制培养成本", "个人兴趣不等于市场需求"]
result: "进入阶段2"
```

## v07 · 根据地—探索钉子—增长率切换

```yaml
id: v07
title: 根据地—探索钉子—增长率切换
type: framework
merged_from: [f15, f25, p21, p22, p30, p31]
V1_cross_domain:
  passed: true
  evidence:
    - "BXSF-081：在多个方向提前埋低成本探索钉子"
    - "BXSF-115：转型是周期，不是旧路崩溃后的单一动作"
    - "BXSF-100/BXSF-120：环境变化时适应能力高于旧标准优秀"
    - "c18/c19/c20/c21/c26 与 ce01/ce07/ce08/ce14/ce24：资源预布、原型、组织阶段、复盘和短长反馈迁移"
V2_predictive_power:
  passed: true
  novel_question: "工作稳定但看到 AI 服务机会，何时应该转型？"
  derived_answer: "保留当前根据地和现金跑道，同时用低成本项目、客户连接和小额交付埋钉子；持续比较新旧路径的边际增长和真实反馈，新路径验证且旧路径增速下降后再加码，不把转型做成裸辞动作。"
V3_exclusivity:
  passed: true
  why_not_common: "它不是泛泛‘副业试水’，而是根据地、多个探索钉子、现金跑道、边际增长率和阶段切换共同构成的探索—利用机制。"
boundary_seeds: ["多钉子不等于无重点", "雇佣资源和知识产权必须合规", "高伤害领域不做快速试错"]
result: "进入阶段2"
```

## v08 · 遵守—打破—建立规则

```yaml
id: v08
title: 遵守—打破—建立规则
type: framework
merged_from: [f13, f19, p05, p06, p32]
V1_cross_domain:
  passed: true
  evidence:
    - "BXSF-077：游戏三阶段——遵守、打破、建立规则"
    - "BXSF-113：从跟规则走到建立自己的 rule"
    - "BXSF-016/BXSF-037：入局前先建立可检验规则"
    - "c01/c10/c13/c16/c22 与 ce01/ce04/ce15/ce16：标准控制、组织重构、跨域调试、训练错位与规则漂移"
V2_predictive_power:
  passed: true
  novel_question: "自由职业者被平台评分和低价竞争困住，下一步怎么办？"
  derived_answer: "先掌握平台规则并稳定交付，再识别可改变的参数和规则边界；积累直接客户、流程、产品或标准，逐步建立不完全依赖平台的游戏。打破规则只指改变合法参数，不指违规。"
V3_exclusivity:
  passed: true
  why_not_common: "不是普通系统思维，而是明确区分规则内优化、改变参数与建立评价/资源系统三种能力层级，并要求训练方式匹配目标角色。"
boundary_seeds: ["打破规则不等于违法或欺骗", "未掌握现有规则时不空谈造局", "建规则必须承担结果"]
result: "进入阶段2"
```

## v09 · 反馈机制—路径周期匹配

```yaml
id: v09
title: 反馈机制—路径周期匹配
type: framework
merged_from: [f06, p06, p27, p29]
V1_cross_domain:
  passed: true
  evidence:
    - "BXSF-081：组织替个人过滤了部分回报周期"
    - "BXSF-116：短、中、长反馈是不同机制，路径要尊重个体耐受度"
    - "BXSF-113/BXSF-118：学习必须连续知行合一"
    - "c13/c21/c22/c26 与 ce06/ce07/ce12/ce21/ce23：调试学习、复盘、最低充分路径和短反馈迁移"
V2_predictive_power:
  passed: true
  novel_question: "一个人连续放弃两次编程课程，第三次如何设计学习路径？"
  derived_answer: "先测他能承受多久没有可见结果，再选择能在一两周产出小工具的短反馈任务；让真实使用暴露问题，逐步延长项目周期，而不是再次报名半年后才见成果的完整体系。"
V3_exclusivity:
  passed: true
  why_not_common: "常识说坚持或拆小目标；本单元先诊断个体反馈耐受度，再匹配任务周期，并允许通过短反馈训练后迁移到长反馈。"
boundary_seeds: ["不把即时刺激当有效反馈", "长期目标仍需保留", "医学或心理问题不以路径设计代替专业帮助"]
result: "进入阶段2"
```

## v10 · “由东”瓶颈与单位时间配置

```yaml
id: v10
title: “由东”瓶颈与单位时间配置
type: framework
merged_from: [f21, f22, p08, p15, p25, p26]
V1_cross_domain:
  passed: true
  evidence:
    - "BXSF-108/BXSF-115：什么卡结果就先做什么，不按简单程度排序"
    - "BXSF-011/BXSF-054：用单位时间成本比较亲做、购买和放弃"
    - "BXSF-115：不可避免的时间可尝试合法复用"
    - "c06/c17/c22/c25 与 ce07/ce15/ce21/ce30：位置切换、责任接口、应试路径和时间私用边界"
V2_predictive_power:
  passed: true
  novel_question: "团队销量下降，负责人应先改官网、做内容还是找客户？"
  derived_answer: "先定义当前唯一结果和控制它的关键瓶颈；若瓶颈是未验证需求，就停止低价值美化，优先访谈和成交。再按自己的单位时间价值决定亲做、委托或删除，并在每阶段重新识别新的‘由东’。"
V3_exclusivity:
  passed: true
  why_not_common: "它把瓶颈称为当前结果真正‘由谁/由什么’控制的支点，再叠加自我计时计费和时间复用，不等于普通待办排序。"
boundary_seeds: ["不能侵占雇主时间和资源", "不能把所有关系货币化", "瓶颈变化后必须重排"]
result: "进入阶段2"
```

## v11 · “基于什么选择”三问审计

```yaml
id: v11
title: “基于什么选择”三问审计
type: framework
merged_from: [f23, p07, p28]
V1_cross_domain:
  passed: true
  evidence:
    - "BXSF-061：用该不该、能不能、爱不爱拆重大选择"
    - "BXSF-116：选择不是重点，基于什么选择才是重点"
    - "BXSF-006/BXSF-115：任何策略不能先骗过自己"
    - "c05/c11/c15/c26 与 ce12/ce19/ce20/ce28/ce29：窗口误判、不可复制、周期绑定、反馈性格和二选一陷阱"
V2_predictive_power:
  passed: true
  novel_question: "应接受高薪异地工作，还是留在本地照顾家庭？"
  derived_answer: "先列选择依据和证据；分别问责任与外部约束上该不该、能力与资源上能不能、过程与较坏结果是否真愿意承受。三者冲突时明确放弃什么，并用小验证补足未知，而不是寻找无代价答案。"
V3_exclusivity:
  passed: true
  why_not_common: "常见决策表只比较利弊；本单元把责任/约束、能力证据、过程意愿三层分开，并要求先暴露选择依据和自我欺骗。"
boundary_seeds: ["爱不爱不能覆盖责任与伤害", "不能替用户伪造价值排序", "材料不足时不替用户拍板"]
result: "进入阶段2"
```

## 汇总

- 通过：11。
- 三项全过：11/11。
- 进入阶段 2 前状态：等待用户轻确认。
