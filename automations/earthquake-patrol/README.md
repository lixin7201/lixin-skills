# 宜宾地震巡逻

零模型地震巡逻：读取公开地震源，识别宜宾境内新事件，生成震情正文和位置图，并通过已配置的发布身份发送。

## 安全边界

- 首次运行只建立当前事件基线，不补发历史事件。
- 只处理地点以 `四川宜宾市` 开头的新事件。
- 发帖前做本地事件去重和目标平台当日查重。
- 登录、身份、版块、截图或查重任一步不确定时停止发布。
- 项目不保存密码、Token、Cookie、浏览器登录态、运行数据库或截图。

## 本地配置

发布身份和版块不进入公开仓库。运行前自行设置：

```bash
export EARTHQUAKE_PUBLISH_VEST_ID='<vest-id>'
export EARTHQUAKE_PUBLISH_VEST_NAME='<vest-name>'
export EARTHQUAKE_PUBLISH_FORUM_ID='<forum-id>'
export EARTHQUAKE_PUBLISH_FORUM_NAME='<forum-name>'
```

千帆凭证仍从 `~/.qianfan-admin/config.json` 读取。微博登录态位于本地 `data/weibo-profile/`，本仓库不包含。

## 运行

```bash
python3 -m unittest discover -s tests -v
python3 earthquake_patrol.py check
python3 earthquake_patrol.py run
```

Wolfx 秒级源默认不发布；只有显式设置 `WOLFX_PUBLISH_ENABLED=1` 才进入发布路径：

```bash
npm install
node scripts/wolfx-listener.js --self-test
node scripts/wolfx-listener.js
```

OpenClaw 定时定义见 `../openclaw-cron/jobs.template.json`。
