from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False

try:
    from wordcloud import WordCloud
except ImportError:
    WordCloud = None

from config import CHART_DIR
from src.analyzer import citation_distribution


def find_chinese_font():
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    for font in candidates:
        if Path(font).exists():
            return font
    return None


def ensure_chart_dir(chart_dir=CHART_DIR):
    Path(chart_dir).mkdir(parents=True, exist_ok=True)


def save_year_trend(stats, chart_dir=CHART_DIR):
    ensure_chart_dir(chart_dir)
    path = Path(chart_dir) / "year_trend.png"
    year_counts = stats.get("year_counts", {})

    plt.figure(figsize=(8, 4.5))
    if year_counts:
        years = list(year_counts.keys())
        counts = list(year_counts.values())
        plt.plot(years, counts, marker="o", color="#2563eb")
        plt.xticks(years, rotation=30)
    else:
        plt.text(0.5, 0.5, "暂无年份数据", ha="center", va="center")
    plt.title("年度发文趋势")
    plt.xlabel("年份")
    plt.ylabel("论文数量")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return path.name


def save_keyword_bar(stats, chart_dir=CHART_DIR):
    ensure_chart_dir(chart_dir)
    path = Path(chart_dir) / "keyword_bar.png"
    keywords = stats.get("top_keywords", [])[:10]

    plt.figure(figsize=(8, 4.5))
    if keywords:
        labels = [item[0] for item in keywords][::-1]
        values = [item[1] for item in keywords][::-1]
        plt.barh(labels, values, color="#16a34a")
    else:
        plt.text(0.5, 0.5, "暂无关键词数据", ha="center", va="center")
    plt.title("高频关键词")
    plt.xlabel("出现次数")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return path.name


def save_citation_chart(papers, chart_dir=CHART_DIR):
    ensure_chart_dir(chart_dir)
    path = Path(chart_dir) / "citation_distribution.png"
    dist = citation_distribution(papers)

    plt.figure(figsize=(8, 4.5))
    plt.bar(list(dist.keys()), list(dist.values()), color="#f59e0b")
    plt.title("引用次数分布")
    plt.xlabel("引用次数")
    plt.ylabel("论文数量")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return path.name


def save_journal_bar(stats, chart_dir=CHART_DIR):
    ensure_chart_dir(chart_dir)
    path = Path(chart_dir) / "journal_bar.png"
    journals = stats.get("top_journals", [])[:8]

    plt.figure(figsize=(8, 4.5))
    if journals:
        labels = [item[0][:28] + ("..." if len(item[0]) > 28 else "") for item in journals][::-1]
        values = [item[1] for item in journals][::-1]
        plt.barh(labels, values, color="#7c3aed")
    else:
        plt.text(0.5, 0.5, "暂无期刊数据", ha="center", va="center")
    plt.title("主要期刊 / 来源分布")
    plt.xlabel("论文数量")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return path.name


def save_author_bar(stats, chart_dir=CHART_DIR):
    ensure_chart_dir(chart_dir)
    path = Path(chart_dir) / "author_bar.png"
    authors = stats.get("top_authors", [])[:8]

    plt.figure(figsize=(8, 4.5))
    if authors:
        labels = [item[0][:20] + ("..." if len(item[0]) > 20 else "") for item in authors][::-1]
        values = [item[1] for item in authors][::-1]
        plt.barh(labels, values, color="#0891b2")
    else:
        plt.text(0.5, 0.5, "暂无作者数据", ha="center", va="center")
    plt.title("高产作者排行")
    plt.xlabel("论文数量")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return path.name


def save_source_pie(stats, chart_dir=CHART_DIR):
    ensure_chart_dir(chart_dir)
    path = Path(chart_dir) / "source_pie.png"
    sources = stats.get("source_counts", [])

    plt.figure(figsize=(8, 4.5))
    if sources:
        labels = [item[0] for item in sources]
        values = [item[1] for item in sources]
        colors = ["#2563eb", "#0f8f68", "#f59e0b", "#be3b62"]
        plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors[: len(values)])
        plt.title("数据源占比")
    else:
        plt.text(0.5, 0.5, "暂无数据源信息", ha="center", va="center")
        plt.axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return path.name


def save_yearly_avg_citation(stats, chart_dir=CHART_DIR):
    ensure_chart_dir(chart_dir)
    path = Path(chart_dir) / "yearly_avg_citation.png"
    yearly = stats.get("yearly_avg_citations", {})

    plt.figure(figsize=(8, 4.5))
    if yearly:
        years = list(yearly.keys())
        values = list(yearly.values())
        plt.plot(years, values, marker="o", color="#be3b62")
        plt.xticks(years, rotation=30)
    else:
        plt.text(0.5, 0.5, "暂无年度引用数据", ha="center", va="center")
    plt.title("年度平均引用次数")
    plt.xlabel("年份")
    plt.ylabel("平均引用")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return path.name


def save_word_cloud(stats, chart_dir=CHART_DIR):
    ensure_chart_dir(chart_dir)
    path = Path(chart_dir) / "keyword_cloud.png"
    frequencies = dict(stats.get("top_keywords", []))

    if WordCloud and frequencies:
        cloud = WordCloud(
            width=900,
            height=450,
            background_color="white",
            font_path=find_chinese_font(),
        ).generate_from_frequencies(frequencies)
        cloud.to_file(path)
    else:
        plt.figure(figsize=(8, 4))
        words = " ".join(frequencies.keys()) if frequencies else "暂无关键词数据"
        plt.text(0.5, 0.5, words, ha="center", va="center", wrap=True)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(path, dpi=150)
        plt.close()
    return path.name


def generate_all_charts(papers, stats, chart_dir=CHART_DIR):
    return [
        {"title": "年度发文趋势", "image": save_year_trend(stats, chart_dir)},
        {"title": "高频关键词", "image": save_keyword_bar(stats, chart_dir)},
        {"title": "引用次数分布", "image": save_citation_chart(papers, chart_dir)},
        {"title": "关键词云", "image": save_word_cloud(stats, chart_dir)},
        {"title": "期刊 / 来源排行", "image": save_journal_bar(stats, chart_dir)},
        {"title": "高产作者排行", "image": save_author_bar(stats, chart_dir)},
        {"title": "数据源占比", "image": save_source_pie(stats, chart_dir)},
        {"title": "年度平均引用", "image": save_yearly_avg_citation(stats, chart_dir)},
    ]
