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


def save_author_network(network, chart_dir=CHART_DIR):
    """Generate author collaboration network visualization"""
    ensure_chart_dir(chart_dir)
    path = Path(chart_dir) / "author_network.png"

    edges = network.get("edges", [])[:30]  # Top 30 edges
    centrality = network.get("centrality", [])[:15]  # Top 15 authors

    if not edges:
        plt.figure(figsize=(8, 4.5))
        plt.text(0.5, 0.5, "暂无合作网络数据", ha="center", va="center")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(path, dpi=150)
        plt.close()
        return path.name

    # Build graph
    import networkx as nx

    G = nx.Graph()

    # Add edges with weights
    for author1, author2, weight in edges:
        G.add_edge(author1, author2, weight=weight)

    # Calculate layout
    pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)

    # Draw
    plt.figure(figsize=(10, 7))

    # Draw edges with varying thickness
    weights = [G[u][v]["weight"] for u, v in G.edges()]
    max_weight = max(weights) if weights else 1
    edge_widths = [2 + 8 * (w / max_weight) for w in weights]

    nx.draw_networkx_edges(
        G, pos, width=edge_widths, alpha=0.3, edge_color="#64748b"
    )

    # Draw nodes with size based on centrality
    node_sizes = []
    centrality_dict = {author: score for author, score in centrality}
    max_centrality = max(centrality_dict.values()) if centrality_dict else 1

    for node in G.nodes():
        score = centrality_dict.get(node, 0)
        size = 300 + 2000 * (score / max_centrality) if max_centrality else 300
        node_sizes.append(size)

    nx.draw_networkx_nodes(
        G, pos, node_size=node_sizes, node_color="#2563eb", alpha=0.7
    )

    # Draw labels
    nx.draw_networkx_labels(
        G, pos, font_size=8, font_family="Microsoft YaHei", font_weight="bold"
    )

    plt.title("作者合作网络（节点大小表示合作次数）")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
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


def generate_all_charts_with_network(papers, stats, network, chart_dir=CHART_DIR):
    """Generate all charts including author network visualization"""
    charts = generate_all_charts(papers, stats, chart_dir)
    charts.append({"title": "作者合作网络", "image": save_author_network(network, chart_dir)})
    return charts


def save_paper_citation_trend(paper, cohort, chart_dir=CHART_DIR):
    """Generate citation trend comparison for a single paper"""
    ensure_chart_dir(chart_dir)
    paper_id = paper.get("id", "paper")
    path = Path(chart_dir) / f"citation_trend_{paper_id}.png"

    paper_year = int(paper.get("year") or 0)
    paper_citations = int(paper.get("citation_count") or 0)

    # Get same-year papers from cohort
    same_year_papers = [p for p in cohort if int(p.get("year") or 0) == paper_year]

    plt.figure(figsize=(8, 4.5))

    if same_year_papers and len(same_year_papers) > 1:
        # Calculate statistics for same-year papers
        citations = [int(p.get("citation_count") or 0) for p in same_year_papers]
        avg_citations = sum(citations) / len(citations)
        max_citations = max(citations)
        min_citations = min(citations)

        # Create bar chart
        categories = ["本文", "同年平均", "同年最高", "同年最低"]
        values = [paper_citations, avg_citations, max_citations, min_citations]
        colors = ["#2563eb", "#0f8f68", "#f59e0b", "#64748b"]

        bars = plt.bar(categories, values, color=colors, alpha=0.8)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{int(height)}",
                ha="center",
                va="bottom",
                fontsize=10,
            )

        plt.title(f"{paper_year} 年论文引用对比（{len(same_year_papers)} 篇）")
        plt.ylabel("引用次数")
    else:
        # Just show the paper's citations
        plt.bar(["本文"], [paper_citations], color="#2563eb")
        plt.text(0, paper_citations, f"{paper_citations}", ha="center", va="bottom")
        plt.title(f"{paper_year} 年论文引用次数")
        plt.ylabel("引用次数")

    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

    return path.name
