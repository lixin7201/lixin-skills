# Darwin Optimization Log

## Round 0 Baseline

- 问题：初版容易把半月谈平均成“央媒评论腔”。
- 处理：拆成账号基线 + 13 个文稿类型 + 聚合/个人署名线。
- keep：是。route correctness 提升。

## Round 1 Original Flavor

- 问题：标题和正文可能只学“警惕/莫让”的表面词。
- 处理：新增 `原味指纹.md` 和 `像不像对照样本.md`，强调机制拆解、事实边界和公共建议。
- keep：是。降低过拟合风险。

## Round 2 De-AI Preservation

- 问题：通用去 AI 可能删掉半月谈真实的政策/治理词。
- 处理：新增 `去AI味保真补丁.md`，明确半月谈 DNA 优先。
- keep：是。de-AI preservation pass。

## Round 3 Blind A/B Failure Analysis

- 真实结果：初次 full blind A/B 为 11 / 30 票、5 / 10 多数胜出。
- 主要问题：基层“精神溜号”、校园心理健康、文旅出圈、体育饭圈化、人格测试 5 类机制链不够细。
- 处理：补充类型 DNA 的具体机制词、边界词和标题禁忌。
- keep：是。targeted r3 复测 15 / 15 票胜出。

## Round 4 Final Full Blind A/B

- 真实结果：final r4 full blind A/B 为 26 / 30 票、9 / 10 多数胜出。
- keep：是。达到可调用 Skill 的出稿门槛。

## Round 5 H01 Boundary Patch

- 问题：品读散文弱素材容易第一人称代入，或把事实审查说明写进正文。
- 处理：补充规则：弱素材默认第三人称/观察者口吻；待核实集中放事实边界；成稿不得提 Skill、DNA、路由、训练材料。
- 验证：h01 internal-boundary smoke 中 forbidden hits = 0。
