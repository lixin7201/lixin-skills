#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median


CORPUS_ROOT = Path("/Users/lixin/Documents/学习/重点学习公众号/半佛仙人/半佛仙人")
OUT_DIR = Path("/Users/lixin/.openclaw/workspace/skills/banfo-skill")
NOW = "2026-07-05"


INTERACTION_RE = re.compile(r"(阅读|点赞|转发|喜欢|留言)\s+([0-9.]+)\s*(万)?")
META_RE = re.compile(r"^([a-zA-Z_]+):\s*\"?(.*?)\"?\s*$", re.M)
SENTENCE_RE = re.compile(r"[^。！？!?；;]+[。！？!?；;]?")
IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
SECTION_RE = re.compile(r"^\s*\*\*\\?([0-9]{1,2}|[一二三四五六七八九十]+)\\?\*\*\s*$", re.M)


STOP_CHARS = set("的一是在了和有就不人都说这也要到为上中下很但而以把被与及或并一个我们你们他们自己没有什么所以因为如果还是其实就是不是")
FOOTER_MARKERS = [
    "## 互动数据",
    "公众号：半佛仙人",
    "B站：硬核的半佛仙人",
    "微博：半佛仙人",
    "知乎：半佛仙人",
    "点击关注下方账号",
    "感谢大家一直以来的阅读",
    "感谢你的阅读",
]


@dataclass
class Article:
    idx: int
    title: str
    author: str
    date: str
    year: int
    url: str
    path: str
    chars: int
    paragraphs: int
    images: int
    sections: int
    read: int | None
    like: int | None
    share: int | None
    favorite: int | None
    comment: int | None
    raw_score: float | None = None
    global_pct: float | None = None
    year_pct: float | None = None
    early_bonus: float = 0.0
    weighted_score: float | None = None
    split: str = "excluded"
    article_type: str = ""
    hook_type: str = ""


def parse_number(value: str, wan: str | None) -> int:
    n = float(value)
    if wan:
        n *= 10000
    return int(n)


def parse_meta(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    return {k: v for k, v in META_RE.findall(text[:end])}


def remove_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            return text[end + 4 :]
    return text


def clean_body(text: str) -> str:
    body = remove_frontmatter(text)
    for marker in FOOTER_MARKERS:
        pos = body.find(marker)
        if pos >= 0:
            body = body[:pos]
    body = re.sub(r"^# .*$", "", body, flags=re.M)
    body = re.sub(r"^> .*$", "", body, flags=re.M)
    body = IMG_RE.sub("", body)
    body = re.sub(r"\[原文链接\]\([^)]+\)", "", body)
    body = re.sub(r"\*\*【?这是半佛仙人的第[0-9]+篇原创】?\*\*", "", body)
    body = re.sub(r"这是半佛仙人的第[0-9]+篇原创", "", body)
    body = re.sub(r"\\[-—]{5,}", "", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def classify_article(title: str) -> str:
    if any(x in title for x in ["电影", "剧", "王者", "游戏", "B站", "综艺", "唐探", "射雕", "黑神话", "繁城"]):
        return "文娱产品拆解"
    if any(x in title for x in ["美团", "京东", "阿里", "腾讯", "拼多多", "沃尔玛", "盒马", "山姆", "西贝", "胖东来", "瑞幸", "小米", "华为", "大疆", "比亚迪", "理想", "蔚来", "抖音", "快手", "支付宝"]):
        return "商业公司拆解"
    if any(x in title for x in ["消费", "品牌", "奶茶", "酒店", "香水", "护肤", "咖啡", "羽绒服", "预制", "餐", "拉面", "果粒橙", "营养快线"]):
        return "消费品牌观察"
    if any(x in title for x in ["父母", "孩子", "大学生", "职场", "老板", "打工", "社畜", "相亲", "爱情", "结婚", "家庭"]):
        return "社会心理吐槽"
    if any(x in title for x in ["黑产", "骗局", "身份", "金融", "征信", "贷款", "律师", "竞业", "隐私", "违法"]):
        return "风险黑产科普"
    if any(x in title for x in ["AI", "科技", "芯片", "汽车", "新能源", "机器人", "鸿蒙", "英伟达"]):
        return "科技产业观察"
    return "热点观点杂谈"


def classify_hook(title: str) -> str:
    if "？" in title or "吗" in title:
        return "反常识提问"
    if any(x in title for x in ["疯", "傻眼", "离谱", "害怕", "笑", "凶猛", "开光", "救"]):
        return "情绪夸张判断"
    if any(x in title for x in ["凭什么", "为什么", "本质", "背后"]):
        return "追问机制"
    if "，" in title or "," in title:
        return "对象加判断"
    return "直给判断"


def load_articles() -> list[Article]:
    articles: list[Article] = []
    for i, path in enumerate(sorted(CORPUS_ROOT.glob("*/*.md")), start=1):
        text = path.read_text(encoding="utf-8", errors="ignore")
        meta = parse_meta(text)
        title = meta.get("title") or path.stem
        date = meta.get("date", "")
        year_match = re.search(r"(\d{4})", date) or re.search(r"/(\d{8})_", str(path))
        year = int(year_match.group(1)[:4]) if year_match else 0
        body = clean_body(text)
        interactions = {k: parse_number(v, wan) for k, v, wan in INTERACTION_RE.findall(text[-1200:])}
        images = len(IMG_RE.findall(text))
        paragraphs = len([p for p in body.splitlines() if p.strip() and not p.strip().startswith("**")])
        article = Article(
            idx=i,
            title=title,
            author=meta.get("author", ""),
            date=date,
            year=year,
            url=meta.get("url", ""),
            path=str(path),
            chars=len(re.sub(r"\s+", "", body)),
            paragraphs=paragraphs,
            images=images,
            sections=len(SECTION_RE.findall(body)),
            read=interactions.get("阅读"),
            like=interactions.get("点赞"),
            share=interactions.get("转发"),
            favorite=interactions.get("喜欢"),
            comment=interactions.get("留言"),
            article_type=classify_article(title),
            hook_type=classify_hook(title),
        )
        articles.append(article)
    return articles


def percentile_ranks(items: list[Article], key: str) -> dict[int, float]:
    values = sorted((getattr(a, key), a.idx) for a in items if getattr(a, key) is not None)
    n = len(values)
    if n <= 1:
        return {idx: 1.0 for _, idx in values}
    ranks: dict[int, float] = {}
    for rank, (_, idx) in enumerate(values, start=1):
        ranks[idx] = (rank - 1) / (n - 1)
    return ranks


def score_articles(articles: list[Article]) -> tuple[list[Article], list[Article]]:
    scored = [a for a in articles if a.read is not None and a.like is not None]
    for a in scored:
        # ponytail: log-weighted blend; swap for platform-specific weights if raw fan counts become available.
        a.raw_score = (
            0.35 * math.log1p(a.read or 0)
            + 0.25 * math.log1p(a.like or 0)
            + 0.25 * math.log1p(a.share or 0)
            + 0.10 * math.log1p(a.favorite or 0)
            + 0.05 * math.log1p(a.comment or 0)
        )
    global_pct = percentile_ranks(scored, "raw_score")
    by_year: dict[int, list[Article]] = defaultdict(list)
    for a in scored:
        by_year[a.year].append(a)
    year_pct: dict[int, float] = {}
    for group in by_year.values():
        year_pct.update(percentile_ranks(group, "raw_score"))
    for a in scored:
        a.global_pct = global_pct[a.idx]
        a.year_pct = year_pct[a.idx]
        a.early_bonus = min(0.12, max(0.0, (2023 - a.year) * 0.025))
        a.weighted_score = 0.55 * a.global_pct + 0.35 * a.year_pct + a.early_bonus
    ranked = sorted(scored, key=lambda x: (x.weighted_score or 0, x.raw_score or 0), reverse=True)
    top_n = len(scored) // 2
    top = ranked[:top_n]
    # Holdout is picked before distillation: representative high-score articles across years/types.
    holdout: list[Article] = []
    used_types: set[str] = set()
    used_years: set[int] = set()
    for a in top:
        if len(holdout) >= 10:
            break
        if a.article_type not in used_types or a.year not in used_years:
            holdout.append(a)
            used_types.add(a.article_type)
            used_years.add(a.year)
    for a in top:
        if len(holdout) >= 10:
            break
        if a not in holdout:
            holdout.append(a)
    holdout_ids = {a.idx for a in holdout}
    for a in articles:
        if a.idx in holdout_ids:
            a.split = "holdout"
        elif a in top:
            a.split = "train"
        elif a in scored:
            a.split = "interaction_bottom_50"
        else:
            a.split = "no_interaction"
    train = [a for a in top if a.idx not in holdout_ids]
    return train, holdout


def body_for(path: str) -> str:
    return clean_body(Path(path).read_text(encoding="utf-8", errors="ignore"))


def ngram_stats(train: list[Article]) -> dict[str, list[tuple[str, int]]]:
    counts: dict[int, Counter[str]] = {2: Counter(), 3: Counter(), 4: Counter()}
    punct = Counter()
    sent_lengths: list[int] = []
    para_lengths: list[int] = []
    for a in train:
        body = body_for(a.path)
        punct.update(ch for ch in body if ch in "。！？；，：、“”《》（）")
        for sent in SENTENCE_RE.findall(body):
            n = len(re.sub(r"\s+", "", sent))
            if n:
                sent_lengths.append(n)
        for para in body.splitlines():
            para = para.strip()
            if para and not para.startswith("**"):
                para_lengths.append(len(re.sub(r"\s+", "", para)))
        chars = re.findall(r"[\u4e00-\u9fff]", body)
        for n in counts:
            for i in range(0, max(0, len(chars) - n + 1)):
                gram = "".join(chars[i : i + n])
                if any(c in STOP_CHARS for c in gram):
                    continue
                counts[n][gram] += 1
    return {
        "top_2gram": counts[2].most_common(60),
        "top_3gram": counts[3].most_common(60),
        "top_4gram": counts[4].most_common(60),
        "punctuation": punct.most_common(),
        "sentence": [
            ("avg", round(mean(sent_lengths), 2)),
            ("median", round(median(sent_lengths), 2)),
            ("short_le_15_pct", round(sum(x <= 15 for x in sent_lengths) / len(sent_lengths), 4)),
            ("long_ge_50_pct", round(sum(x >= 50 for x in sent_lengths) / len(sent_lengths), 4)),
        ],
        "paragraph": [
            ("avg", round(mean(para_lengths), 2)),
            ("median", round(median(para_lengths), 2)),
        ],
    }


def write_csv(path: Path, rows: list[Article]) -> None:
    fields = list(asdict(rows[0]).keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def md_table(rows: list[list[object]], headers: list[str]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(out)


def write_lists(articles: list[Article], train: list[Article], holdout: list[Article]) -> None:
    data = OUT_DIR / "data"
    reports = OUT_DIR / "reports"
    data.mkdir(exist_ok=True)
    reports.mkdir(exist_ok=True)
    write_csv(data / "文章元数据总表.csv", articles)
    write_csv(data / "training-corpus-list.csv", train)
    write_csv(data / "holdout-eval-list.csv", holdout)

    def short_rows(rows: list[Article]) -> list[list[object]]:
        return [
            [
                a.date[:10],
                a.title.replace("|", "\\|"),
                a.article_type,
                f"{a.weighted_score:.3f}" if a.weighted_score is not None else "",
                a.read or "",
                a.like or "",
                a.share or "",
                a.favorite or "",
                a.comment or "",
                a.path,
            ]
            for a in rows
        ]

    (data / "training-corpus-list.md").write_text(
        "# Training Corpus List\n\n"
        f"- 选择口径：有互动数据的 {sum(1 for a in articles if a.read is not None)} 篇文章中，加权互动分前 50%。\n"
        f"- 前 50% 候选：{len(train) + len(holdout)} 篇。\n"
        f"- 已冻结 holdout：{len(holdout)} 篇，不进入训练。\n"
        f"- 实际训练：{len(train)} 篇。\n\n"
        + md_table(short_rows(train[:120]), ["date", "title", "type", "score", "read", "like", "share", "favorite", "comment", "path"])
        + "\n\n> 完整列表见 `training-corpus-list.csv`。\n",
        encoding="utf-8",
    )
    (data / "holdout-eval-list.md").write_text(
        "# Holdout Eval List\n\n"
        "这些文章在蒸馏前冻结，只使用标题、主题、基础素材和结构标签做验证；原文正文不写入 DNA 文件和测试 prompt。\n\n"
        + md_table(short_rows(holdout), ["date", "title", "type", "score", "read", "like", "share", "favorite", "comment", "path"])
        + "\n",
        encoding="utf-8",
    )


def write_audit(articles: list[Article], train: list[Article], holdout: list[Article], stats: dict[str, object]) -> None:
    years = defaultdict(lambda: [0, 0, 0, 0])
    for a in articles:
        years[a.year][0] += 1
        if a.read is not None:
            years[a.year][1] += 1
        if a.split == "train":
            years[a.year][2] += 1
        if a.split == "holdout":
            years[a.year][3] += 1
    type_counts = Counter(a.article_type for a in train)
    hook_counts = Counter(a.hook_type for a in train)
    report = [
        "# 语料质量报告",
        "",
        f"- 审计日期：{NOW}",
        f"- 原始目录：`{CORPUS_ROOT}`",
        f"- 总文章数：{len(articles)}",
        f"- 有互动数据文章：{sum(1 for a in articles if a.read is not None)}",
        f"- 无互动数据文章：{sum(1 for a in articles if a.read is None)}（主要集中在 2018-2020）",
        f"- 互动前 50% 候选：{len(train) + len(holdout)}",
        f"- 训练集：{len(train)}",
        f"- holdout：{len(holdout)}",
        f"- 训练集正文中位字数：{int(median(a.chars for a in train))}",
        f"- 训练集平均配图数：{round(mean(a.images for a in train), 1)}",
        "",
        "## 互动加权口径",
        "",
        "基础互动分使用 log 加权，降低 10万+ 阅读的天花板效应：",
        "",
        "`raw = 0.35*阅读 + 0.25*点赞 + 0.25*转发 + 0.10*喜欢 + 0.05*留言`，各项先做 `log1p`。",
        "",
        "最终分：`0.55*全局百分位 + 0.35*同年百分位 + 早期加成`。早期加成按年份给 2021-2022 的好文少量补偿，上限 0.12。",
        "",
        "## 年份分布",
        "",
        md_table([[y, *years[y]] for y in sorted(years)], ["year", "total", "with_interaction", "train", "holdout"]),
        "",
        "## 训练集类型分布",
        "",
        md_table([[k, v] for k, v in type_counts.most_common()], ["type", "train_count"]),
        "",
        "## 标题 hook 分布",
        "",
        md_table([[k, v] for k, v in hook_counts.most_common()], ["hook", "train_count"]),
        "",
        "## 表层节奏统计",
        "",
        md_table(stats["sentence"], ["metric", "value"]),
        "",
        md_table(stats["paragraph"], ["metric", "value"]),
        "",
        "## 说明",
        "",
        "- 2018-2020 老文不参与互动前 50% 排名，因为源文件没有互动字段；它们只作为风格背景和历史跨度证据。",
        "- holdout 文章在蒸馏前冻结，后续验证只使用题材与素材摘要，不把原文段落写进 Skill。",
        "- 原文语料仍保留在用户本地目录；生成 Skill 不复制原文正文。",
    ]
    (OUT_DIR / "data" / "语料质量报告.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def write_stats(train: list[Article], stats: dict[str, object]) -> None:
    analysis = OUT_DIR / "data" / "analysis-statistics.json"
    payload = {
        "top_titles": [asdict(a) for a in sorted(train, key=lambda x: x.weighted_score or 0, reverse=True)[:80]],
        "ngrams": stats,
    }
    analysis.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    articles = load_articles()
    train, holdout = score_articles(articles)
    stats = ngram_stats(train)
    write_lists(articles, train, holdout)
    write_audit(articles, train, holdout, stats)
    write_stats(train, stats)
    print(json.dumps({
        "total": len(articles),
        "with_interaction": sum(1 for a in articles if a.read is not None),
        "train": len(train),
        "holdout": len(holdout),
        "out_dir": str(OUT_DIR),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
