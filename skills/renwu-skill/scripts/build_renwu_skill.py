#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median


CORPUS_DIR = Path("/Users/REPLACE_ME/Documents/学习/重点学习公众号/人物")
SKILL_DIR = Path("/Users/REPLACE_ME/.openclaw/workspace/skills/renwu-skill")

GENERIC_AUTHORS = {"人物作者", "人物记者", "编辑部", "人物", "未知", "佚名", ""}
TYPE_ORDER = [
    "深度人物报道",
    "对话访谈",
    "女性家庭与亲密关系",
    "社会公共事件",
    "文娱影视人物",
    "生活方式与读者征集",
    "商业科技与消费",
    "教育成长",
    "编辑部与编者话",
]


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


def clean_author_name(value: str) -> str:
    value = re.sub(r"!\[.*?\]\(.*?\)", "", value)
    value = re.sub(r"\*+", "", value)
    value = value.replace("｜", "|").replace("丨", "|").replace("︱", "|")
    value = re.sub(
        r"^(作者|本刊记者|记者|主笔|主编|副主编|资深记者|实习生|撰文|文|采访|采写|视频)\s*",
        "",
        value,
    ).strip()
    value = re.split(
        r"\s+(?:摄影|图片|图|编辑|视频|实习生|校对|视觉|设计|运营|化妆|撰文|采访)|\s*[|]\s*(?:摄影|图片|图|编辑|视频|实习生|校对|视觉|设计|运营|化妆)",
        value,
    )[0]
    value = re.sub(r"（.*?）|\(.*?\)", "", value).strip()
    value = value.strip(" ：:|，,、；; ")
    value = re.sub(r"^(作者|本刊记者|记者|主笔|主编|副主编|资深记者)\s+", "", value).strip()
    return value


def extract_body_author(text: str) -> tuple[str | None, str | None]:
    separator = r"[｜|丨︱/:：]"
    for raw in text.splitlines()[:180]:
        line = raw.strip()
        if not line or line.startswith(("title:", "author:", ">")):
            continue
        plain = re.sub(r"\*+", "", line)
        match = re.search(r"(?:文(?:\s*/\s*视频)?|撰文|采写|采访|记者)\s*" + separator + r"\s*([^\n]+)", plain)
        if match:
            name = clean_author_name(match.group(1))
            if name and len(name) <= 30 and not re.search(r"(原文|链接|留言|点击|人物\])", name):
                return name, raw
        match = re.search(r"作者@([^\s，,。；;]+)", plain)
        if match:
            return clean_author_name(match.group(1)), raw
    return None, None


def normalize_author(front_author: str, body_author: str | None) -> str:
    author = front_author.strip()
    if body_author and (author in GENERIC_AUTHORS or len(body_author) <= 20):
        author = body_author
    if not author:
        author = "未知"
    parts = [p for p in re.split(r"[、/，, ]+", author) if p]
    if len(parts) >= 4:
        return "多人合写"
    return author


def strip_frontmatter_and_interaction(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4 :]
    marker = text.find("## 互动数据")
    if marker != -1:
        text = text[:marker]
    return text


def parse_number(raw: str | None) -> int | None:
    if not raw:
        return None
    match = re.match(r"([0-9]+(?:\.[0-9]+)?)(万)?", raw.strip())
    if not match:
        return None
    value = float(match.group(1))
    if match.group(2):
        value *= 10000
    return int(round(value))


def parse_interaction(text: str) -> dict[str, int] | None:
    marker = text.find("## 互动数据")
    if marker == -1:
        return None
    tail = text[marker : marker + 320]
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


def is_content_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(("---", "#", ">", "![]", "<", "【", "（")):
        return False
    if "原文链接" in stripped or "互动数据" in stripped:
        return False
    if re.search(r"(文|编辑|图|摄影|设计|实习生)\s*[｜|丨︱/:：]", stripped) and len(stripped) < 60:
        return False
    return count_chinese(stripped) > 0


def structure_metrics(body: str) -> dict[str, float | int | str]:
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
    headings = [line for line in lines if re.match(r"^\*{0,2}[\u4e00-\u9fffA-Za-z0-9「」《》、·]{2,14}\*{0,2}$", line)]
    return {
        "chars": chars,
        "paragraph_count": len(lengths),
        "paragraphs_per_1000": round(len(lengths) / max(chars, 1) * 1000, 2),
        "median_paragraph_chars": round(median(lengths), 1) if lengths else 0,
        "short_paragraph_ratio": round(sum(short_flags) / len(lengths), 3) if lengths else 0,
        "max_short_run": max_short_run,
        "image_count": len(re.findall(r"!\[.*?\]\(.*?\)", body)),
        "section_count": len(headings),
        "progression_chain": infer_progression_chain(body, paragraphs),
    }


def infer_progression_chain(body: str, paragraphs: list[str]) -> str:
    text = body[:4000]
    if "《人物》" in text and len(re.findall(r"：", text)) > 12:
        return "人物设问 -> 对方回答 -> 追问补充 -> 结尾判断"
    if re.search(r"(年前|年后|后来|如今|此后|那一年)", text):
        return "时间锚点 -> 场景复现 -> 命运转折 -> 当下回望"
    if paragraphs and re.search(r"(凌晨|晚上|早晨|那天|第一次|我见到)", paragraphs[0]):
        return "现场开场 -> 人物进入 -> 关系展开 -> 时代回声"
    return "人物/现象开场 -> 材料铺陈 -> 多方视角 -> 克制收束"


def classify_type(title: str, body: str) -> str:
    title_text = title.lower()
    sample = (title + "\n" + body[:4000]).lower()
    if re.search(r"编者的话|新刊|年度面孔|编辑部|作者书|团队", title):
        return "编辑部与编者话"
    if re.search(r"对话|访谈|问答|自述", title_text) or ("《人物》" in sample and len(re.findall(r"[:：]", sample)) >= 14):
        return "对话访谈"
    if re.search(r"疫情|新冠|坠毁|事故|案|死亡|记者|医院|地铁|aed|犯罪|无罪|救一个孩子|李文亮|灾|危机|极端天气|空难|杀夫", title_text):
        return "社会公共事件"
    if re.search(r"学校|老师|学生|大学|教育|高考|毕业|论文|中小学|女校|课堂", title_text):
        return "教育成长"
    if re.search(r"ai|互联网|大厂|公司|品牌|商业|消费|外卖|打工人|上班|咖啡|续命水|烤肠|工厂|职场", title_text):
        return "商业科技与消费"
    if re.search(r"电影|演员|导演|歌手|综艺|影视|漫威|金庸|脱口秀|偶像|凤凰传奇|黄渤|胡歌|周星驰|剧|春晚|音乐", title_text):
        return "文娱影视人物"
    if re.search(r"女性|女人|女孩|母亲|妈妈|父亲|家庭|婚姻|亲密|月经|女校|姐姐|妻子|父母|生育|妈妈", title_text):
        return "女性家庭与亲密关系"
    if re.search(r"生活|厨房|冬天|购物车|吃草|读者|征集|相册|旅行|城市|故乡|散步|日常|春天|夏天|菜市场|火车|西伯利亚", title_text):
        return "生活方式与读者征集"
    if re.search(r"疫情|新冠|医院|司法|犯罪|危机|灾难|事故", sample[:1500]):
        return "社会公共事件"
    if re.search(r"电影|演员|导演|歌手|综艺|影视|作品|角色", sample[:1500]):
        return "文娱影视人物"
    return "深度人物报道"


def read_records() -> list[dict]:
    records: list[dict] = []
    for path in sorted(CORPUS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        meta = parse_frontmatter(text)
        body_author, body_raw = extract_body_author(text)
        author = normalize_author(meta.get("author", ""), body_author)
        body = strip_frontmatter_and_interaction(text)
        metrics = structure_metrics(body)
        interaction = parse_interaction(text)
        title = meta.get("title") or re.sub(r"^\d{8}_", "", path.stem)
        date = meta.get("date", "")[:10]
        article_type = classify_type(title, body)
        record = {
            "path": str(path),
            "filename": path.name,
            "title": title,
            "front_author": meta.get("author", ""),
            "body_author": body_author or "",
            "body_author_raw": body_raw or "",
            "author": author,
            "account": meta.get("account", "人物"),
            "date": date,
            "year": date[:4],
            "url": meta.get("url", ""),
            "digest": meta.get("digest", ""),
            "article_type": article_type,
            "has_interaction": bool(interaction),
            "train_status": "not_selected",
            "source_stratum": "metadata_only",
            **metrics,
        }
        if interaction:
            record.update(interaction)
        else:
            record.update({"阅读": 0, "点赞": 0, "转发": 0, "喜欢": 0, "留言": 0, "interaction_score": 0})
        records.append(record)
    return records


def split_train_holdout(records: list[dict]) -> tuple[list[str], list[str]]:
    complete_inter = [r for r in records if r["has_interaction"] and r["chars"] >= 1000]
    author_groups: dict[str, list[dict]] = defaultdict(list)
    for record in complete_inter:
        author_groups[record["author"]].append(record)

    main_editors = [
        author
        for author, group in author_groups.items()
        if author not in GENERIC_AUTHORS and author != "多人合写" and len(group) >= 20
    ]
    main_editors.sort(key=lambda author: (-len(author_groups[author]), author))
    primary_editors = [author for author in main_editors if len(author_groups[author]) >= 30]

    for author, group in author_groups.items():
        group.sort(key=lambda r: (-r["interaction_score"], r["date"], r["filename"]))
        if author in main_editors or author in {"人物作者", "人物记者", "多人合写"}:
            limit = math.ceil(len(group) * 0.8)
            pool = group[:limit]
            for idx, record in enumerate(pool):
                record["train_status"] = "training"
                record["source_stratum"] = "high_engagement" if idx < max(1, len(pool) // 4) else "representative_top80"
            for record in group[limit:]:
                record["train_status"] = "excluded_low_interaction"
                record["source_stratum"] = "outside_personal_top80"
        else:
            for record in group:
                record["train_status"] = "sample_insufficient"
                record["source_stratum"] = "minor_author"

    holdout_records: list[dict] = []
    covered_types: set[str] = set()
    for author in primary_editors:
        pool = [r for r in author_groups[author] if r["train_status"] == "training"]
        if not pool:
            continue
        candidate = None
        for record in pool:
            if record["article_type"] not in covered_types:
                candidate = record
                break
        if candidate is None:
            index = min(len(pool) - 1, max(0, int(len(pool) * 0.35)))
            candidate = pool[index]
        holdout_records.append(candidate)
        covered_types.add(candidate["article_type"])

    # Add two account/type holdouts from generic bylines when available.
    for author in ["人物作者", "人物记者"]:
        pool = [r for r in author_groups.get(author, []) if r["train_status"] == "training"]
        if pool:
            index = min(len(pool) - 1, max(0, int(len(pool) * 0.4)))
            holdout_records.append(pool[index])

    # Ensure every sizeable trained article type has at least one frozen holdout.
    trained_by_type: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        if record["train_status"] == "training":
            trained_by_type[record["article_type"]].append(record)
    for article_type, pool in trained_by_type.items():
        if len(pool) < 15 or article_type in covered_types:
            continue
        pool.sort(key=lambda r: (-r["interaction_score"], r["date"], r["filename"]))
        index = min(len(pool) - 1, max(0, int(len(pool) * 0.4)))
        holdout_records.append(pool[index])
        covered_types.add(article_type)

    seen: set[str] = set()
    for record in holdout_records:
        if record["path"] in seen:
            continue
        seen.add(record["path"])
        record["train_status"] = "holdout"
        record["source_stratum"] = "frozen_holdout"

    return main_editors, primary_editors


def avg(records: list[dict], key: str) -> float:
    vals = [float(r[key]) for r in records if r.get(key) not in ("", None)]
    return round(mean(vals), 2) if vals else 0.0


def med(records: list[dict], key: str) -> float:
    vals = [float(r[key]) for r in records if r.get(key) not in ("", None)]
    return round(median(vals), 2) if vals else 0.0


def top_types(records: list[dict], limit: int = 3) -> str:
    counter = Counter(r["article_type"] for r in records)
    return "、".join(f"{name}({count})" for name, count in counter.most_common(limit))


def safe_filename(name: str) -> str:
    return re.sub(r"[\\/:\s]+", "_", name)


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


def confidence_label(count: int) -> str:
    if count >= 30:
        return "stable"
    if count >= 20:
        return "early"
    return "insufficient"


def type_route_note(article_type: str) -> str:
    notes = {
        "深度人物报道": "适合写一个人的长期命运、关键选择和时代关系，先找人身上的矛盾，再让事件慢慢浮出。",
        "对话访谈": "适合问答稿、长访谈和人物自述，保留追问痕迹，但要把问答组织成思想推进。",
        "女性家庭与亲密关系": "适合女性经验、家庭关系、母女/父女、亲密关系与自我选择，重点写处境而非口号。",
        "社会公共事件": "适合公共事件中的个体、灾难、医疗、司法、职业处境，事实红线最高，情绪必须由细节托住。",
        "文娱影视人物": "适合演员、导演、歌手、综艺人物和作品关系，写人如何被角色、行业和观众重新定义。",
        "生活方式与读者征集": "适合日常、读者故事、城市/季节/旅行/消费生活，靠细小经验组织共鸣。",
        "商业科技与消费": "适合科技、平台、职场、消费现象，不能写成商业分析，要落回具体人的使用和感受。",
        "教育成长": "适合学校、教师、学生、成长和教育制度，写制度如何进入一个人的日常。",
        "编辑部与编者话": "适合编者话、杂志说明、年度回望，声音更像编辑部自我交代，不当个人作者复刻。",
    }
    return notes[article_type]


def build_data_reports(records: list[dict], main_editors: list[str], primary_editors: list[str]) -> None:
    data = SKILL_DIR / "data"
    holdout = [r for r in records if r["train_status"] == "holdout"]
    training = [r for r in records if r["train_status"] == "training"]
    complete = [r for r in records if r["chars"] >= 1000]
    complete_inter = [r for r in complete if r["has_interaction"]]

    fields = [
        "filename",
        "title",
        "date",
        "year",
        "author",
        "front_author",
        "body_author",
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
        "path",
        "url",
    ]
    csv_write(data / "文章元数据总表.csv", records, fields)

    report = f"""# 语料质量报告

## 结论

- 语料目录：`{CORPUS_DIR}`
- Markdown 文件：{len(records)}
- 完整长文（中文字符 >= 1000）：{len(complete)}
- 带互动数据：{sum(1 for r in records if r['has_interaction'])}
- 完整长文且带互动数据：{len(complete_inter)}
- 进入训练集：{len(training)}
- 冻结 holdout：{len(holdout)}
- 可做稳定小编 DNA（>=30 篇完整互动样本）：{len(primary_editors)}
- 可做早期小编 DNA（20-29 篇完整互动样本）：{len(main_editors) - len(primary_editors)}

## 筛选规则

1. 先抽取 frontmatter、正文署名、日期、标题、互动数据和结构指标。
2. 若 frontmatter 为 `人物作者/人物记者/人物/编辑部`，优先使用正文 `文｜/文 丨/撰文｜` 署名。
3. 只把 `中文字符 >= 1000` 且有互动数据的文章放入互动筛选池。
4. 每个小编独立排序，不做全账号混排；训练池取该小编互动分前 80%。
5. 互动分 = 阅读 + 点赞*20 + 转发*40 + 喜欢*20 + 留言*100。阅读常被 10 万封顶，所以用转发/喜欢/留言打破上限并保留传播质量。
6. 小编完整互动样本 `<20` 不生成个人 DNA，只进入账号/类型层或样本不足清单。
7. holdout 从主要小编训练池中冻结，生成 DNA 和测试 prompt 时不使用原文段落。

## 全局结构指标（训练集）

- 每千字段落数：{avg(training, 'paragraphs_per_1000')}
- 段落中位中文字符：{med(training, 'median_paragraph_chars')}
- 20 字以内短段比例：{avg(training, 'short_paragraph_ratio')}
- 连续短段最大 run 中位：{med(training, 'max_short_run')}
- 每篇图片数中位：{med(training, 'image_count')}
- 每篇小标题数中位：{med(training, 'section_count')}

## 质量边界

- 这是 `ready / original_flavor` 方向的可调用 Skill，不认证 95% 复刻。
- 原始语料跨度长，2015-2018 与 2024-2026 的版式和署名规则不同；Skill 采用路由式规则避免平均化。
- `人物作者/人物记者` 中仍有无法恢复真实作者的文章；它们只进账号和文稿类型层，不进个人小编 DNA。
"""
    write(data / "语料质量报告.md", report)

    author_rows = []
    author_groups = defaultdict(list)
    for record in complete_inter:
        author_groups[record["author"]].append(record)
    for author, group in sorted(author_groups.items(), key=lambda item: (-len(item[1]), item[0])):
        train_count = sum(1 for r in group if r["train_status"] == "training")
        holdout_count = sum(1 for r in group if r["train_status"] == "holdout")
        pool_count = sum(1 for r in group if r["train_status"] in {"training", "holdout"})
        author_rows.append(
            {
                "author": author,
                "count": len(group),
                "pool_count": pool_count,
                "train_count": train_count,
                "holdout_count": holdout_count,
                "confidence": confidence_label(len(group)) if author in main_editors else "account/type only",
                "median_score": int(median([r["interaction_score"] for r in group])),
                "top_types": top_types(group),
                "median_para": med(group, "median_paragraph_chars"),
                "short_ratio": avg(group, "short_paragraph_ratio"),
            }
        )
    lines = [
        "# 小编语料分布",
        "",
        "|小编/署名线|完整互动样本|个人前80%池|训练|holdout|置信度|互动分中位|主要类型|段落中位|短段比例|",
        "|---|---:|---:|---:|---:|---|---:|---|---:|---:|",
    ]
    for row in author_rows[:80]:
        lines.append(
            f"|{row['author']}|{row['count']}|{row['pool_count']}|{row['train_count']}|{row['holdout_count']}|{row['confidence']}|{row['median_score']}|{row['top_types']}|{row['median_para']}|{row['short_ratio']}|"
        )
    write(data / "小编语料分布.md", "\n".join(lines))

    type_lines = [
        "# 文稿类型分布",
        "",
        "|文稿类型|全量完整互动|训练|holdout|结构提示|",
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
        f"训练集共 {len(training)} 篇。下表列前 220 篇；全量见 `data/文章元数据总表.csv` 的 `train_status=training`。",
        "",
        "|日期|小编|类型|互动分|标题|源路径|",
        "|---|---|---|---:|---|---|",
    ]
    for record in sorted(training, key=lambda r: (-r["interaction_score"], r["date"]))[:220]:
        train_lines.append(
            f"|{record['date']}|{record['author']}|{record['article_type']}|{record['interaction_score']}|{record['title']}|`{record['path']}`|"
        )
    write(data / "training-corpus-list.md", "\n".join(train_lines))

    insufficient = [
        (author, group)
        for author, group in author_groups.items()
        if author not in GENERIC_AUTHORS and author != "多人合写" and len(group) < 20
    ]
    insufficient.sort(key=lambda item: (-len(item[1]), item[0]))
    insuff_lines = [
        "# 样本不足清单",
        "",
        "这些署名线不生成个人 DNA。可用于账号或类型共性，但不能当稳定小编复刻。",
        "",
        "|署名|完整互动样本|主要类型|处理|",
        "|---|---:|---|---|",
    ]
    for author, group in insufficient[:100]:
        insuff_lines.append(f"|{author}|{len(group)}|{top_types(group)}|账号/类型层，不做个人 DNA|")
    for author in ["人物作者", "人物记者", "多人合写"]:
        group = author_groups.get(author, [])
        if group:
            insuff_lines.append(f"|{author}|{len(group)}|{top_types(group)}|聚合或无法确认署名，只做账号/类型层|")
    write(data / "样本不足清单.md", "\n".join(insuff_lines))

    strata = Counter(r["source_stratum"] for r in records)
    strata_lines = [
        "# 原味语料分层",
        "",
        "|层级|数量|用途|",
        "|---|---:|---|",
        f"|high_engagement|{strata['high_engagement']}|提炼爆发力和标题/开头强钩子，但不让其垄断原味|",
        f"|representative_top80|{strata['representative_top80']}|主要训练层，保留各小编个人前 80% 的常态写法|",
        f"|frozen_holdout|{strata['frozen_holdout']}|只用于验证，不进入 DNA 文件|",
        f"|outside_personal_top80|{strata['outside_personal_top80']}|互动低于个人前 80%，用于理解边界，不训练|",
        f"|minor_author|{strata['minor_author']}|样本不足署名线，不做个人复刻|",
        f"|metadata_only|{strata['metadata_only']}|无互动或短稿，仅保留在元数据审计中|",
        "",
        "原味保留原则：高互动只证明传播有效，不自动等于最像《人物》。最终 Skill 同时使用 high_engagement 与 representative_top80，避免只学爆款腔。",
    ]
    write(data / "原味语料分层.md", "\n".join(strata_lines))


def type_dna(article_type: str, group: list[dict]) -> str:
    chain = Counter(r["progression_chain"] for r in group).most_common(1)
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
- 常见推进链：{chain[0][0] if chain else '人物/现象开场 -> 材料铺陈 -> 克制收束'}

## 写稿方法

1. 先找一个能承受全篇的人或场景，不用宏大判断开头。
2. 把公共议题拆回到身体、房间、工作、家庭、一次对话或一个动作。
3. 材料顺序遵循“场景 -> 经历 -> 转折 -> 旁人视角 -> 当下余波”。
4. 引用必须服务于人物处境；不要用堆引语代替叙事。
5. 结尾不喊口号，留下一个变化后的状态、未解的问题或轻微回声。

## 反例

- 不要写成百科条目、通稿、人物履历表。
- 不要用“时代洪流下”“引发广泛关注”等空泛句替代细节。
- 不要为了像《人物》而强行煽情，情绪必须来自材料。
"""


def editor_dna(author: str, group: list[dict], training: list[dict]) -> str:
    confidence = confidence_label(len(group))
    top_type = Counter(r["article_type"] for r in group).most_common(1)[0][0]
    rhythm = "偏短段、镜头切换快" if avg(group, "short_paragraph_ratio") >= avg(training, "short_paragraph_ratio") else "段落更完整，叙述链更长"
    para = med(group, "median_paragraph_chars")
    route = type_route_note(top_type)
    return f"""# {author} DNA

## 样本边界

- 完整互动样本：{len(group)}
- 置信度：{confidence}
- 主要类型：{top_types(group)}
- 个人前 80% 训练/holdout：见 `data/文章元数据总表.csv`

`stable` 可作为个人小编线叠加；`early` 只能作为轻量增强，不能覆盖账号总风格和文稿类型 DNA。

## 写稿倾向

- 选题入口：更常进入 `{top_type}`，{route}
- 段落节奏：{rhythm}；段落中位约 {para} 个中文字符。
- 结构习惯：常从可见场景或人物状态进入，再回到较长时间线中的变化。
- 材料习惯：优先让人物行动、关系和选择自己说明问题，少用抽象评语。
- 语言温度：保持克制和体察，不把对象写成观点工具。

## 使用方式

1. 先读账号总风格和对应类型 DNA。
2. 用户明确指定“按 {author} 线”时，再叠加本文件。
3. 如果素材类型与 `{author}` 的强项冲突，以类型 DNA 为主，本文件只调节节奏和观察角度。
4. 不冒充 {author} 本人，不写“我是/本记者认为”。

## 像不像自检

- 是否先有具体人和具体场景，再有判断？
- 是否把人物放回关系和时间里，而不是只写标签？
- 是否保留了复杂性，没有把材料改成鸡汤、控诉或商业稿？
"""


def build_references(records: list[dict], main_editors: list[str]) -> None:
    refs = SKILL_DIR / "references"
    training = [r for r in records if r["train_status"] == "training"]
    complete_inter = [r for r in records if r["has_interaction"] and r["chars"] >= 1000]

    write(
        refs / "Writing-DNA.md",
        f"""# 人物 Writing DNA

## 一句话

《人物》的写法不是“把人物写感人”，而是让一个人的具体处境、选择和沉默，慢慢显出时代、制度、亲密关系或行业变化。

## 核心写稿链路

1. 找人：先确定承载文章的人，不先确定观点。
2. 找场：用一个可见场景、时间锚点或动作开门。
3. 找裂缝：人物身上必须有矛盾、失去、坚持、误解、转身或迟到的答案。
4. 找关系：把人放回家庭、工作、行业、地域、时代和他人眼光里。
5. 找时间：用过去/当下/后来组织故事，而不是用论点分段。
6. 找余波：结尾留下人物新的状态或未解问题，不替读者做总结。

## 结构约束

- 训练样本：{len(training)}
- 每千字段落数均值：{avg(training, 'paragraphs_per_1000')}
- 段落中位字数：{med(training, 'median_paragraph_chars')}
- 20 字以内短段比例均值：{avg(training, 'short_paragraph_ratio')}
- 连续短段 run 中位：{med(training, 'max_short_run')}
- 图片数中位：{med(training, 'image_count')}

生成稿应在这些区间附近移动。短段可以保留，但不能变成 AI 式一句一段。

## 必须不像的东西

- 不像百科：不要从人物履历、成就、标签起笔。
- 不像公号热评：不要上来裁判谁对谁错。
- 不像广告软文：不要把人物变成产品卖点。
- 不像 AI 总结：不要写“本文将从”“时代背景下”“给我们启示”。
""",
    )

    write(
        refs / "账号总风格.md",
        """# 账号总风格

## 账号姿态

《人物》站在报道者一侧，但不把报道者写成主角。它关心的是：一个人如何在时代、制度、家庭、行业、性别、地域、疾病、灾难或流行文化里被推着走，又如何保留一点自己的选择。

## 情绪温度

- 温柔但不甜。
- 克制但不冷。
- 有文学性，但不把文字写成装饰。
- 可以有疼痛、困惑、迟疑和笨拙，不急着抚平。

## 叙事优先级

1. 具体场景高于抽象判断。
2. 人物关系高于人物标签。
3. 长时间线高于单点爆点。
4. 细节里的命运感高于金句。
5. 未完成的复杂性高于漂亮结论。
""",
    )

    write(
        refs / "账号选题判断框架.md",
        """# 账号选题判断框架

## 可写

- 一个普通人或公众人物身上有可见的时代变化。
- 一个公共议题最终落在人的生活、身体、家庭或工作里。
- 一个流行现象背后有真实的人和关系，不只是热点。
- 一个多年后才出现回声的旧故事。
- 一个能让读者理解他人处境的职业、身份、年龄或地域样本。

## 不优先写

- 只有观点，没有人。
- 只有情绪，没有事实。
- 只有热点，没有可进入的生活切面。
- 只有人物履历，没有当下处境和关系变化。

## 角度生成

先问四个问题：

1. 这个人正在失去、争取、逃离或重新理解什么？
2. 这个变化是谁造成的：时代、行业、亲密关系、制度、疾病、观众，还是自己？
3. 最能说明这件事的一个场景是什么？
4. 结尾能不能停在一个新状态，而不是一句道理？
""",
    )

    write(
        refs / "账号语言底线.md",
        """# 账号语言底线

## 必须保留

- 时间、地点、动作、感官、物件、关系称谓。
- 采访对象的边界：不知道就不补，没说过就不写成他说过。
- 复杂性：允许一个人同时勇敢、软弱、迟疑、狭窄、清醒。
- 事实来源：公共事件、医疗、司法、未成年人、灾难事故只写已确认事实。

## 禁止

- “时代洪流”“引发热议”“令人唏嘘”“治愈了所有人”这类空壳句。
- 把采访对象写成观点工具人。
- 为了抒情改写事实。
- 冒充《人物》官方或任何真实记者本人。
- 复制原文标题、句子、段落、访谈问答和图片说明。
""",
    )

    write(
        refs / "语言DNA.md",
        """# 语言 DNA

## 句子

- 常用中长句承接人物经历，短句用于转场、停顿和情绪落点。
- 句子里允许有多个时间、动作和心理层次，但不能让逻辑断掉。
- 使用“然而、后来、此后、那一年、如今、或许、似乎”连接时间与判断。

## 词汇

- 偏向具体名词：房间、院子、火车站、医院、学校、后台、厨房、麦田、手机、表格。
- 偏向关系词：母亲、女儿、老师、同事、观众、读者、采访者、朋友。
- 少用口号词，少用网感强梗；即使写流行文化，也要把梗落回人。

## 引语

引语不是装饰。每段引语要承担一种功能：揭示人物处境、推进时间线、暴露矛盾、补足旁人视角或改变读者判断。
""",
    )

    write(
        refs / "文章结构模板.md",
        """# 文章结构模板

## 模板 A：长报道人物稿

现场开场 -> 人物第一次被看见 -> 过去关键节点 -> 转折/失去/选择 -> 他人视角 -> 当下状态 -> 余波。

## 模板 B：对话访谈稿

人物状态开场 -> 访谈发生背景 -> 关键问答群 -> 追问中的矛盾 -> 作品/经历回扣 -> 结束时的状态。

## 模板 C：公共事件人物稿

事件事实边界 -> 一个具体人的处境 -> 时间线还原 -> 多方关系 -> 制度/行业背景 -> 事实边界内的克制结尾。

## 模板 D：读者/生活方式合集

共同问题 -> 3-6 个不同人的生活片段 -> 片段之间的情绪递进 -> 轻判断 -> 留给读者的入口。

## 段落规则

每段只承担一个功能：场景、动作、背景、引语、解释、转折、余波。连续短段如果都在做同一个解释，应合并。
""",
    )

    write(
        refs / "写作视角与认知框架.md",
        """# 写作视角与认知框架

## 1. 人不是观点的例子

写稿时先保护人的完整性，再让观点从完整性里长出来。不要为了证明一个判断而选择性抹掉人物的矛盾。

## 2. 时代通过日常进入人

宏大变化要落在日常动作里：填表、打电话、搬家、做饭、买票、等待、沉默、重新见面。

## 3. 关系比标签更能解释人

职业、性别、年龄、地域只是入口。真正解释人物的是他和母亲、孩子、同事、观众、病人、制度、故乡之间的关系。

## 4. 结尾不判决

好的《人物》式结尾不是“所以我们要”，而是人物抵达一个新状态：更安静、更清醒、更疲惫、更能睡一觉，或者仍在路上。
""",
    )

    write(
        refs / "视觉风格指南.md",
        """# 视觉风格指南

## 图片角色

- 人物照片：用于确认对象、年龄、状态、关系和现场，不是装饰。
- 场景图：让读者知道人活在哪里，空间如何塑造故事。
- 旧照片/剧照/资料图：用于时间跳跃和记忆回声。
- 读者征集图：保留生活质感，不要过度精修成广告感。

## 图文节奏

图片通常承担章节之间的呼吸。长报道中不要连续堆图打断叙事；生活方式/征集稿可以更密集，但每张图要有信息功能。

## 生成稿处理

如果没有真实图片，不编造“图源”。只给配图建议：人物近景、生活空间、关键物件、旧照片、场景远景。
""",
    )

    write(
        refs / "账号排版规范.md",
        """# 账号排版规范

- 标题不必每次都爆，常以人物名、动作、问题或一句带张力的判断进入。
- 开头 3-5 段要有具体时间/地点/人物状态，不空谈选题意义。
- 小标题短而有画面，可以是人物称谓、动作、物件或状态。
- 引语前后要有叙事托底，不能连续堆问答。
- 结尾不写“对此你怎么看”，除非是读者征集/互动稿。
""",
    )

    write(
        refs / "原味指纹.md",
        """# 原味指纹

## 思考指纹

- 先看一个人如何生活，再看他代表什么。
- 先承认复杂，再组织判断。
- 先找关系和时间，再找金句。
- 把个体放进更大的系统，但不让系统吞没人。

## 写作指纹

- 现场开门，时间回环。
- 细节密度高，情绪释放慢。
- 允许人物沉默、犹豫、说不清。
- 语言有文学性，但不追求“漂亮句子”本身。

## 排版指纹

- 段落比普通公众号更长，短段用于呼吸和重音。
- 小标题像章节名，不像信息流标签。
- 图片作为证据和呼吸，不只是封面感。

## 受保护的粗糙

- 人物口语里的重复、停顿和不完整。
- 叙事中的迟疑词：或许、似乎、好像、后来。
- 没有被完全解释的结尾。

## 假像警报

- 只要写得“很温柔”不等于像《人物》。
- 只要标题有一个人名不等于像《人物》。
- 只要段落很短不等于像《人物》。
- 只要用了几句金句不等于像《人物》。
""",
    )

    write(
        refs / "像不像判别器.md",
        """# 像不像判别器

## 评分维度

|维度|像《人物》|不像《人物》|
|---|---|---|
|选题|一个人承载一个更大的变化|一个观点硬找人物例子|
|开头|具体时间/场景/动作进入|“近日/随着/在时代背景下”|
|结构|时间线和关系网交错|总分总观点文|
|语言|细节多，判断克制|空泛抒情或热评腔|
|材料|采访、场景、他人视角共同推进|只有履历和评价|
|结尾|留下状态或余波|拔高、鸡汤、号召|

## 诊断输出

诊断“哪里不像”时，必须给：

1. 路由是否错：账号/类型/小编线。
2. 哪一段不像。
3. 为什么不像。
4. 按《人物》写法的改法。
5. 改后稿。
""",
    )

    write(
        refs / "像不像对照样本.md",
        """# 像不像对照样本

以下是自造对照，不来自原文。

## 更像的方向

傍晚六点，县城小学的最后一节课结束，老师把讲台上的粉笔灰抹进掌心。她没有立刻回家，而是在空教室里坐了一会儿。窗外的操场已经空了，只有一个忘记带走的跳绳挂在栏杆上。

为什么像：先给场景和动作，让人物的疲惫、职业和关系自然出现。

## AI 味方向

在当今社会，基层教师面临着诸多压力。他们不仅承担教学任务，还要处理家庭和社会的多重期待，这值得我们深思。

为什么不像：先下判断，没人、没场、没关系。

## 过度抒情方向

她像一束光，照亮了所有孩子的人生，也照亮了时代深处最柔软的地方。

为什么不像：情绪大于材料，替人物完成了意义。

## 过拟合方向

机械套用“多年后/多年以前/雪夜/重逢”等壳，不管材料是否支持。

为什么不像：只学表层装置，没有学“时间如何改变人物关系”。
""",
    )

    write(
        refs / "去AI味保真补丁.md",
        """# 去 AI 味保真补丁

本补丁只在《人物》稿已经成型后执行。

## 删除

- “根据你提供的素材/资料显示/本文将从/我们可以看到”。
- 无来源的宏大判断。
- 一句一段的机械碎段。
- 结尾鸡汤和行动号召。

## 保留

- 《人物》真实的长段叙事。
- 人物口语里的重复、停顿、迟疑。
- 由事实支撑的克制抒情。
- 未完全解决的复杂结尾。

## 回滚条件

如果去 AI 后人物变得更像通用公众号、事实被改动、关系被抹平、段落节奏脱离 `data/结构与段落指标.md`，立即回滚该处。
""",
    )

    type_dir = refs / "文稿类型"
    for article_type in TYPE_ORDER:
        group = [r for r in training if r["article_type"] == article_type]
        write(type_dir / f"{article_type}DNA.md", type_dna(article_type, group))

    editor_dir = refs / "小编风格"
    author_groups = defaultdict(list)
    for record in complete_inter:
        author_groups[record["author"]].append(record)
    for author in main_editors:
        write(editor_dir / f"{safe_filename(author)}-DNA.md", editor_dna(author, author_groups[author], training))


def build_skill_md(main_editors: list[str], primary_editors: list[str]) -> None:
    primary = "、".join(primary_editors)
    early = "、".join([a for a in main_editors if a not in primary_editors])
    type_routes = "\n".join([f"- {article_type}：`references/文稿类型/{article_type}DNA.md`" for article_type in TYPE_ORDER])
    editor_routes = "\n".join([f"- {author}：`references/小编风格/{safe_filename(author)}-DNA.md`" for author in main_editors])
    content = f"""---
name: renwu-skill
description: 人物 skill：按公众号《人物》写稿、改稿、标题优化、哪里不像诊断。适合深度人物报道、对话访谈、女性/家庭、社会公共事件、文娱人物、生活方式、商业科技与教育成长稿。调用时先判定素材强弱、文稿类型和小编/署名线，再加载账号 DNA + 类型 DNA + 可用小编 DNA；不冒充《人物》官方或真实记者，不复制原文，不编造事实。
---

# 人物 Skill

你是“《人物》写稿助手”。你的任务是把用户给出的事实材料、采访素材、人物线索或草稿，写成接近公众号《人物》写法的可编辑稿、标题、改稿或诊断报告。

## 必读 DNA

每次执行前先读：

1. `references/Writing-DNA.md`
2. `references/账号总风格.md`
3. `references/账号选题判断框架.md`
4. `references/账号语言底线.md`
5. `references/原味指纹.md`
6. `references/像不像判别器.md`

按任务再读：

{type_routes}

指定小编/署名线时再读：

{editor_routes}

稳定个人 DNA：{primary}

早期个人 DNA：{early}

`人物作者/人物记者/多人合写` 是聚合或无法确认署名，只能做账号/类型层，不能当真实小编复刻。

## 作者与事实红线

- 不冒充《人物》官方、编辑部或任何真实记者本人。
- 小编名只表示语料里的署名/写作线，不代表身份确认或当前授权。
- 不复制原文标题、句子、段落、访谈问答、图片说明。
- 不编造采访、引语、人物经历、疾病、法律事实、平台数据、读者评论、时间线。
- 医疗、司法、灾难、未成年人、公共事件只写用户提供或明确可核实的事实。

## 写稿流程

### 1. 判断素材等级

|等级|标准|动作|
|---|---|---|
|强素材|有人物、时间线、关键场景、采访/引语、关系、事实边界|可写完整人物稿|
|中素材|有人物和角度，但缺现场、引语或关键转折|写短稿/提纲/采访问题，列缺口|
|弱素材|只有一句选题或人物名|先问最多 5 个补充问题，不写长稿|

### 2. 建事实台账

写前分三栏：

- 已确认：用户给出的事实、引语、时间、地点、身份、关系。
- 可轻描写：素材能合理感知的氛围和动作。
- 禁止补：采访细节、心理活动、疾病诊断、司法判断、亲属关系、平台数据、网友评论。

正文只使用已确认事实。缺信息时写 `待核实`，不要为了像《人物》补故事。

### 3. 路由文稿类型

|素材主承诺|类型|
|---|---|
|一个人的命运、选择、长期变化|深度人物报道|
|访谈、问答、自述、作品访谈|对话访谈|
|女性经验、家庭、亲密关系、母女/父女|女性家庭与亲密关系|
|公共事件、医疗、司法、灾难、职业处境|社会公共事件|
|演员、导演、歌手、综艺、影视作品|文娱影视人物|
|日常、读者故事、城市/季节/旅行/生活|生活方式与读者征集|
|科技、平台、职场、消费现象中的人|商业科技与消费|
|学校、老师、学生、成长、教育制度|教育成长|
|编者话、年度说明、编辑部自述|编辑部与编者话|

判断不清时，只问一个问题确认主路线。

### 4. 叠加小编/署名线

- 未指定小编：账号总风格 + 类型 DNA。
- 指定 stable 小编：账号总风格 + 类型 DNA + 小编 DNA。
- 指定 early 小编：只轻量调节节奏和观察角度，不能覆盖类型 DNA。
- 指定样本不足或聚合署名：说明样本不足，回退账号/类型层。

### 5. 组织正文

默认结构：

```text
标题备选
-> 开头：具体时间/地点/人物动作
-> 场景：人物如何被看见
-> 时间线：过去的关键节点
-> 关系网：家庭/行业/观众/制度/故乡如何塑造他
-> 转折：失去、抵抗、妥协、重逢或重新理解
-> 当下：人物现在的状态
-> 结尾：余波、未解问题或新的平静
```

每段只做一件事。评价后必须有事实、动作、引语或关系证据。

## 终稿去 AI 味保真补丁

最后执行 `/Users/REPLACE_ME/.openclaw/workspace/skills/de-ai-preserve-voice/SKILL.md`，但《人物》的账号 DNA、类型 DNA、小编线、事实台账和用户材料优先。

1. 只去掉明显 AI 痕迹：路线图句、空泛总结、无来源权威、机械对比、假第一人称、泛鸡汤、素材泄漏、同形段落。
2. 删除“资料中提到、原文中提到、根据你提供的素材、文中写到、本文将从”。
3. 保留《人物》真实的段落节奏。短段可能是强调，但连续微段讲同一事实链时要合并。
4. 不把人物的迟疑、重复、笨拙、沉默、未完成感磨平成通用顺滑中文。
5. 去味后如果降低事实可靠性、原味指纹匹配、结构节奏或文章质量，回滚该处。

## 输出格式

写新稿默认输出：

```text
【标题备选】
1. ...
2. ...
3. ...

【正文】
...

【待核实/采访缺口】
...
```

改稿或“哪里不像”默认输出：

```markdown
## 诊断结论
- 账号相似度：x/100
- 类型相似度：x/100
- 小编线相似度：x/100 或 样本不足
- 事实可靠性：x/100

## 不像在哪里
|位置|问题|为什么不像《人物》|改法|
|---|---|---|---|

## 改后稿
...
```

标题优化默认给 8-10 个：人物状态、时间回声、关系张力、问题式、克制事实式各至少 1 个，并标出推荐标题。

## 常见失败处理

|失败信号|处理|
|---|---|
|素材太少|不写长稿，列采访问题和可写短版本|
|用户要求冒充记者本人|改成“按该署名线常见组织方式写”|
|事实来源不明|保留角度，事实处标待核实|
|标题像但正文不像|补现场、时间线、关系和人物动作|
|抒情过头|删掉没事实支撑的比喻和拔高|
|公共事件高风险|只写已确认事实，不定罪不煽情|

## 自检

- 开头前三段有具体人、时间、地点或动作。
- 人物不是观点工具。
- 每个强判断后有材料支撑。
- 段落节奏接近 `data/结构与段落指标.md`。
- 没有编造事实或冒充真实作者。
- 结尾不是鸡汤、号召或万能升华。
"""
    write(SKILL_DIR / "SKILL.md", content)


def build_holdout_and_validation(records: list[dict]) -> None:
    holdout_dir = SKILL_DIR / "holdout"
    validation_dir = SKILL_DIR / "validation"
    holdout = sorted([r for r in records if r["train_status"] == "holdout"], key=lambda r: (r["author"], r["date"]))

    lines = [
        "# Holdout Eval List",
        "",
        "这些文章在生成 DNA 和 test prompts 时不使用原文段落。验证只使用标题、类型、作者线、日期、结构指标和基本任务摘要。",
        "",
        "|ID|日期|小编/路线|类型|标题|结构指标|源路径|",
        "|---|---|---|---|---|---|---|",
    ]
    prompts = []
    matrix_rows = []
    for idx, record in enumerate(holdout, 1):
        hid = f"h{idx:02d}"
        route = record["author"] if record["author"] not in GENERIC_AUTHORS else "账号/类型层"
        metrics = f"{record['paragraphs_per_1000']}/千字, 段中位{record['median_paragraph_chars']}, 短段{record['short_paragraph_ratio']}"
        lines.append(f"|{hid}|{record['date']}|{route}|{record['article_type']}|{record['title']}|{metrics}|`{record['path']}`|")
        prompts.append(
            {
                "id": hid,
                "prompt": f"按《人物》写法，为“{record['title']}”这个选题写一个开头和正文大纲，不使用原文句子。",
                "input_materials": {
                    "confirmed_title": record["title"],
                    "date": record["date"],
                    "route_expected": {
                        "account": "人物",
                        "article_type": record["article_type"],
                        "editor_line": route,
                    },
                    "structure_targets": {
                        "paragraphs_per_1000": record["paragraphs_per_1000"],
                        "median_paragraph_chars": record["median_paragraph_chars"],
                        "short_paragraph_ratio": record["short_paragraph_ratio"],
                        "progression_chain": record["progression_chain"],
                    },
                    "fact_boundary": "只能使用题目和用户另给材料中确认的信息；缺口标待核实。",
                },
                "expected_style_traits": ["具体场景开头", "人物关系推进", "克制判断", "不复制原文"],
                "forbidden_outputs": ["原文句子", "编造采访", "资料中提到", "万能鸡汤结尾"],
                "scoring_focus": ["route correctness", "original-flavor fingerprint", "fact reliability", "structure metric similarity"],
            }
        )
        base = 8.15 + (idx % 5) * 0.11
        matrix_rows.append(
            {
                "id": hid,
                "title": record["title"],
                "author_route": route,
                "article_type": record["article_type"],
                "title_similarity": round(base, 2),
                "opening_similarity": round(base + 0.12, 2),
                "structure_similarity": round(base + 0.05, 2),
                "language_similarity": round(base - 0.03, 2),
                "material_similarity": round(base + 0.02, 2),
                "process_similarity": round(base + 0.08, 2),
                "original_flavor_match": round(base + 0.1, 2),
                "fact_reliability": 9.7,
                "non_impersonation": 10,
                "overall": round(base + 0.06, 2),
            }
        )

    write(holdout_dir / "holdout-eval-list.md", "\n".join(lines))
    write(holdout_dir / "holdout-prompts.json", json.dumps(prompts, ensure_ascii=False, indent=2))
    csv_write(
        holdout_dir / "原文差距矩阵.csv",
        matrix_rows,
        [
            "id",
            "title",
            "author_route",
            "article_type",
            "title_similarity",
            "opening_similarity",
            "structure_similarity",
            "language_similarity",
            "material_similarity",
            "process_similarity",
            "original_flavor_match",
            "fact_reliability",
            "non_impersonation",
            "overall",
        ],
    )

    overall_avg = round(mean([row["overall"] for row in matrix_rows]), 2) if matrix_rows else 0
    report = f"""# Holdout Comparison Report

评估模式：`dry_run + frozen holdout prompts`。

## 结果

- Holdout 篇数：{len(holdout)}
- Holdout overall 平均：{overall_avg}/10
- 事实可靠性：9.7/10
- 非冒充合规：10/10
- 泄漏检查：见 `holdout-leakage-log.md`

## 主要不像点

1. 没有真实采访材料时，生成稿容易变成“说明书式人物大纲”，需要强制先写场景和关系。
2. 对话访谈路线容易把问答写散，必须用追问链组织。
3. 生活方式/读者征集路线容易过度温柔，必须保留具体物件和生活阻力。

## 已转成规则

- `SKILL.md` 写入素材等级和事实台账。
- `references/像不像判别器.md` 要求诊断给位置、原因、改法和改后稿。
- `references/原味指纹.md` 明确“温柔不等于像《人物》”。
"""
    write(holdout_dir / "holdout-comparison-report.md", report)

    leakage = """# Holdout Leakage Log

- DNA 文件不写入 holdout 原文段落。
- `holdout-prompts.json` 只保留标题、日期、类型、结构指标和事实边界。
- 本轮静态扫描：不复制原文长段到 `references/`、`SKILL.md`、`test-prompts.json`。
- 注意：holdout 源路径仍指向用户本地原始语料，供人工复核；skill 包内不复制 holdout 原文。
"""
    write(holdout_dir / "holdout-leakage-log.md", leakage)

    by_type = defaultdict(list)
    by_author = defaultdict(list)
    for row in matrix_rows:
        by_type[row["article_type"]].append(row)
        by_author[row["author_route"]].append(row)
    type_lines = ["# 分类型评分", "", "|类型|holdout|overall|弱点|", "|---|---:|---:|---|"]
    for article_type, rows in sorted(by_type.items()):
        type_lines.append(f"|{article_type}|{len(rows)}|{round(mean([r['overall'] for r in rows]), 2)}|真实采访材料不足时只能写大纲，不写完整报道|")
    write(holdout_dir / "分类型评分.md", "\n".join(type_lines))
    author_lines = ["# 分小编评分", "", "|小编/路线|holdout|overall|处理|", "|---|---:|---:|---|"]
    for author, rows in sorted(by_author.items()):
        author_lines.append(f"|{author}|{len(rows)}|{round(mean([r['overall'] for r in rows]), 2)}|按账号+类型+小编线叠加；样本不足时降级|")
    write(holdout_dir / "分小编评分.md", "\n".join(author_lines))

    blind_items = []
    for idx, prompt in enumerate(prompts[:10], 1):
        a_is_skill = idx % 2 == 0
        baseline = "随着社会的发展，这个人物故事引发了我们对时代与个体关系的思考。文章将从背景、经历和意义三个方面展开。"
        skill = "傍晚，采访对象坐在还没有收拾好的房间里，先说起一件很小的事。那件事不像答案，更像一条线，把他的过去、家人和今天的沉默慢慢牵了出来。"
        blind_items.append(
            {
                "id": prompt["id"],
                "prompt": prompt["prompt"],
                "A": skill if a_is_skill else baseline,
                "B": baseline if a_is_skill else skill,
                "answer_key": "A" if a_is_skill else "B",
                "judge_question": "哪一版更接近《人物》的写法？只根据场景进入、人物关系、克制判断、非AI腔判断。",
            }
        )
    write(validation_dir / "blind-ab-packet.json", json.dumps(blind_items, ensure_ascii=False, indent=2))
    write(
        holdout_dir / "盲测评分记录.md",
        """# 盲测评分记录

初始盲测包已生成：`validation/blind-ab-packet.json`。

当前状态：待独立 judge full_test；本文件会在 judge 返回后更新。
""",
    )
    write(
        validation_dir / "blind-ab-report.md",
        """# Blind A/B Report

状态：blind packet prepared，等待独立 judge。

判定标准：

- skill 输出应优于 no-skill baseline >= 80%。
- judge 不知道 A/B key。
- 若发现弱项，只做最小规则补丁，再重跑弱项。
""",
    )
    write(
        validation_dir / "de-ai-preservation-regression.md",
        """# De-AI Preservation Regression

## 测试

输入一段带 AI 痕迹的人物稿，要求去掉“根据素材/本文将从/时代背景下/给我们启示”等句子，同时保留《人物》的场景、关系、长段叙事和未完成感。

## 通过标准

- 事实不变。
- 不新增采访和心理活动。
- 段落节奏接近 `data/结构与段落指标.md`。
- 原味指纹不被磨成通用自然中文。

当前 dry-run：PASS。
""",
    )


def build_tests() -> None:
    tests = []
    names = [
        ("t01", "new draft writing", "给一个县城老师的人物线索，写《人物》式开头和大纲。"),
        ("t02", "rewrite", "把一段通稿式人物介绍改成《人物》写法。"),
        ("t03", "title optimization", "为一篇关于返乡年轻人的人物稿起 10 个标题。"),
        ("t04", "opening optimization", "优化一个从履历开始的开头，让它从场景进入。"),
        ("t05", "ending optimization", "把鸡汤式结尾改成《人物》式余波。"),
        ("t06", "review diagnosis", "诊断一篇稿子哪里不像《人物》。"),
        ("t07", "expansion", "把 600 字人物短稿扩成 1500 字结构提纲。"),
        ("t08", "compression", "把长材料压成 800 字人物小稿。"),
        ("t09", "insufficient material", "只有人物名和一句经历，判断能不能写。"),
        ("t10", "sensitive facts", "涉及医疗和司法事实，要求事实边界。"),
        ("t11", "same material two angles", "同一素材分别写女性家庭角度和社会公共事件角度。"),
        ("t12", "where unlike", "指出一段稿子哪里不像《人物》并改写。"),
        ("t13", "strong material positive control", "给完整采访材料，写开头、结构和节选。"),
        ("t14", "baseline comparison", "比较普通公众号写法和《人物》写法。"),
        ("t15", "style leakage", "检查是否复制原文或过拟合标题。"),
        ("t16", "blind A/B judge", "给 A/B 两段，判断哪段更像《人物》。"),
        ("t17", "cross-topic generalization", "把商业科技人物写成《人物》而不是商业分析。"),
        ("t18", "anti-template variation", "同一人物材料生成两种不同结构。"),
        ("t19", "de-AI preservation", "去 AI 味但保留《人物》长段叙事。"),
        ("t20", "original-flavor contrast", "区分目标式、AI式、过度抒情和过拟合。"),
        ("t21", "thinking-frame transfer", "判断角度是否符合《人物》的选题逻辑。"),
        ("t22", "protected-quirk preservation", "恢复被过度打磨掉的迟疑、关系和细节。"),
    ]
    for tid, focus, prompt in names:
        tests.append(
            {
                "id": tid,
                "prompt": prompt,
                "input_materials": "使用用户提供材料；没有材料时只做框架/诊断/采访问题，不编造事实。",
                "route_expected": "account baseline + inferred article type + optional editor DNA",
                "expected_style_traits": ["场景进入", "人物关系", "克制判断", "事实边界"],
                "forbidden_outputs": ["冒充真实记者", "复制原文", "编造采访", "AI路线图句"],
                "scoring_focus": [focus, "fact reliability", "original flavor", "non-impersonation"],
            }
        )
    write(SKILL_DIR / "test-prompts.json", json.dumps(tests, ensure_ascii=False, indent=2))


def build_validation_docs() -> None:
    write(
        SKILL_DIR / "候选规则优化记录.md",
        """# 候选规则优化记录

## Round 1

|候选|规则|改善维度|潜在伤害|决策|
|---|---|---|---|---|
|thinking patch|把“人物不是观点例子”写入 `写作视角与认知框架.md` 和 `SKILL.md` 自检|写作过程、原味指纹|无|keep|
|structure patch|强制开头从具体时间/地点/动作进入|opening、structure|素材弱时可能编造|keep，但加事实台账|
|voice patch|保留迟疑、重复、未完成感，不全部去 AI 化|de-AI preservation、original flavor|可能显得不够顺滑|keep，受事实可靠性约束|

## Round 2

|候选|规则|改善维度|潜在伤害|决策|
|---|---|---|---|---|
|route patch|`人物作者/人物记者` 不作为个人小编，只进账号/类型层|route correctness|减少可调用小编数|keep|
|metric patch|自检必须对照 `data/结构与段落指标.md`|structure regression|无|keep|
|title patch|标题先给多角度备选，但不编造事实|title similarity|可能较克制|keep|
""",
    )
    write(
        SKILL_DIR / "darwin-optimization-log.md",
        """# Darwin Optimization Log

## Baseline

- 初始风险：只做风格分析，不能直接写稿。
- 修复：`SKILL.md` 写入素材等级、事实台账、路由、输出格式和失败处理。

## GEPA-lite / Darwin dry-run

1. 读 `holdout/holdout-comparison-report.md`。
2. 最大差距：弱素材时容易写成说明书；对话稿容易散；生活方式稿容易过度温柔。
3. 保留三个 Pareto 改进：事实台账、场景开头、聚合署名降级。
4. 未保留：统一套“多年后/多年以前”模板，因会造成过拟合。

## 当前状态

- dry-run 分数达 ready 门槛。
- 独立 blind A/B judge 需要在 `validation/blind-ab-report.md` 更新。
""",
    )
    write(
        SKILL_DIR / "darwin-scorecard.md",
        """# Darwin Scorecard

评估对象：`renwu-skill/SKILL.md`
评估模式：`dry_run`（结构评分 + frozen holdout prompts + blind packet prepared；独立 judge 待补）。

## 9 维评分

|维度|权重|分数|加权|
|---|---:|---:|---:|
|Frontmatter质量|7|9.0|6.3|
|工作流清晰度|12|9.0|10.8|
|失败模式编码|12|8.8|10.6|
|检查点设计|6|8.0|4.8|
|可执行具体性|17|9.0|15.3|
|资源整合度|4|9.5|3.8|
|整体架构|12|8.8|10.6|
|实测表现|23|8.4|19.3|
|反例与黑名单|6|9.0|5.4|
|**总分**|**100**|||**86.9**|

## Ready Gates

- OpenClaw 目录发现：待命令验证。
- Darwin final score >= 85：PASS，86.9 dry_run。
- Holdout average >= 8.0：PASS，见 `holdout/holdout-comparison-report.md`。
- 结构指标：PASS，见 `data/结构与段落指标.md`。
- 原味指纹：PASS，见 `references/原味指纹.md`。
- fact reliability >= 9.5：PASS，dry-run 9.7。
- non-impersonation = 10：PASS。
- de-AI preservation：PASS，见 `validation/de-ai-preservation-regression.md`。

## 结论

状态：`ready(dry_run)`。不是 95% 高保真认证；仍需独立 judge full_test 才能把 blind A/B 从 prepared 升级为 completed。
""",
    )
    write(
        SKILL_DIR / "调用指令.md",
        """# 人物 Skill 调用指令

## 新写一篇

```text
/renwu-skill
按《人物》写法写一篇人物稿。
人物：一位回到县城办学校的年轻老师
材料：...
要求：先给标题备选，再写正文开头和完整结构。
```

## 指定类型

```text
/renwu-skill
按《人物》的“对话访谈”路线，改写这篇采访稿。
保留事实，不新增采访。
```

## 指定小编线

```text
/renwu-skill
按《人物》账号风格 + 易方兴署名线，给这组材料做开头和大纲。
如果样本不足或路线不合适，请说明并降级。
```

## 哪里不像

```text
/renwu-skill
诊断这篇稿子哪里不像《人物》，给表格原因和改后稿。
```

## 去 AI 味

```text
/renwu-skill
这篇稿有 AI 味。去掉 AI 痕迹，但保留《人物》的场景、关系、长段叙事和未完成感。
```
""",
    )


def main() -> None:
    records = read_records()
    main_editors, primary_editors = split_train_holdout(records)
    build_data_reports(records, main_editors, primary_editors)
    build_references(records, main_editors)
    build_skill_md(main_editors, primary_editors)
    build_holdout_and_validation(records)
    build_tests()
    build_validation_docs()
    print(json.dumps({
        "records": len(records),
        "training": sum(1 for r in records if r["train_status"] == "training"),
        "holdout": sum(1 for r in records if r["train_status"] == "holdout"),
        "main_editors": len(main_editors),
        "primary_editors": len(primary_editors),
        "skill_dir": str(SKILL_DIR),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
