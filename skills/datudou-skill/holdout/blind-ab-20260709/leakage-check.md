# Blind A/B Leakage Check

方法：生成完成后才读取 holdout originals；对 with-skill/baseline 输出与 8 篇 holdout 原文做去空白/标点后的最长公共连续片段检查。
阈值：>= 28 个连续中文/数字字符记为人工复核。

结果：PASS

| generated | closest original | longest common chars | note |
|---|---|---:|---|
| with-skill:h01 | 20260604_提前退休.md | 4 | ok |
| with-skill:h02 | 20260415_教育格局在发生巨变.md | 9 | ok |
| with-skill:h03 | 20260522_为什么年轻人不愿意留在北京了？.md | 14 | ok |
| with-skill:h04 | 20260526_终于有车牌了.md | 6 | ok |
| with-skill:h05 | 20260604_提前退休.md | 4 | ok |
| with-skill:h06 | 20260522_为什么年轻人不愿意留在北京了？.md | 5 | ok |
| with-skill:h07 | 20260609_写一篇育儿经，关于英语.md | 10 | ok |
| with-skill:h08 | 20260706_车市跟楼市现在有的一拼了.md | 12 | ok |
| with-skill:t20 | 20260522_为什么年轻人不愿意留在北京了？.md | 4 | ok |
| with-skill:t21 | 20260526_终于有车牌了.md | 5 | ok |
| with-skill:t22 | 20260522_为什么年轻人不愿意留在北京了？.md | 4 | ok |
| baseline:h01 | 20260327_夫妻之道.md | 4 | ok |
| baseline:h02 | 20260415_教育格局在发生巨变.md | 9 | ok |
| baseline:h03 | 20260522_为什么年轻人不愿意留在北京了？.md | 14 | ok |
| baseline:h04 | 20260526_终于有车牌了.md | 6 | ok |
| baseline:h05 | 20260522_为什么年轻人不愿意留在北京了？.md | 4 | ok |
| baseline:h06 | 20260608_最近三个月，三件反常识的事.md | 12 | ok |
| baseline:h07 | 20260609_写一篇育儿经，关于英语.md | 10 | ok |
| baseline:h08 | 20260706_车市跟楼市现在有的一拼了.md | 12 | ok |
| baseline:t20 | 20260706_车市跟楼市现在有的一拼了.md | 3 | ok |
| baseline:t21 | 20260604_提前退休.md | 6 | ok |
| baseline:t22 | 20260327_夫妻之道.md | 4 | ok |