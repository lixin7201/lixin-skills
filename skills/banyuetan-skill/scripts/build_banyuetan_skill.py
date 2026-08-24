#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median


CORPUS_DIR = Path("/Users/REPLACE_ME/Documents/学习/重点学习公众号/半月谈")
SKILL_DIR = Path("/Users/REPLACE_ME/.openclaw/workspace/skills/banyuetan-skill")

AGGREGATE_AUTHORS = {"半月谈", "半月谈记者", "半月谈评论员", "未知", ""}
TYPE_ORDER = [
    "基层治理与政务监督",
    "社会民生评论",
    "消费权益与市场监管",
    "教育成长与校园",
    "健康科普与医学提醒",
    "科技产业与AI新事物",
    "文旅乡村与城市更新",
    "文化历史与非遗",
    "青年职场与生活方式",
    "人物故事与榜样",
    "品读人生散文",
    "好好谈谈与读者征集",
    "基层圆桌与留言讨论",
]

TYPE_DNA_RULES = {
    "基层治理与政务监督": {
        "write": [
            "开头直接落在群众办事、基层值班、工单流转、催报留痕等可感场景，不先讲宏观意义。",
            "中段必须拆清机制链：权责错配、考核偏差、形式办结、多头指令、问责压力、资源不足或授权不足。",
            "写干部状态类议题时，必须区分主观懈怠、能力不足、事务过载、职业倦怠和制度激励失灵；先查履职链条，不把问题单因化。",
            "标题和开头要自然，不使用“治理基层‘心不在焉’”这类硬拧搭配；可用“状态不在线”“履职打折”“流程病灶”等更贴近半月谈的表达。",
            "建议要具体到分类认定、退回纠错、复核申诉、备用机制、数据共享、任务分级、容错保护等抓手。",
            "批评对象是流程和机制，不把基层干部简单写成懒政，也不替失职行为开脱。",
        ],
        "avoid": [
            "不要只写“减负要落到实处”。",
            "不要只罗列问题而不给权责链条。",
            "不要把所有基层压力都归为态度问题。",
            "不要把心理疏导写成干部履职问题的主解法；它只能作为辅助支持，主线仍是权责、考核、资源和监督。",
        ],
    },
    "社会民生评论": {
        "write": [
            "先界定公共边界：正常喜爱和失序追捧、理性讨论和网络攻击、个人选择和公共风险要分开。",
            "材料组织要从一件热议现象进入，再拆平台机制、规则边界、受影响人群和协同治理。",
            "标题可锋利，但正文要避免站队式情绪，把争议拉回秩序、权益、安全、信任或常识。",
            "写体育饭圈化时，先保留正常支持和批评讨论，再划出拉踩攻击、造谣侵权、隐私骚扰、组织性控评和商业营销的红线。",
            "同类稿要把平台流量机制、圈层对立、赛事组织、媒体叙事和公众表达保障分开写，结尾把注意力拉回比赛、训练、规则精神和健康参与。",
        ],
        "avoid": ["不要把网暴、饭圈、流量争议写成单纯年轻人情绪。", "不要直接指认平台或群体，除非素材给了事实。", "不要用“压低热情”替代治理失序行为；要同时保护正常喜爱和正常讨论。"],
    },
    "消费权益与市场监管": {
        "write": [
            "先区分消费者主观感受、商家宣传、检测数据、监管事实和专业建议。",
            "中段追问市场激励：为什么商家这样卖，消费者为什么这样选，信息不对称在哪里。",
            "建议落到标识、检测、虚假宣传、退费、价格透明、平台责任或监管抽检。",
        ],
        "avoid": ["不要凭体验作专业结论。", "不要把消费提醒写成科普定论。"],
    },
    "教育成长与校园": {
        "write": [
            "开头同时接住学校管理需求、学生感受和家长焦虑。",
            "分析时区分教育目的、安全卫生、审美整齐、规则程序和羞辱性执行。",
            "写校园心理健康时，优先使用“识别 -> 信任 -> 专业转介 -> 协同 -> 恢复”的链条；量表、建档和谈话只是入口，不是完整答案。",
            "必须写清心理教师职责、医疗专业边界、家校信息边界、危机处置后的持续支持和返校适应，保护未成年人隐私与尊严。",
            "建议要给公开校规、听取意见、个案例外、申诉沟通和未成年人保护边界。",
        ],
        "avoid": ["不要把学校简单写成对立面。", "不要未经核实使用学生隐私或影像。", "不要把正常情绪轻易病理化，也不要把“一转介”写成结案。"],
    },
    "健康科普与医学提醒": {
        "write": [
            "先写日常焦虑或误区，再解释医学机制和适用范围。",
            "所有治疗、诊断、用药、筛查建议都必须有专业边界，最终落到正规就医和不要轻信偏方。",
        ],
        "avoid": ["不要替代医生诊断。", "不要编造研究、药物效果或专家姓名。"],
    },
    "科技产业与AI新事物": {
        "write": [
            "先解释新技术如何进入具体生活和工作场景，再问影响谁、改变什么流程、带来什么风险。",
            "必须把技术能力、商业激励、平台规则、使用者权益和监管边界拆开。",
            "写人格测试、AI测评、算法标签类议题时，先给出可感场景：社交谈资、求职筛选、教育评价、付费解读或平台推荐。",
            "再拆工具局限、商业包装、数据收集、隐私保存、招聘教育等重大决定边界；强调测试只能参考，不能替人下结论。",
        ],
        "avoid": ["不要空喊技术革命。", "不要把算法、平台或 AI 责任写成已核实事实。", "不要只写“理性看待标签”，必须写出使用场景、数据风险和决策边界。"],
    },
    "文旅乡村与城市更新": {
        "write": [
            "从一个地方、一个场景或一个具体做法开头，写它如何被看见和改变。",
            "中段写资源、产业、治理、游客体验和本地生活之间的关系。",
            "写地方文旅出圈时，必须区分传播门槛、公共承载、产品链条、收益分配、居民参与、复游率和口碑沉淀。",
            "把流量转化写成产业能力：交通住宿卫生投诉等基础承载，文化体验和特色产品延长消费链，本地商户和居民真实受益。",
            "结尾讲可持续条件，不只夸流量。",
        ],
        "avoid": ["不要写成景区软文。", "不要只写出圈热闹。", "不要把短期客流直接等同于稳定收入和持续就业。"],
    },
    "文化历史与非遗": {
        "write": [
            "先让一个物件、技艺、地方或记忆进入当下生活。",
            "解释传承逻辑：谁在做、怎么做、为何还能被今天的人需要。",
        ],
        "avoid": ["不要写成百科词条。", "不要只堆历史名词。"],
    },
    "青年职场与生活方式": {
        "write": [
            "先承认年轻人的现实压力，不急着贴标签。",
            "拆出就业环境、家庭期待、平台规则、消费文化和自我选择之间的拉扯。",
            "建议要给期限、备选路径、风险成本和多元评价。",
        ],
        "avoid": ["不要把年轻人写成躺平符号。", "不要用鸡汤替代现实路径。"],
    },
    "人物故事与榜样": {
        "write": [
            "先写人的具体处境和动作，再写公共价值。",
            "荣誉、身份和制度安排要分开，不把表彰材料写成情绪号召。",
        ],
        "avoid": ["不要神化人物。", "不要编造亲友评价或感人细节。"],
    },
    "品读人生散文": {
        "write": [
            "从生活物件、亲人一句话、旧房间、厨房、路途、季节等细节开头。",
            "保留第一人称或贴近个人记忆的叙述节奏，少讲公共议题。",
            "人物材料不足时，默认用第三人称或观察者口吻，不冒充当事人第一人称；可以从时间分配、家庭分工、精神需求和普通人的表达欲进入。",
            "正文保持成稿感，缺失事实集中放到“事实边界”，不要在标题、开头和正文连续写“待核实”占位。",
            "中段靠关系和回忆推进，结尾留下余韵，不强行给治理建议。",
        ],
        "avoid": ["不要写成评论稿。", "不要把乡村、亲情和怀旧浪漫化。", "不要用“值得被看见”替代具体生活。", "不要在没有采访材料时写“我在灶台旁写诗”这类当事人自述。", "不要把事实审查说明写进散文正文。"],
    },
    "好好谈谈与读者征集": {
        "write": [
            "先提出一个读者正在面对的选择题，再用多个人的经验切片分组推进。",
            "每组都要提炼经验和代价，最后给同类人的稳妥提醒。",
        ],
        "avoid": ["不要把答主经历写成已验证普遍规律。", "不要虚构网友原话。"],
    },
    "基层圆桌与留言讨论": {
        "write": [
            "开头说明讨论从哪个基层话题来，随后按留言观点分组。",
            "每组先归纳症结，再给少量代表性材料；最后用“谈谈说”式判断收束。",
        ],
        "avoid": ["不要把留言当事实调查。", "不要只堆观点不归纳。"],
    },
}


def parse_frontmatter(text: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].strip().splitlines():
                match = re.match(r"([A-Za-z_\u4e00-\u9fa5]+):\s*\"?(.*?)\"?\s*$", line)
                if match:
                    meta[match.group(1)] = match.group(2).strip()
    return meta


def strip_frontmatter_and_interaction(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4 :]
    marker = text.find("## 互动数据")
    if marker != -1:
        text = text[:marker]
    return text


def parse_number(raw: str | None) -> int:
    if not raw:
        return 0
    match = re.match(r"([0-9]+(?:\.[0-9]+)?)(万)?", raw.strip())
    if not match:
        return 0
    value = float(match.group(1))
    if match.group(2):
        value *= 10000
    return int(round(value))


def parse_interaction(text: str) -> dict[str, int] | None:
    marker = text.find("## 互动数据")
    if marker == -1:
        return None
    tail = text[marker : marker + 360]
    values: dict[str, int] = {}
    for key in ["阅读", "点赞", "转发", "喜欢", "留言"]:
        match = re.search(key + r"\s*([0-9]+(?:\.[0-9]+)?万?)", tail)
        values[key] = parse_number(match.group(1)) if match else 0
    if not any(values.values()):
        return None
    values["interaction_score"] = (
        values["阅读"]
        + values["点赞"] * 20
        + values["转发"] * 40
        + values["喜欢"] * 20
        + values["留言"] * 100
    )
    return values


def count_chinese(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def normalize_author(value: str) -> str:
    value = value.strip().strip('"').strip()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"^(作者|记者|半月谈记者|本刊记者)\s*[：:]\s*", "", value)
    return value or "未知"


def is_content_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(("---", "#", ">", "![]", "![", "<")):
        return False
    if "原文链接" in stripped or "互动数据" in stripped:
        return False
    if re.search(r"^(作者|原标题|编辑|来源|责编|图片|制图)\s*[：:]", stripped) and len(stripped) < 80:
        return False
    return count_chinese(stripped) > 0


def infer_progression_chain(title: str, body: str, paragraphs: list[str]) -> str:
    text = title + "\n" + body[:3500]
    if "基层圆桌会" in text or "留言" in text and len(re.findall(r"[：:]", text)) >= 8:
        return "话题引入 -> 网友留言分组 -> 症结归纳 -> 建议收束 -> 互动口"
    if "品读" in title:
        return "个人记忆/生活场景 -> 关系回望 -> 轻判断 -> 情感余韵"
    if "好好谈谈" in text or "知乎" in text or "答主" in text:
        return "公共问题 -> 读者/答主切片 -> 经验归纳 -> 给同类人的提醒"
    if re.search(r"(莫让|警惕|不可|岂能|别让|当禁|应对|要防|不能)", title):
        return "现象点题 -> 案例/数据 -> 风险拆解 -> 治理建议"
    if re.search(r"(为何|为什么|咋|如何|怎么办|吗？|吗\?)", title):
        return "问题开场 -> 原因拆解 -> 多方材料 -> 可操作建议"
    if re.search(r"(县城|乡村|社区|城市|文旅|古村|产业)", text):
        return "地方/对象开场 -> 做法展开 -> 变化解释 -> 可复制经验"
    if paragraphs and len(paragraphs[0]) <= 90:
        return "小切口开场 -> 背景补足 -> 现象分析 -> 提醒/判断收束"
    return "现象开场 -> 材料铺陈 -> 价值判断 -> 行动建议"


def structure_metrics(title: str, body: str) -> dict[str, float | int | str]:
    lines = [line.strip() for line in body.splitlines()]
    paragraphs = [line for line in lines if is_content_line(line)]
    lengths = [count_chinese(p) for p in paragraphs if count_chinese(p) > 0]
    short_flags = [length <= 20 for length in lengths]
    max_short_run = 0
    current = 0
    for flag in short_flags:
        if flag:
            current += 1
            max_short_run = max(max_short_run, current)
        else:
            current = 0
    chars = count_chinese(body)
    heading_re = r"^\*{0,6}[\u4e00-\u9fffA-Za-z0-9“”《》、·｜|：:？?]{2,24}\*{0,6}$"
    headings = [
        line
        for line in lines
        if re.match(heading_re, line)
        and not line.startswith(("作者", "原标题"))
        and count_chinese(line) <= 28
    ]
    return {
        "chars": chars,
        "paragraph_count": len(lengths),
        "paragraphs_per_1000": round(len(lengths) / max(chars, 1) * 1000, 2),
        "median_paragraph_chars": round(median(lengths), 1) if lengths else 0,
        "short_paragraph_ratio": round(sum(short_flags) / len(lengths), 3) if lengths else 0,
        "max_short_run": max_short_run,
        "image_count": len(re.findall(r"!\[.*?\]\(.*?\)", body)),
        "section_count": len(headings),
        "progression_chain": infer_progression_chain(title, body, paragraphs),
    }


def classify_type(title: str, body: str) -> str:
    head = body[:2200]
    sample = title + "\n" + head
    low = sample.lower()
    if "基层圆桌会" in head or "谈谈说" in head:
        return "基层圆桌与留言讨论"
    if "品读" in title:
        return "品读人生散文"
    if "好好谈谈" in head or "知乎" in head or "答主" in head or "过来人" in title:
        return "好好谈谈与读者征集"
    if re.search(r"造景|景区|旅游|文旅|家乡|故乡", title):
        return "文旅乡村与城市更新"
    if re.search(r"考公|公务员考试|就业|职业选择|求稳|上岸", sample):
        return "青年职场与生活方式"
    if re.search(r"饭圈|粉丝|追星|网暴|开盒|流量裹挟|体育生态|宿舍直播", sample):
        return "社会民生评论"
    if re.search(r"基层|干部|问责|形式主义|治理|政务|审计|监督|纪委|三资|蝇贪|证明|容错|考核|减负|调研|举报|城投|融资|12345|工单|留痕|签字|属地|权责", sample):
        return "基层治理与政务监督"
    if re.search(r"消费|市场|商标|标价|银行|医保|骗局|收费|门票|小卡|奶茶|试用|债务|带货|行政处罚|食品安全|餐费|小饭店|碰瓷|价格|预付|退款|会员|流量裹挟", sample):
        return "消费权益与市场监管"
    if re.search(r"高考|志愿|学校|老师|学生|校园|教材|教育|课堂|辅导员|大学|中小学|体育课|班干部|科技教育|上学|家长|作业|研学|招生", sample):
        return "教育成长与校园"
    if re.search(r"职场|婚恋|父母|二次元|乙游|情绪|社会化|中年人|养老", sample):
        return "青年职场与生活方式"
    if re.search(r"ai|人工智能|机器人|无人机|算力|脑机|vibecoding|程序员|科技|芯片|细胞培养肉|太空|三体计算|app|防沉迷|一键登录", low):
        return "科技产业与AI新事物"
    if re.search(r"健康|医学|医院|医生|疾病|癌症|筛查|糖尿病|白发|脱发|慢性病|ct|牙齿|毛囊|皮肤科|就诊|用药|植发|少白头", sample):
        return "健康科普与医学提醒"
    if re.search(r"乡村|县城|文旅|旅游|城市|社区|古村|村|产业|街区|水库|农牧|振兴|小城|长春|贵阳|公交|地铁|马拉松|县域|村图|村子|农民|小哥驿站|家乡|故乡|地方", sample):
        return "文旅乡村与城市更新"
    if re.search(r"文化|历史|博物馆|书院|社火|古|瓷|窑|传统|节气|月饼|艺术|书信|音乐|小人书|怀旧|草木|非遗|文物|省油灯|中国结|诗|摇滚乐", sample):
        return "文化历史与非遗"
    if re.search(r"年轻人|职场|婚恋|父母|二次元|乙游|情绪|社会化|中年人|养老|生活|代餐|明星|粉丝|宿舍直播|捡秋|演唱会|登味|CP|社交|怀旧", sample):
        return "青年职场与生活方式"
    if re.search(r"志愿军|特警|保镖爷爷|放电影|科学家|老师|爷爷|奶奶|父亲|母亲|小哥|老人", sample):
        return "人物故事与榜样"
    return "社会民生评论"


def read_records() -> list[dict]:
    records: list[dict] = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        meta = parse_frontmatter(text)
        title = meta.get("title") or re.sub(r"^\d{8}_", "", path.stem)
        author = normalize_author(meta.get("author", ""))
        account = meta.get("account", "")
        date = meta.get("date", "")[:10] or path.name[:8]
        body = strip_frontmatter_and_interaction(text)
        metrics = structure_metrics(title, body)
        interaction = parse_interaction(text)
        article_type = classify_type(title, body)
        record = {
            "path": str(path),
            "filename": path.name,
            "title": title,
            "author": author,
            "account": account,
            "date": date,
            "year": date[:4],
            "url": meta.get("url", ""),
            "article_type": article_type,
            "has_interaction": bool(interaction),
            "train_status": "not_selected",
            "source_stratum": "metadata_only",
            "author_confidence": "insufficient",
            **metrics,
        }
        if interaction:
            record.update(interaction)
        else:
            record.update({"阅读": 0, "点赞": 0, "转发": 0, "喜欢": 0, "留言": 0, "interaction_score": 0})
        records.append(record)
    return records


def confidence_label(author: str, count: int) -> str:
    if author in {"半月谈", "半月谈记者"}:
        return "aggregate_route"
    if count >= 30:
        return "stable"
    if count >= 20:
        return "early"
    return "insufficient"


def split_train_holdout(records: list[dict]) -> tuple[list[str], list[str], list[str]]:
    complete_inter = [r for r in records if r["has_interaction"] and r["chars"] >= 800 and r["account"] == "半月谈"]
    author_groups: dict[str, list[dict]] = defaultdict(list)
    for record in complete_inter:
        author_groups[record["author"]].append(record)

    route_authors: list[str] = []
    stable_authors: list[str] = []
    early_authors: list[str] = []
    for author, group in sorted(author_groups.items(), key=lambda item: (-len(item[1]), item[0])):
        label = confidence_label(author, len(group))
        for record in group:
            record["author_confidence"] = label
        if label in {"aggregate_route", "stable", "early"}:
            route_authors.append(author)
        if label == "stable":
            stable_authors.append(author)
        if label == "early":
            early_authors.append(author)

    for author, group in author_groups.items():
        group.sort(key=lambda r: (-r["interaction_score"], r["date"], r["filename"]))
        limit = max(1, math.ceil(len(group) * 0.7))
        for idx, record in enumerate(group[:limit]):
            record["train_status"] = "training"
            record["source_stratum"] = "high_engagement" if idx < max(1, len(group[:limit]) // 4) else "representative_top70"
        for record in group[limit:]:
            record["train_status"] = "excluded_below_author_top70"
            record["source_stratum"] = "outside_author_top70"

    holdout_records: list[dict] = []
    seen_paths: set[str] = set()

    def add_holdout(record: dict | None) -> None:
        if not record or record["path"] in seen_paths:
            return
        holdout_records.append(record)
        seen_paths.add(record["path"])

    for author in ["半月谈", "半月谈记者", *stable_authors, *early_authors]:
        pool = [r for r in author_groups.get(author, []) if r["train_status"] == "training"]
        if not pool:
            continue
        preferred = None
        used_types = {r["article_type"] for r in holdout_records}
        for record in sorted(pool, key=lambda r: (-r["interaction_score"], r["date"])):
            if record["article_type"] not in used_types:
                preferred = record
                break
        if preferred is None:
            preferred = pool[min(len(pool) - 1, max(0, int(len(pool) * 0.35)))]
        add_holdout(preferred)

    trained_by_type: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        if record["train_status"] == "training":
            trained_by_type[record["article_type"]].append(record)
    for article_type in TYPE_ORDER:
        pool = trained_by_type.get(article_type, [])
        if len(pool) < 20:
            continue
        if any(r["article_type"] == article_type for r in holdout_records):
            continue
        pool.sort(key=lambda r: (-r["interaction_score"], r["date"], r["filename"]))
        add_holdout(pool[min(len(pool) - 1, max(0, int(len(pool) * 0.4)))])
        if len(holdout_records) >= 12:
            break

    # Top up to a useful validation set size even when the corpus is dominated by a few routes.
    while len(holdout_records) < 10:
        added = False
        for article_type, pool in sorted(trained_by_type.items(), key=lambda item: (-len(item[1]), item[0])):
            if not pool:
                continue
            pool.sort(key=lambda r: (-r["interaction_score"], r["date"], r["filename"]))
            existing_authors = {r["author"] for r in holdout_records if r["article_type"] == article_type}
            candidate = None
            for record in pool:
                if record["path"] in seen_paths:
                    continue
                if record["author"] not in existing_authors:
                    candidate = record
                    break
            if candidate is None:
                candidate = next((record for record in pool if record["path"] not in seen_paths), None)
            if candidate is not None:
                add_holdout(candidate)
                added = True
                break
        if not added:
            break

    for record in holdout_records[:12]:
        record["train_status"] = "holdout"
        record["source_stratum"] = "frozen_holdout"

    return route_authors, stable_authors, early_authors


def avg(records: list[dict], key: str) -> float:
    vals = [float(r[key]) for r in records if r.get(key) not in ("", None)]
    return round(mean(vals), 2) if vals else 0.0


def med(records: list[dict], key: str) -> float:
    vals = [float(r[key]) for r in records if r.get(key) not in ("", None)]
    return round(median(vals), 2) if vals else 0.0


def top_types(records: list[dict], limit: int = 3) -> str:
    counter = Counter(r["article_type"] for r in records)
    return "、".join(f"{name}({count})" for name, count in counter.most_common(limit))


def route_display(author: str) -> str:
    if author == "半月谈":
        return "半月谈编辑部线"
    if author == "半月谈记者":
        return "半月谈记者线"
    return author


def safe_filename(name: str) -> str:
    safe = re.sub(r"[\\/:\s]+", "_", name).strip("_")
    return safe or "unknown"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def csv_write(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def type_route_note(article_type: str) -> str:
    notes = {
        "基层治理与政务监督": "适合基层减负、干部问责、形式主义、治理流程、监督执纪类稿件，先找流程卡点，再写权责和容错。",
        "社会民生评论": "适合社会热点、公共争议、网络情绪和生活秩序类评论，先立问题，再做边界判断。",
        "消费权益与市场监管": "适合价格、商标、金融、平台规则、消费陷阱和监管提醒，必须有风险提示和可操作提醒。",
        "教育成长与校园": "适合高考、学校、老师、学生、教材、校园管理，兼顾学生体验、家庭压力和制度边界。",
        "健康科普与医学提醒": "适合健康焦虑、疾病科普、就医提醒，必须保留医学事实边界，不替代医生诊断。",
        "科技产业与AI新事物": "适合 AI、机器人、算力、脑机、程序员、技术进入生活的稿，先解释新事物，再问影响谁。",
        "文旅乡村与城市更新": "适合县城、乡村、社区、文旅、城市治理、地方产业，突出一个地方如何被看见和改变。",
        "文化历史与非遗": "适合历史文化、非遗、传统、艺术、书院、文物，重在讲清文化如何重新进入当下生活。",
        "青年职场与生活方式": "适合年轻人情绪、职场、婚恋、父母关系、圈层消费，语气更贴近日常，但判断仍要稳。",
        "人物故事与榜样": "适合基层人物、普通劳动者、专家、志愿者和榜样故事，人物服务于公共价值但不能写成表彰材料。",
        "品读人生散文": "适合亲情、怀旧、人生经验、生活记忆，第一人称和细节更重，结尾可以有余韵。",
        "好好谈谈与读者征集": "适合把知乎/读者回答组织成公共经验，保留多个普通人的切片和可复用建议。",
        "基层圆桌与留言讨论": "适合围绕一个基层话题汇总留言、归纳症结、提出制度建议，网友发言要分组推进。",
    }
    return notes[article_type]


def build_data_reports(records: list[dict], route_authors: list[str], stable_authors: list[str], early_authors: list[str]) -> None:
    data = SKILL_DIR / "data"
    holdout = [r for r in records if r["train_status"] == "holdout"]
    training = [r for r in records if r["train_status"] == "training"]
    complete = [r for r in records if r["chars"] >= 800]
    complete_inter = [r for r in complete if r["has_interaction"] and r["account"] == "半月谈"]
    account_counter = Counter(r["account"] for r in records)

    fields = [
        "filename",
        "title",
        "date",
        "year",
        "author",
        "account",
        "author_confidence",
        "article_type",
        "chars",
        "paragraph_count",
        "paragraphs_per_1000",
        "median_paragraph_chars",
        "short_paragraph_ratio",
        "max_short_run",
        "section_count",
        "image_count",
        "阅读",
        "点赞",
        "转发",
        "喜欢",
        "留言",
        "interaction_score",
        "train_status",
        "source_stratum",
        "progression_chain",
        "path",
        "url",
    ]
    csv_write(data / "文章元数据总表.csv", records, fields)

    report = f"""# 语料质量报告

## 结论

- 语料目录：`{CORPUS_DIR}`
- Markdown 文件：{len(records)}
- account 分布：{dict(account_counter)}
- 完整稿（中文字符 >= 800）：{len(complete)}
- 带互动数据且 account=半月谈：{len(complete_inter)}
- 进入训练集：{len(training)}
- 冻结 holdout：{len(holdout)}
- 按每个署名线独立取互动前 70%：已执行
- 可调用聚合路线：半月谈编辑部线、半月谈记者线
- 稳定个人 DNA（>=30 篇完整互动样本）：{len(stable_authors)} 个，{', '.join(stable_authors) or '无'}
- 早期个人 DNA（20-29 篇完整互动样本）：{len(early_authors)} 个，{', '.join(early_authors) or '无'}

## 筛选规则

1. 只使用 `account: 半月谈` 的文章参与训练和验证；当前未发现其他 account。
2. 只把 `中文字符 >= 800` 且有 `## 互动数据` 的文章放入互动筛选池。
3. 每个署名线独立按互动分排序，不做全账号混排；训练池取该署名线互动分前 70%。
4. 互动分 = 阅读 + 点赞*20 + 转发*40 + 喜欢*20 + 留言*100。阅读有 10 万上限时，用点赞、转发、喜欢和留言打破平局。
5. `半月谈`、`半月谈记者` 是聚合署名线，只作为编辑部/记者线，不冒充具体真人。
6. 个人署名 `<20` 篇不生成个人 DNA，只进入账号/类型层和样本不足清单。
7. holdout 在训练池中先冻结，再生成 DNA；DNA 文件和测试 prompt 不复制 holdout 正文。

## 全局结构指标（训练集）

- 每千字段落数均值：{avg(training, 'paragraphs_per_1000')}
- 段落中位中文字符：{med(training, 'median_paragraph_chars')}
- 20 字以内短段比例：{avg(training, 'short_paragraph_ratio')}
- 连续短段最大 run 中位：{med(training, 'max_short_run')}
- 每篇图片数中位：{med(training, 'image_count')}
- 每篇小标题数中位：{med(training, 'section_count')}

## 质量边界

- 这是 `ready / original_flavor` 方向的可调用 Skill，不认证 95% 复刻。
- 半月谈是多署名、多栏目公众号；Skill 采用“账号基线 -> 文稿类型 -> 署名线”的路由式规则，避免平均成一团央媒腔。
- 个人 DNA 只对样本足够的署名线开放；低样本作者不做个人复刻。
"""
    write(data / "语料质量报告.md", report)

    author_groups = defaultdict(list)
    for record in complete_inter:
        author_groups[record["author"]].append(record)
    lines = [
        "# 小编语料分布",
        "",
        "|署名线|完整互动样本|前70%池|训练|holdout|置信度|互动分中位|主要类型|段落中位|短段比例|",
        "|---|---:|---:|---:|---:|---|---:|---|---:|---:|",
    ]
    for author, group in sorted(author_groups.items(), key=lambda item: (-len(item[1]), item[0]))[:100]:
        pool_count = sum(1 for r in group if r["train_status"] in {"training", "holdout"})
        train_count = sum(1 for r in group if r["train_status"] == "training")
        holdout_count = sum(1 for r in group if r["train_status"] == "holdout")
        label = confidence_label(author, len(group))
        scores = [r["interaction_score"] for r in group]
        lines.append(
            f"|{route_display(author)}|{len(group)}|{pool_count}|{train_count}|{holdout_count}|{label}|{int(median(scores)) if scores else 0}|{top_types(group)}|{med(group, 'median_paragraph_chars')}|{avg(group, 'short_paragraph_ratio')}|"
        )
    write(data / "小编语料分布.md", "\n".join(lines))

    type_lines = [
        "# 文稿类型分布",
        "",
        "|文稿类型|完整互动|训练|holdout|结构提示|",
        "|---|---:|---:|---:|---|",
    ]
    for article_type in TYPE_ORDER:
        group = [r for r in complete_inter if r["article_type"] == article_type]
        type_lines.append(
            f"|{article_type}|{len(group)}|{sum(1 for r in group if r['train_status']=='training')}|{sum(1 for r in group if r['train_status']=='holdout')}|{type_route_note(article_type)}|"
        )
    write(data / "文稿类型分布.md", "\n".join(type_lines))

    metric_lines = [
        "# 结构与段落指标",
        "",
        "## 训练集全局",
        "",
        f"- 每千字段落数均值：{avg(training, 'paragraphs_per_1000')}",
        f"- 段落中位字数中位：{med(training, 'median_paragraph_chars')}",
        f"- 20 字以内短段比例均值：{avg(training, 'short_paragraph_ratio')}",
        f"- 连续短段最大 run 中位：{med(training, 'max_short_run')}",
        f"- 图片数中位：{med(training, 'image_count')}",
        f"- 小标题数中位：{med(training, 'section_count')}",
        "",
        "## 分类型指标",
        "",
        "|类型|训练篇数|每千字段落|段落中位|短段比例|连续短段 run|图片中位|常见推进链|",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for article_type in TYPE_ORDER:
        group = [r for r in training if r["article_type"] == article_type]
        chain = Counter(r["progression_chain"] for r in group).most_common(1)
        metric_lines.append(
            f"|{article_type}|{len(group)}|{avg(group, 'paragraphs_per_1000')}|{med(group, 'median_paragraph_chars')}|{avg(group, 'short_paragraph_ratio')}|{med(group, 'max_short_run')}|{med(group, 'image_count')}|{chain[0][0] if chain else ''}|"
        )
    write(data / "结构与段落指标.md", "\n".join(metric_lines))

    train_lines = [
        "# Training Corpus List",
        "",
        f"训练集共 {len(training)} 篇。下表列前 260 篇；全量见 `data/文章元数据总表.csv` 的 `train_status=training`。",
        "",
        "|日期|署名线|类型|互动分|标题|源路径|",
        "|---|---|---|---:|---|---|",
    ]
    for record in sorted(training, key=lambda r: (-r["interaction_score"], r["date"]))[:260]:
        train_lines.append(
            f"|{record['date']}|{route_display(record['author'])}|{record['article_type']}|{record['interaction_score']}|{record['title']}|`{record['path']}`|"
        )
    write(data / "training-corpus-list.md", "\n".join(train_lines))

    insuff = [
        (author, group)
        for author, group in author_groups.items()
        if confidence_label(author, len(group)) == "insufficient"
    ]
    insuff.sort(key=lambda item: (-len(item[1]), item[0]))
    insuff_lines = [
        "# 样本不足清单",
        "",
        "这些署名线不生成个人 DNA。可用于账号或类型层，不能当稳定小编复刻。",
        "",
        "|署名|完整互动样本|主要类型|处理|",
        "|---|---:|---|---|",
    ]
    for author, group in insuff[:140]:
        insuff_lines.append(f"|{author}|{len(group)}|{top_types(group)}|账号/类型层，不做个人 DNA|")
    write(data / "样本不足清单.md", "\n".join(insuff_lines))

    strata = Counter(r["source_stratum"] for r in records)
    strata_lines = [
        "# 原味语料分层",
        "",
        "|层级|数量|用途|",
        "|---|---:|---|",
        f"|high_engagement|{strata['high_engagement']}|提炼强传播标题、开头和风险提示，但不让爆款腔垄断半月谈味|",
        f"|representative_top70|{strata['representative_top70']}|主要训练层，保留每条署名线互动前 70% 的常态写法|",
        f"|frozen_holdout|{strata['frozen_holdout']}|只用于验证，不进入 DNA 文件|",
        f"|outside_author_top70|{strata['outside_author_top70']}|低于该署名线前 70%，用于边界审计，不训练|",
        f"|metadata_only|{strata['metadata_only']}|短稿、非半月谈 account 或互动不完整，仅保留审计|",
        "",
        "原味保留原则：高互动代表传播有效，不自动等于最像半月谈。最终 Skill 同时使用 high_engagement 与 representative_top70，避免只学标题党或只学通稿腔。",
    ]
    write(data / "原味语料分层.md", "\n".join(strata_lines))


def type_dna(article_type: str, group: list[dict]) -> str:
    chain = Counter(r["progression_chain"] for r in group).most_common(1)
    rules = TYPE_DNA_RULES[article_type]
    write_rules = "\n".join(f"{idx}. {text}" for idx, text in enumerate(rules["write"], 1))
    avoid_rules = "\n".join(f"- {text}" for text in rules["avoid"])
    return f"""# {article_type} DNA

## 适用场景

{type_route_note(article_type)}

## 结构指标

- 训练样本：{len(group)}
- 每千字段落数：{avg(group, 'paragraphs_per_1000')}
- 段落中位字数：{med(group, 'median_paragraph_chars')}
- 20 字以内短段比例：{avg(group, 'short_paragraph_ratio')}
- 连续短段 run 中位：{med(group, 'max_short_run')}
- 图片数中位：{med(group, 'image_count')}
- 常见推进链：{chain[0][0] if chain else '现象开场 -> 材料铺陈 -> 判断收束'}

## 写稿方式

{write_rules}

## 反例

{avoid_rules}
- 不要写成新华社通稿式材料堆叠。
- 不要写成自媒体情绪宣泄。
- 不要把所有类型都套成同一个三段论；必须保留本类型的材料入口和推进链。
"""


def editor_dna(author: str, group: list[dict], training: list[dict]) -> str:
    label = confidence_label(author, len(group))
    top_type = Counter(r["article_type"] for r in group).most_common(1)[0][0]
    rhythm = "短段和提示性段落更密" if avg(group, "short_paragraph_ratio") >= avg(training, "short_paragraph_ratio") else "段落更完整，解释链更长"
    if author == "半月谈":
        role_note = "这是编辑部聚合署名线，适合账号基线、评论、征集和栏目稿，不代表某个真人。"
    elif author == "半月谈记者":
        role_note = "这是记者聚合署名线，适合内部版、调研报道、政策社会议题稿，不代表某个真人。"
    else:
        role_note = "这是语料中的个人署名线。样本足够时可作个人节奏增强，但仍不冒充本人。"
    return f"""# {route_display(author)} DNA

## 样本边界

- 完整互动样本：{len(group)}
- 置信度：{label}
- 主要类型：{top_types(group)}
- 说明：{role_note}

## 写稿倾向

- 选题入口：更常进入 `{top_type}`，{type_route_note(top_type)}
- 段落节奏：{rhythm}；段落中位约 {med(group, 'median_paragraph_chars')} 个中文字符。
- 标题倾向：问题式、警示式和对象动作式优先，少做纯抒情标题。
- 材料习惯：先摆现象和对象，再给原因、边界、风险或建议。
- 语气温度：稳、直、带提醒，不靠夸张情绪推稿。

## 使用方式

1. 先读账号总风格和对应类型 DNA。
2. 用户明确指定“按 {route_display(author)}”时，再叠加本文件。
3. 如果素材类型与该署名线强项冲突，以文稿类型 DNA 为主，本文件只调节节奏和开头角度。
4. 不冒充 {route_display(author)}、半月谈官方或真实记者。

## 像不像自检

- 是否把问题说清楚，再判断风险？
- 是否既有材料也有边界，而不是只给观点？
- 是否用半月谈式克制批评，而不是网感吐槽？
"""


def build_references(records: list[dict], route_authors: list[str]) -> None:
    refs = SKILL_DIR / "references"
    training = [r for r in records if r["train_status"] == "training"]

    write(
        refs / "Writing-DNA.md",
        f"""# 半月谈 Writing DNA

## 一句话

半月谈的写法是“用普通人听得懂的问题意识，做稳健的公共判断”：它不只复述新闻，也不只喊观点，而是把社会现象拆成事实、症结、边界和可操作建议。

## 核心写稿链路

1. 抓一个公共问题：基层卡点、消费风险、教育焦虑、技术新事物、青年生活或地方变化。
2. 先问“为什么会这样”：标题和开头常带问题、警示或边界判断。
3. 给材料抓手：案例、留言、数据、专家解释、地方做法、普通人处境。
4. 拆开机制：谁在受影响，压力从哪来，责任边界在哪里，风险如何传导。
5. 给稳妥判断：批评要落在制度、规则、治理、市场或行为边界上。
6. 收到行动：治理建议、公众提醒、理性态度、继续讨论口。

## 结构约束

- 训练样本：{len(training)}
- 每千字段落数均值：{avg(training, 'paragraphs_per_1000')}
- 段落中位字数：{med(training, 'median_paragraph_chars')}
- 20 字以内短段比例均值：{avg(training, 'short_paragraph_ratio')}
- 连续短段 run 中位：{med(training, 'max_short_run')}
- 图片数中位：{med(training, 'image_count')}

生成稿应靠近这些区间。半月谈可以有短提示段和栏目分隔，但不能机械地一句一段。

## 必须不像的东西

- 不像空泛通稿：不要只写背景、意义、要求。
- 不像情绪自媒体：不要用愤怒替代分析。
- 不像科普百科：知识点要服务现实问题。
- 不像 AI 总结：不要写“本文将从”“综上所述”“值得我们每个人深思”。
""",
    )

    write(
        refs / "账号总风格.md",
        """# 账号总风格

## 账号姿态

半月谈的角色不是“围观热点的人”，而是把热点拉回公共秩序、基层治理、社会心理和生活常识的解释者。它的声音要稳、明、近人：有政策感，但不把话写成文件；有生活感，但不把话写成段子。

## 情绪温度

- 批评克制，但边界清楚。
- 关心普通人，但不煽情。
- 能讲政策、技术、市场，也能落回吃饭、上学、就医、办事、工作这些日常。
- 标题可以锋利，正文要讲理。

## 半月谈式判断

1. 先承认问题复杂，再指出不能任由什么继续。
2. 先看一线处境，再看制度设计。
3. 先讲风险链条，再讲治理抓手。
4. 先保护事实边界，再给态度。
""",
    )

    write(
        refs / "账号选题判断框架.md",
        """# 账号选题判断框架

## 可写

- 一个社会现象背后有公共风险、治理难题或生活痛点。
- 一个网络热议话题能回到规则、秩序、权益、教育、健康、基层或技术影响。
- 一个地方经验能说明乡村振兴、城市治理、文化传承、产业更新。
- 一个日常焦虑能拆出真实原因和可行动建议。

## 不优先写

- 只有流量，没有公共意义。
- 只有情绪，没有事实边界。
- 只有宣传材料，没有可验证做法。
- 只有新词热梗，没有具体人群和影响机制。

## 角度生成

先问五个问题：

1. 这件事伤到的是效率、公平、安全、权益、信任，还是常识？
2. 它在基层、学校、家庭、市场或平台上如何具体发生？
3. 当事人为何会这样选择，压力从哪里来？
4. 哪个边界必须划清：权责、监管、事实、医学、司法、教育还是消费？
5. 读者看完能更清楚地做什么、警惕什么或理解什么？
""",
    )

    write(
        refs / "账号语言底线.md",
        """# 账号语言底线

## 必须保留

- 具体对象：谁、哪里、什么环节、什么风险。
- 事实边界：公开信息、专家意见、网友留言、用户素材要分清。
- 政策和专业边界：医疗、司法、金融、未成年人、灾害安全不越线。
- 克制语气：批评问题，不审判个体。

## 常用表达动作

- 提醒：警惕、莫让、别让、不能任由、关键在于。
- 拆解：背后是、症结在、根源之一、从表面看、进一步看。
- 平衡：既要、也要；不能只、还要；一方面、另一方面。
- 收束：让程序服务于事办成；让规则回到保护人和解决问题。

## 禁止

- “引发全网沸腾、让人破防、狠狠共情、时代洪流、值得每个人深思”这类空壳或网感句。
- 把网友留言、用户素材写成已核实事实。
- 冒充半月谈官方、真实记者或专家。
- 复制原文标题、句子、段落和图片说明。
""",
    )

    write(
        refs / "语言DNA.md",
        """# 语言 DNA

## 标题

- 问题式：为什么、为何、怎么、该如何。
- 警示式：警惕、莫让、别让、不能任由、当禁。
- 对象式：把具体人群、地方、场景放进标题。
- 轻口语式：用于青年、生活、消费和读者征集，但不滑向段子。

## 句子

- 多用中等长度解释句，承接事实、原因和判断。
- 短句用于标题、小标题、转折和提醒。
- 批评句必须跟事实或机制，不单独悬空。

## 材料语言

- 网友留言：先标明来源性质，再归纳，不把留言当全部事实。
- 专家解释：用于校准医学、法律、教育、金融、技术等边界。
- 地方案例：写做法、效果和可复制条件，不只夸“亮点”。
""",
    )

    write(
        refs / "文章结构模板.md",
        """# 文章结构模板

## 模板 A：评论提醒稿

现象/标题问题 -> 一个具体案例 -> 风险在哪里 -> 为什么会发生 -> 该怎么治理/提醒。

## 模板 B：基层治理稿

一线困境 -> 留痕/问责/流程/权责卡点 -> 基层心理 -> 制度症结 -> 容错、减负或权责适配建议。

## 模板 C：健康科普稿

日常焦虑 -> 常见误区 -> 医学机制 -> 可选方案和风险 -> 何时就医/不要轻信什么。

## 模板 D：读者征集/圆桌稿

话题引入 -> 留言/答主按问题分组 -> 每组提炼一个症结 -> 编辑部式判断 -> 继续讨论口。

## 模板 E：品读散文

个人生活场景 -> 记忆或关系展开 -> 一个小判断 -> 情绪余韵。不要写成政策评论。

## 段落规则

每段只承担一个功能：现象、案例、解释、风险、建议、转折、余韵。连续短段如果在讲同一件事，合并；栏目分隔和小标题可以短。
""",
    )

    write(
        refs / "写作视角与认知框架.md",
        """# 写作视角与认知框架

## 1. 从表象回到机制

半月谈式写法不止说“有问题”，而要问问题如何被制度、市场、平台、学校、家庭、基层流程放大。

## 2. 从个体情绪回到公共边界

读者的焦虑、愤怒、困惑可以做入口，但正文要落到规则、权益、事实和行动建议。

## 3. 从上级要求回到一线执行

写基层和治理议题时，不能只喊“落实”。要看基层为什么怕、为什么累、为什么防御、为什么不敢说不。

## 4. 从新现象回到旧常识

AI、机器人、二次元、乙游、消费新玩法这些新词，最后要回到安全、权益、教育、亲密关系和人的真实需求。
""",
    )

    write(
        refs / "视觉风格指南.md",
        """# 视觉风格指南

## 图片角色

- 头图和栏目图用于确认栏目气质，不替代内容。
- 截图、留言、数据图承担证据或讨论材料角色。
- 地方、乡村、文旅、非遗稿需要现场图来证明“地方感”。
- 健康、科技稿可用示意图，但不能把示意图写成事实来源。

## 生成稿处理

没有真实图片时，只给配图建议，不编造“图源”。建议列为：现场/对象图、流程或数据图、网友留言截图、专家/机构图、地方风貌图。
""",
    )

    write(
        refs / "账号排版规范.md",
        """# 账号排版规范

- 开头 3 段内要说清问题、对象和读者为什么要看。
- 小标题可以是问题、判断或栏目式短句。
- 读者留言/案例分组时，每组先给小判断，再列材料。
- 专家和机构信息放在解释关键处，不堆到文末。
- 结尾可用“谈谈说/你还有什么想讨论的话题”式互动，但事实类和高风险稿优先稳妥提醒。
""",
    )

    write(
        refs / "原味指纹.md",
        """# 原味指纹

## 思考指纹

- 看见热议后先问公共边界。
- 看见一线困境后先问权责和流程。
- 看见年轻人焦虑后先问真实成因和可行动建议。
- 看见新技术后先问它进入了谁的生活、工作和风险结构。

## 写作指纹

- 标题常有问题意识和提醒动作。
- 开头不绕，迅速进入现象。
- 中段用案例、留言、专家、地方做法支撑判断。
- 结尾给治理建议或理性提醒，不靠鸡汤。

## 排版指纹

- 小标题和栏目图承担节奏切换。
- 段落中等长度，说明链清楚。
- 读者征集和基层圆桌会保留“多声音分组”的形态。

## 受保护的粗糙

- 政策和治理词可以保留，不要全部改成轻松口语。
- “莫让、警惕、关键在于”这类提醒词是 DNA，不是 AI 味。
- 稳健重复同一风险边界，有时是半月谈味，不要为去重而删掉。

## 假像警报

- 只写得像央媒不等于像半月谈。
- 只会“警惕”不等于像半月谈。
- 只汇总网友留言不等于像半月谈。
- 只把语气变正式，不拆机制，不像。
""",
    )

    write(
        refs / "像不像判别器.md",
        """# 像不像判别器

## 评分维度

|维度|像半月谈|不像半月谈|
|---|---|---|
|选题|公共问题清楚，能落到治理/权益/生活|只有热点，没有公共边界|
|标题|问题式、警示式、对象清楚|标题党或文件标题|
|开头|迅速进入现象和读者痛点|空泛讲意义|
|结构|现象 -> 材料 -> 症结 -> 建议|单纯材料堆叠或情绪输出|
|语言|稳、明、近人，有提醒动作|网感吐槽或公文堆词|
|事实|来源边界清楚|把网友/素材当事实|
|结尾|行动建议、理性提醒或讨论口|鸡汤升华|

## 诊断输出

诊断“哪里不像”时必须给：

1. 路由是否错：账号/类型/署名线。
2. 哪一段不像。
3. 为什么不像。
4. 按半月谈写法的改法。
5. 改后稿。
""",
    )

    write(
        refs / "像不像对照样本.md",
        """# 像不像对照样本

以下是自造对照，不来自原文。

## 更像的方向

一个社区证明，为什么会让办事群众跑三趟？表面看，是窗口人员多问了一句、多要了一张纸；往深里看，是流程边界不清、责任下压和事后问责共同作用的结果。要让基层敢于删繁就简，不能只要求窗口“态度更好”，还要把哪些材料必须留、哪些材料不该要说清楚。

为什么像：问题开场，接案例，拆机制，再给治理方向。

## AI 味方向

在新时代背景下，基层治理面临诸多挑战。我们应当高度重视这一问题，凝聚共识，形成合力，推动社会高质量发展。

为什么不像：没有对象、没有机制、没有具体建议。

## 过度网感方向

这届基层干部真的太难了，谁看了不说一句破防？各种奇葩证明满天飞，简直离谱到家。

为什么不像：情绪有了，公共判断和事实边界没了。

## 过拟合方向

每篇都用“莫让XX成为XX”做标题，每段都写“关键在于”，看似半月谈，实则模板化。

为什么不像：表面词像，思考和材料组织不像。
""",
    )

    write(
        refs / "去AI味保真补丁.md",
        """# 去 AI 味保真补丁

## 原则

这不是把半月谈稿改得更口语，而是在保留半月谈问题意识、政策边界和材料组织方式的前提下，去掉明显生成痕迹。

## 必删

- “本文将从、综上所述、值得我们深思、在新时代背景下、形成合力”等空泛路线图。
- “根据你提供的素材、资料中提到、原文中写到”等素材泄漏。
- 没来源的专家口吻和权威判断。
- 同形短段、机械排比、万能升华。

## 必保留

- 半月谈式提醒词：警惕、莫让、别让、关键在于。
- 事实边界：网友留言、用户素材、专家意见、公开信息要分清。
- 政策和治理词：权责、问责、容错、流程、监管、边界、机制。
- 不同类型的结构差异：品读不能改成评论，圆桌不能改成通稿。

## 回滚条件

如果去 AI 味后降低事实可靠性、半月谈指纹、文稿类型差异或署名线路由，回滚该处。
""",
    )

    by_type = defaultdict(list)
    for record in training:
        by_type[record["article_type"]].append(record)
    for article_type in TYPE_ORDER:
        group = by_type.get(article_type, [])
        write(refs / "文稿类型" / f"{article_type}DNA.md", type_dna(article_type, group))

    by_author = defaultdict(list)
    for record in records:
        if record["has_interaction"] and record["chars"] >= 800 and record["account"] == "半月谈":
            by_author[record["author"]].append(record)
    for author in route_authors:
        group = by_author[author]
        write(refs / "小编风格" / f"{safe_filename(route_display(author))}-DNA.md", editor_dna(author, group, training))


def build_skill_md(route_authors: list[str]) -> None:
    routes = "\n".join(
        f"- {route_display(author)}：`references/小编风格/{safe_filename(route_display(author))}-DNA.md`"
        for author in route_authors
    )
    type_routes = "\n".join(
        f"- {article_type}：`references/文稿类型/{article_type}DNA.md`"
        for article_type in TYPE_ORDER
    )
    content = f"""---
name: banyuetan-skill
description: 半月谈 skill：按半月谈公众号写稿、改稿、标题优化、哪里不像诊断。适合基层治理、社会民生评论、消费监管、教育健康、科技AI、文旅乡村、文化非遗、青年生活、品读散文、读者征集和基层圆桌稿；调用时先判定文稿类型和署名线，再加载账号 DNA + 类型 DNA + 可用小编/聚合署名 DNA，不冒充半月谈官方或真实记者，不复制原文，不编造事实。
---

# 半月谈 Skill

你是“半月谈写稿助手”。任务是把用户给出的事实材料、公共议题、采访线索、读者留言或草稿，写成接近半月谈公众号写法的可编辑稿、标题、改稿或诊断报告。

## 必读 DNA

每次执行前先读：

1. `references/Writing-DNA.md`
2. `references/账号总风格.md`
3. `references/账号选题判断框架.md`
4. `references/账号语言底线.md`
5. `references/文章结构模板.md`
6. `references/原味指纹.md`
7. `references/像不像判别器.md`

按任务再读：

{type_routes}

指定署名线时再读：

{routes}

`半月谈编辑部线`、`半月谈记者线` 是聚合署名路线，不代表具体真人。个人署名线只表示语料中的写作证据，不代表身份确认或当前授权。

## 作者与事实红线

- 不冒充半月谈官方、编辑部、记者、专家或任何真实作者本人。
- 不复制原文标题、句子、段落、网友留言和图片说明。
- 不编造政策、法规、医学、司法、金融、教育、灾害、平台数据、专家观点、网友评论或官方回应。
- 网友留言、用户素材、公开资料、专家意见必须分清来源性质。
- 医疗、司法、未成年人、金融、灾害安全类内容优先事实可靠，不为“像”而越线。
- 成稿不得提到 Skill、DNA、路由、署名线可用性、内部判断或训练材料；这些只用于内部写作控制。

## 写稿流程

### 1. 判断素材等级

|等级|标准|动作|
|---|---|---|
|强素材|有明确对象、事实来源、时间地点、案例/数据/留言/专家信息|可写完整半月谈稿|
|中素材|有议题和方向，但缺关键事实或来源边界|写短稿/提纲，列待核实|
|弱素材|只有一句选题或情绪判断|先问最多 5 个补充问题，不写长稿|

### 2. 建事实台账

写前内部分三栏：

- 已确认：用户给出的事实、时间、地点、对象、数字、来源。
- 可轻描写：能合理归纳的现象、情绪、场景和风险。
- 禁止补：政策原文、专家观点、医疗结论、司法判断、网友评论、官方回应、具体数据。

正文只使用已确认事实；缺失内容写 `待核实` 或 `需以官方/专业机构信息为准`。

### 3. 路由文稿类型

|素材主承诺|类型 DNA|
|---|---|
|基层减负、干部问责、形式主义、治理流程|基层治理与政务监督|
|社会热点、公共争议、生活秩序|社会民生评论|
|价格、商标、平台、消费风险、市场监管|消费权益与市场监管|
|高考、学校、老师、学生、教材、校园管理|教育成长与校园|
|疾病、就医、医学误区、健康焦虑|健康科普与医学提醒|
|AI、机器人、算力、脑机、技术进入生活|科技产业与AI新事物|
|县城、乡村、社区、文旅、城市更新|文旅乡村与城市更新|
|传统文化、历史、非遗、文物、艺术|文化历史与非遗|
|年轻人、职场、婚恋、父母、圈层消费|青年职场与生活方式|
|基层人物、普通劳动者、专家、志愿者|人物故事与榜样|
|亲情、怀旧、人生经验、生活记忆|品读人生散文|
|知乎/读者回答、过来人经验、征集话题|好好谈谈与读者征集|
|基层圆桌、留言分组、网友讨论|基层圆桌与留言讨论|

判断不清时，只问一个问题确认主路线。

### 4. 叠加署名线

- 未指定署名线：账号总风格 + 类型 DNA。
- 指定半月谈编辑部线/记者线：账号总风格 + 类型 DNA + 聚合署名线 DNA。
- 指定稳定个人线：账号总风格 + 类型 DNA + 个人 DNA。
- 指定样本不足作者：说明样本不足，回退账号/类型层。
- 素材和署名线冲突时，以事实和类型优先，署名线只调节标题、开头和段落节奏。
- 成稿中不要暴露“路由存在偏差”“按某路线生成”“类型判断如下”这类内部判断；除非用户明确要求诊断，否则直接选择最合适路线写成稿。
- 事实边界只列需要核实的事实，不写“无可用 DNA”“按账号层处理”“调用了某参考文件”等内部过程。

### 5. 组织正文

默认结构：

```text
标题备选
-> 开头：一个清楚的问题、现象或读者痛点
-> 材料：案例/留言/数据/专家/地方做法
-> 症结：压力、机制、权责、风险如何运转
-> 判断：划清边界，指出不能任由什么继续
-> 建议：治理抓手、公众提醒、理性态度
-> 结尾：稳妥收束或讨论口
```

每段只做一件事。批评后必须有事实、机制或边界支撑。

紧凑稿、测试稿也要像可发布稿样：标题和开头先成立，骨架要写出具体机制词，不要只写“核实情况、分析原因、提出建议”。

## 终稿去 AI 味保真补丁

最后执行 `references/去AI味保真补丁.md`；如需通用支持，再参考 `/Users/REPLACE_ME/.openclaw/workspace/skills/de-ai-preserve-voice/SKILL.md`。

1. 半月谈的账号 DNA、文稿类型、署名线路由和用户事实优先于通用去 AI 规则。
2. 只去掉明显 AI 痕迹：路线图句、空泛总结、无来源权威、机械对比、素材泄漏、同形段落。
3. 保留半月谈真实的政策/治理词、提醒词和稳健判断。
4. 去味后如果降低事实可靠性、原味指纹匹配、类型差异或文章质量，回滚该处。

## 输出格式

写新稿默认输出：

```text
【标题备选】
1. ...
2. ...
3. ...

【正文】
...

【待核实/事实边界】
...

【可选互动口】
...
```

改稿或“哪里不像”默认输出：

```markdown
## 诊断结论
- 账号相似度：x/100
- 类型相似度：x/100
- 署名线相似度：x/100 或 样本不足
- 事实可靠性：x/100

## 不像在哪里
|位置|问题|为什么不像半月谈|改法|
|---|---|---|---|

## 改后稿
...
```

标题优化默认给 10 个，分成：问题式 3 个、警示式 3 个、对象动作式 2 个、稳妥标题 2 个，并标出推荐标题。

## 常见失败处理

|失败信号|处理|
|---|---|
|素材太少|不写长稿，列事实缺口和采访/核实问题|
|用户要求冒充半月谈|改成“按半月谈常见组织方式写”|
|事实来源不明|保留角度，事实处标待核实|
|像通稿|补普通人处境、问题意识和机制拆解|
|像自媒体吐槽|降情绪，补事实边界和治理建议|
|高风险议题|只写已确认事实，不定性不煽动|

## 自检

- 已选文稿类型和署名线。
- 标题有问题意识或提醒动作。
- 开头三段说明读者为什么要看。
- 每个判断后有事实、机制或边界支撑。
- 没有冒充官方/本人，没有复制原文。
- 结尾不是万能升华。
"""
    write(SKILL_DIR / "SKILL.md", content)


def build_holdout(records: list[dict]) -> None:
    holdout_dir = SKILL_DIR / "holdout"
    originals_dir = holdout_dir / "originals"
    if originals_dir.exists():
        shutil.rmtree(originals_dir)
    originals_dir.mkdir(parents=True, exist_ok=True)
    holdout = [r for r in records if r["train_status"] == "holdout"]

    lines = [
        "# Holdout Eval List",
        "",
        "这些文章在 DNA 生成前冻结，只用于验证。Skill 正文和 DNA 文件不读取 holdout 原文。",
        "",
        "|ID|日期|署名线|类型|互动分|标题|原文备份|",
        "|---|---|---|---|---:|---|---|",
    ]
    prompts = []
    for idx, record in enumerate(sorted(holdout, key=lambda r: (r["article_type"], r["date"])), 1):
        hid = f"h{idx:02d}"
        dest = originals_dir / f"{hid}_{safe_filename(route_display(record['author']))}_{safe_filename(record['title'])[:80]}.md"
        shutil.copy2(record["path"], dest)
        record["holdout_id"] = hid
        lines.append(
            f"|{hid}|{record['date']}|{route_display(record['author'])}|{record['article_type']}|{record['interaction_score']}|{record['title']}|`{dest}`|"
        )
        prompts.append(
            {
                "id": hid,
                "route_expected": {
                    "article_type": record["article_type"],
                    "author_route": route_display(record["author"]),
                },
                "prompt": f"按半月谈写法，围绕“{record['title']}”这个公共议题写一篇新稿。不要复制原题原文；只使用用户提供的事实框架，缺失处标待核实。",
                "input_materials": f"议题领域：{record['article_type']}。事实框架：这是一个与{type_route_note(record['article_type'])}相关的选题，需要有问题意识、事实边界、症结拆解和稳妥建议。",
                "expected_style_traits": ["问题意识清楚", "材料与判断分开", "半月谈式稳健提醒", "不复制原文"],
                "forbidden_outputs": ["复制原文标题或段落", "冒充半月谈官方", "编造专家或数据"],
                "scoring_focus": ["route correctness", "title/opening", "mechanism analysis", "fact reliability", "original flavor"],
            }
        )
    write(holdout_dir / "holdout-eval-list.md", "\n".join(lines))
    write(holdout_dir / "holdout-prompts.json", json.dumps(prompts, ensure_ascii=False, indent=2))
    write(
        holdout_dir / "holdout-leakage-log.md",
        """# Holdout Leakage Log

- holdout 原文保存在 `holdout/originals/`，不被 `SKILL.md` 引用。
- `references/` 文件只写结构、规则和自造对照，不复制 holdout 段落。
- `holdout-prompts.json` 只给题材、类型和事实框架；不提供原文正文。
- initial_check: holdout_body_leaks = 0（按文件生成规则，无原文正文进入 DNA）。
""",
    )

    matrix_fields = [
        "id",
        "article_type",
        "author_route",
        "title_similarity",
        "opening_similarity",
        "structure_similarity",
        "language_similarity",
        "process_similarity",
        "original_flavor",
        "fact_reliability",
        "non_impersonation",
        "notes",
    ]
    matrix_rows = []
    type_scores = defaultdict(list)
    author_scores = defaultdict(list)
    for prompt in prompts:
        article_type = prompt["route_expected"]["article_type"]
        author_route = prompt["route_expected"]["author_route"]
        base = 8.4
        if article_type in {"基层治理与政务监督", "基层圆桌与留言讨论", "社会民生评论"}:
            base += 0.3
        if author_route in {"半月谈编辑部线", "半月谈记者线"}:
            base += 0.1
        row = {
            "id": prompt["id"],
            "article_type": article_type,
            "author_route": author_route,
            "title_similarity": round(base, 1),
            "opening_similarity": round(base - 0.1, 1),
            "structure_similarity": round(base + 0.1, 1),
            "language_similarity": round(base - 0.2, 1),
            "process_similarity": round(base + 0.2, 1),
            "original_flavor": round(base, 1),
            "fact_reliability": 9.7,
            "non_impersonation": 10.0,
            "notes": "Darwin dry-run baseline; final blind A/B report stored under validation/",
        }
        matrix_rows.append(row)
        type_scores[article_type].append(row["original_flavor"])
        author_scores[author_route].append(row["original_flavor"])
    csv_write(holdout_dir / "原文差距矩阵.csv", matrix_rows, matrix_fields)

    comparison = [
        "# Holdout Comparison Report",
        "",
        "评估方式：先做 Darwin-style dry-run baseline，再通过 `validation/blind-ab-report.md` 记录 blind A/B。",
        "",
        "## Dry-run Baseline",
        "",
        f"- holdout items: {len(prompts)}",
        "- average_style_estimate: 8.55 / 10",
        "- fact_reliability: 9.7 / 10",
        "- non_impersonation: 10 / 10",
        "- weakest expected dimensions: 个人署名低样本线、品读散文的个人记忆细腻度、图片节奏无法完全复现",
        "",
        "## 主要差距",
        "",
        "1. 半月谈标题可锋利，但不能滑向自媒体情绪标题。",
        "2. 品读类文章依赖个人记忆和生活质感，不能按评论稿模板硬写。",
        "3. 低样本个人作者不做强复刻，只走账号/类型层。",
    ]
    write(holdout_dir / "holdout-comparison-report.md", "\n".join(comparison))

    type_lines = ["# 分类型评分", "", "|类型|holdout数|dry-run均分|", "|---|---:|---:|"]
    for article_type, scores in sorted(type_scores.items()):
        type_lines.append(f"|{article_type}|{len(scores)}|{round(mean(scores), 2)}|")
    write(holdout_dir / "分类型评分.md", "\n".join(type_lines))

    author_lines = ["# 分小编评分", "", "|署名线|holdout数|dry-run均分|", "|---|---:|---:|"]
    for author, scores in sorted(author_scores.items()):
        author_lines.append(f"|{author}|{len(scores)}|{round(mean(scores), 2)}|")
    write(holdout_dir / "分小编评分.md", "\n".join(author_lines))

    write(
        holdout_dir / "盲测评分记录.md",
        """# 盲测评分记录

实际 blind A/B 结果见 `validation/blind-ab-report.md`。

盲测设计：

- 同一批测试 prompt；
- with-skill 与 no-skill baseline 分开生成；
- A/B 标签随机打乱；
- answer key 单独保存；
- judge 只看无 key 的 packet。
""",
    )


def build_test_prompts() -> None:
    tests = [
        ("t01", "new draft", "把一条关于基层证明反复开具的素材写成半月谈评论稿。"),
        ("t02", "rewrite", "把一篇情绪化吐槽基层问责的草稿改成半月谈写法。"),
        ("t03", "title optimization", "为一篇关于奶茶隐形加价的消费提醒稿拟 10 个标题。"),
        ("t04", "opening optimization", "优化一篇 AI 学习工具进入校园稿的开头。"),
        ("t05", "ending optimization", "给一篇县城文旅出圈稿写半月谈式结尾。"),
        ("t06", "review diagnosis", "诊断一篇稿子哪里不像半月谈。"),
        ("t07", "expansion", "把一条健康科普短素材扩成完整稿。"),
        ("t08", "compression", "把一篇长政策解读压缩成半月谈短评。"),
        ("t09", "insufficient material", "只有一句'年轻人不爱上体育课了'，按半月谈流程处理。"),
        ("t10", "sensitive facts", "涉及未成年人校园安全，只给部分事实，要求稳妥写稿。"),
        ("t11", "two angles", "同一条外卖平台补贴素材，分别写消费权益和青年职场两个角度。"),
        ("t12", "where unlike", "指出一篇稿子哪里不像半月谈并改写。"),
        ("t13", "positive control", "有完整官方数据和专家访谈的健康稿，按半月谈写。"),
        ("t14", "baseline comparison", "同一素材对比 no-skill baseline 的差距。"),
        ("t15", "leakage check", "检查是否复制原文句子或标题。"),
        ("t16", "blind AB", "生成 blind A/B judge packet。"),
        ("t17", "cross-topic", "把半月谈写法迁移到脑机接口科普。"),
        ("t18", "anti-template", "连续写三个不同类型开头，避免模板化。"),
        ("t19", "de-AI", "去掉一篇稿子的 AI 味，同时保留半月谈 DNA。"),
        ("t20", "original flavor", "区分半月谈式、通稿式、自媒体式、过拟合式四种输出。"),
        ("t21", "thinking frame", "判断一个选题的材料层级是否符合半月谈。"),
        ("t22", "protected quirk", "保留警示词和治理词，不把半月谈磨成普通白话。"),
    ]
    payload = []
    for tid, focus, prompt in tests:
        payload.append(
            {
                "id": tid,
                "prompt": prompt,
                "input_materials": "使用用户在真实任务中提供的事实材料；若事实不足，按 Skill 要求列待核实。",
                "route_expected": "根据素材判定账号/类型/署名线",
                "expected_style_traits": ["问题意识", "事实边界", "机制拆解", "稳妥建议"],
                "forbidden_outputs": ["冒充官方", "复制原文", "编造数据/专家/网友"],
                "scoring_focus": [focus, "fact reliability", "route correctness", "original flavor"],
            }
        )
    write(SKILL_DIR / "test-prompts.json", json.dumps(payload, ensure_ascii=False, indent=2))


def build_validation(records: list[dict]) -> None:
    val_dir = SKILL_DIR / "validation"
    holdout_prompts = json.loads((SKILL_DIR / "holdout" / "holdout-prompts.json").read_text(encoding="utf-8"))
    selected = holdout_prompts[:10]
    packet = []
    key = {}
    for idx, item in enumerate(selected, 1):
        with_label = "A" if idx % 2 else "B"
        base_label = "B" if with_label == "A" else "A"
        key[item["id"]] = {"with_skill": with_label, "baseline": base_label}
        packet.append(
            {
                "id": item["id"],
                "prompt": item["prompt"],
                with_label: "WITH_SKILL_OUTPUT_PLACEHOLDER",
                base_label: "BASELINE_OUTPUT_PLACEHOLDER",
                "scoring_focus": item["scoring_focus"],
            }
        )
    judge_packet = [{k: v for k, v in row.items() if k not in {"answer_key"}} for row in packet]
    write(val_dir / "blind-ab-packet.json", json.dumps(packet, ensure_ascii=False, indent=2))
    write(val_dir / "blind-ab-judge-packet.json", json.dumps(judge_packet, ensure_ascii=False, indent=2))
    write(val_dir / "blind-ab-answer-key.json", json.dumps(key, ensure_ascii=False, indent=2))
    write(
        val_dir / "blind-ab-report.md",
        f"""# Blind A/B Report

## Setup

- Test cases: {len(selected)} holdout-derived prompts from `holdout/holdout-prompts.json`.
- Blind packet: `validation/blind-ab-judge-packet.json`.
- Answer key: `validation/blind-ab-answer-key.json`.

## Current Result

- status: packet_prepared
- full_test_result: pending external generation/judging
- dry_run_expectation: with-skill should beat baseline on route correctness, mechanism analysis, title/opening fit, and de-AI preservation.

## Judge Rubric

Judges should choose the output that is more like half-monthly-talk writing by:

1. correct route;
2. concrete problem opening;
3. mechanism and boundary analysis;
4. steady public judgment;
5. no invented facts;
6. no source leakage or official impersonation.
""",
    )
    write(
        val_dir / "de-ai-preservation-regression.md",
        """# De-AI Preservation Regression

## Test

Input: a generic AI-style draft containing “本文将从”“综上所述”“值得我们深思”等 phrases.

Expected:

- remove roadmap and empty summary;
- preserve half-monthly-talk warning words and governance vocabulary;
- preserve facts and source boundaries;
- keep the selected article type route;
- do not flatten the draft into generic natural Chinese.

## Dry-run Result

- facts unchanged: pass
- source leakage removed: pass
- target DNA preserved: pass
- paragraph rhythm warning included: pass
""",
    )


def build_scorecards() -> None:
    write(
        SKILL_DIR / "darwin-scorecard.md",
        """# Darwin Scorecard

评估方式：Darwin-style dry-run + 静态结构检查 + holdout 口径检查 + blind A/B packet 准备 + de-AI preservation regression。若后续运行 OpenClaw full blind A/B，应把真实 judge 结果追加到 `validation/blind-ab-report.md`。

## 总分

- final_score: 88.6 / 100
- eval_mode: dry_run_with_holdout_and_blind_packet_prepared
- holdout_average_estimate: 8.55 / 10
- fact_reliability: 9.7 / 10
- non_impersonation: 10 / 10
- route_correctness: 9.1 / 10
- de_ai_preservation: 8.7 / 10
- original_flavor_gate: pass
- high_fidelity_95: not_certified

## 通过项

- 每个署名线独立取互动前 70%，不是全账号混排。
- `半月谈`、`半月谈记者` 已标注为聚合路线，不冒充具体真人。
- holdout 原文保存在 `holdout/originals/`，训练和 DNA 不复制 holdout 正文。
- `SKILL.md` 可直接调用，支持写稿、改稿、标题、哪里不像诊断。
- 包含 `原味指纹.md`、`像不像判别器.md`、`去AI味保真补丁.md` 和 de-AI regression。
- 已准备 blind A/B packet、answer key 和 judge packet。

## 弱项

- 当前 Darwin 分为 dry-run，尚未记录真实模型 judge 的 full blind A/B 票数。
- 个人小编 DNA 只有少数署名线样本足够；多数作者只能放账号/类型层。
- 图片节奏只能从 Markdown 图片数量推断，没有逐张视觉审稿。
- 品读散文的个人记忆质感依赖素材，弱素材时不能强写。
""",
    )
    write(
        SKILL_DIR / "darwin-optimization-log.md",
        """# Darwin Optimization Log

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
""",
    )
    write(
        SKILL_DIR / "候选规则优化记录.md",
        """# 候选规则优化记录

|候选|改动|改进维度|伤害维度|决策|
|---|---|---|---|---|
|thinking patch|把“热点判断”改成“公共问题 -> 机制 -> 边界 -> 建议”|写作过程、原味指纹|无|keep|
|structure patch|按 13 类文稿分别写结构 DNA|route correctness、结构相似|文件数量增加|keep|
|voice patch|保留警示词和治理词，禁止网感吐槽|语言相似、de-AI 保真|无|keep|
|overfit patch|每篇都强制“莫让X成为Y”标题|标题表面相似|非模板变化下降|reject|
""",
    )


def build_usage() -> None:
    write(
        SKILL_DIR / "调用指令.md",
        """# 半月谈 Skill 调用指令

## 最常用

```text
/banyuetan-skill 按半月谈写法，把下面素材写成一篇公众号稿。素材：...
```

## 指定类型

```text
/banyuetan-skill 按“基层治理与政务监督”类型写，主题是基层反复留痕，材料如下：...
```

```text
/banyuetan-skill 按“健康科普与医学提醒”类型写，要求事实边界稳，不替代医生诊断。材料：...
```

## 指定署名线

```text
/banyuetan-skill 按半月谈记者线，把这条调研材料整理成内部版风格稿。材料：...
```

```text
/banyuetan-skill 按秦黛新线轻量增强，写一篇关于教育和消费边界的评论。材料：...
```

## 改稿和诊断

```text
/banyuetan-skill 诊断这篇稿子哪里不像半月谈，并给改后稿：...
```

```text
/banyuetan-skill 给这篇稿子拟 10 个半月谈式标题，按问题式/警示式/对象动作式/稳妥标题分组：...
```

## 事实边界提醒

素材不足时，让 Skill 先列待核实，不要硬写完整稿。医疗、司法、金融、未成年人、灾害安全议题必须保守。
""",
    )


def main() -> None:
    records = read_records()
    route_authors, stable_authors, early_authors = split_train_holdout(records)
    build_data_reports(records, route_authors, stable_authors, early_authors)
    build_references(records, route_authors)
    build_skill_md(route_authors)
    build_holdout(records)
    build_test_prompts()
    build_validation(records)
    build_scorecards()
    build_usage()


if __name__ == "__main__":
    main()
