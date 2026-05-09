from collections import Counter, defaultdict
from statistics import median, pstdev


SOURCE_LABELS = {
    "crossref": "CrossRef",
    "arxiv": "arXiv",
    "openalex": "OpenAlex",
    "demo": "演示数据",
    "cache": "本地缓存",
}


def analyze_papers(papers):
    year_counts = Counter()
    yearly_citations = defaultdict(list)
    journal_counts = Counter()
    author_counts = Counter()
    keyword_counts = Counter()
    source_counts = Counter()
    citation_values = []
    author_totals = []
    doi_count = 0

    for paper in papers:
        if paper.get("year"):
            year = int(paper["year"])
            year_counts[year] += 1
            yearly_citations[year].append(int(paper.get("citation_count") or 0))
        if paper.get("journal"):
            journal_counts[paper["journal"]] += 1
        if paper.get("source"):
            source_counts[SOURCE_LABELS.get(paper["source"], paper["source"])] += 1
        for author in paper.get("authors", []):
            author_counts[author] += 1
        for keyword in paper.get("keywords", []):
            keyword_counts[keyword] += 1
        citation_values.append(int(paper.get("citation_count") or 0))
        author_totals.append(len(paper.get("authors", [])))
        if paper.get("doi"):
            doi_count += 1

    avg_citation = round(sum(citation_values) / len(citation_values), 2) if citation_values else 0
    max_citation = max(citation_values) if citation_values else 0
    median_citation = round(median(citation_values), 2) if citation_values else 0
    citation_std = round(pstdev(citation_values), 2) if len(citation_values) > 1 else 0
    total_citation = sum(citation_values)
    cited_count = sum(1 for value in citation_values if value > 0)
    cited_rate = round(cited_count / len(citation_values) * 100, 1) if citation_values else 0
    doi_coverage_rate = round(doi_count / len(papers) * 100, 1) if papers else 0
    avg_authors_per_paper = round(sum(author_totals) / len(author_totals), 2) if author_totals else 0

    sorted_year_counts = dict(sorted(year_counts.items()))
    years = list(sorted_year_counts.keys())
    earliest_year = min(years) if years else None
    latest_year = max(years) if years else None
    active_years = len(years)
    peak_year = None
    peak_year_count = 0
    if year_counts:
        peak_year, peak_year_count = max(year_counts.items(), key=lambda item: item[1])

    growth_rate = None
    if len(years) >= 2:
        previous_count = sorted_year_counts[years[-2]]
        latest_count = sorted_year_counts[years[-1]]
        if previous_count:
            growth_rate = round((latest_count - previous_count) / previous_count * 100, 1)

    recent_count = 0
    if latest_year:
        recent_count = sum(
            count for year, count in year_counts.items() if year >= latest_year - 4
        )

    top_cited = sorted(
        papers,
        key=lambda paper: int(paper.get("citation_count") or 0),
        reverse=True,
    )[:10]

    yearly_avg_citations = {
        year: round(sum(values) / len(values), 2)
        for year, values in sorted(yearly_citations.items())
        if values
    }

    return {
        "total": len(papers),
        "year_counts": sorted_year_counts,
        "yearly_avg_citations": yearly_avg_citations,
        "top_journals": journal_counts.most_common(10),
        "top_authors": author_counts.most_common(10),
        "top_keywords": keyword_counts.most_common(15),
        "source_counts": source_counts.most_common(),
        "top_cited": top_cited,
        "avg_citation": avg_citation,
        "max_citation": max_citation,
        "median_citation": median_citation,
        "citation_std": citation_std,
        "total_citation": total_citation,
        "cited_rate": cited_rate,
        "doi_coverage_rate": doi_coverage_rate,
        "unique_authors": len(author_counts),
        "unique_journals": len(journal_counts),
        "avg_authors_per_paper": avg_authors_per_paper,
        "earliest_year": earliest_year,
        "latest_year": latest_year,
        "active_years": active_years,
        "peak_year": peak_year,
        "peak_year_count": peak_year_count,
        "growth_rate": growth_rate,
        "recent_count": recent_count,
    }


def generate_summary(stats):
    total = stats.get("total", 0)
    if total == 0:
        return "当前还没有论文数据，请先在首页进行检索或导入演示数据。"

    years = list(stats.get("year_counts", {}).keys())
    top_keywords = [word for word, _ in stats.get("top_keywords", [])[:5]]

    if years:
        trend_text = f"当前数据集覆盖 {min(years)} 年至 {max(years)} 年的论文"
    else:
        trend_text = "当前数据集缺少足够的年份信息"

    keyword_text = "、".join(top_keywords) if top_keywords else "暂未形成明显关键词聚类"
    return (
        f"{trend_text}。当前分析数据集共包含 {total} 篇论文，"
        f"覆盖 {stats.get('unique_authors', 0)} 位作者和 {stats.get('unique_journals', 0)} 个来源期刊。"
        f"高频研究主题包括 {keyword_text}，平均引用次数为 {stats.get('avg_citation', 0)}。"
    )


def generate_insights(stats):
    if stats.get("total", 0) == 0:
        return ["当前暂无可分析数据，请先完成论文检索。"]

    insights = []
    if stats.get("peak_year"):
        insights.append(
            f"发文峰值出现在 {stats['peak_year']} 年，共收录 {stats['peak_year_count']} 篇论文。"
        )

    if stats.get("growth_rate") is not None:
        trend_word = "增长" if stats["growth_rate"] >= 0 else "下降"
        insights.append(
            f"最近两个有记录年份之间，论文数量{trend_word} {abs(stats['growth_rate'])}%。"
        )

    if stats.get("top_keywords"):
        word, count = stats["top_keywords"][0]
        insights.append(f"最核心关键词为“{word}”，在当前数据集中出现 {count} 次。")

    if stats.get("top_authors"):
        author, count = stats["top_authors"][0]
        insights.append(f"最高产作者为“{author}”，相关论文数量为 {count} 篇。")

    if stats.get("top_journals"):
        journal, count = stats["top_journals"][0]
        insights.append(f"收录最多的来源为“{journal}”，共有 {count} 篇论文。")

    insights.append(
        f"DOI 覆盖率为 {stats.get('doi_coverage_rate', 0)}%，有引文记录的论文占 {stats.get('cited_rate', 0)}%。"
    )
    return insights[:6]


def citation_distribution(papers):
    buckets = defaultdict(int)
    for paper in papers:
        value = int(paper.get("citation_count") or 0)
        if value == 0:
            buckets["0"] += 1
        elif value <= 10:
            buckets["1-10"] += 1
        elif value <= 50:
            buckets["11-50"] += 1
        elif value <= 100:
            buckets["51-100"] += 1
        else:
            buckets[">100"] += 1
    order = ["0", "1-10", "11-50", "51-100", ">100"]
    return {key: buckets[key] for key in order}
