import os
from statistics import median

from flask import Flask, redirect, render_template, request, send_from_directory, url_for

from config import (
    APP_TITLE,
    DEFAULT_LIMIT,
    EXPORT_DIR,
    MAX_LIMIT_PER_PAGE,
    MAX_TOTAL_RESULTS,
    SORT_OPTIONS,
)
from src.analyzer import analyze_papers, generate_insights, generate_summary
from src.api_client import (
    CROSSREF_SORT_MAP,
    OPENALEX_SORT_MAP,
    demo_papers,
    fetch_arxiv,
    fetch_crossref,
    fetch_openalex_paged,
)
from src.database import (
    cached_query,
    get_paper,
    get_papers_by_ids,
    init_db,
    save_papers,
)
from src.exporter import export_papers_to_csv
from src.network import build_author_network
from src.parser import parse_arxiv_response, parse_crossref_response, parse_openalex_response
from src.ranker import rank_papers
from src.recommender import recommend_by_paper
from src.visualizer import generate_all_charts


app = Flask(__name__)


API_SOURCES = {"crossref", "arxiv", "openalex"}

SOURCE_LABELS = {
    "cache": "本地真实缓存",
    "crossref": "CrossRef 实时 API",
    "arxiv": "arXiv 实时 API",
    "openalex": "OpenAlex 高引用 API",
    "demo": "演示数据",
}

SORT_LABELS = {
    "relevance": "按相关度",
    "citations": "按引用最高",
    "recent": "按最新",
}


def normalize_source(source):
    return source if source in API_SOURCES else "openalex"


def normalize_limit(value):
    try:
        limit = int(value or DEFAULT_LIMIT)
    except (TypeError, ValueError):
        return DEFAULT_LIMIT
    return max(1, min(MAX_TOTAL_RESULTS, limit))


def candidate_limit(limit):
    if limit >= 100:
        return min(MAX_TOTAL_RESULTS, limit)
    return min(MAX_TOTAL_RESULTS, max(limit * 3, 60))


def normalize_year(value):
    try:
        year = int(value)
    except (TypeError, ValueError):
        return None
    if year < 1900 or year > 2100:
        return None
    return year


def normalize_min_citations(value):
    try:
        n = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, n)


def normalize_sort(value):
    return value if value in SORT_OPTIONS else "relevance"


def normalize_concept(value):
    if not value:
        return ""
    return str(value).strip()[:100]


def collect_filters(getter):
    """getter is request.form.get or request.args.get"""
    return {
        "year_from": normalize_year(getter("year_from")),
        "year_to": normalize_year(getter("year_to")),
        "min_citations": normalize_min_citations(getter("min_citations")),
        "sort": normalize_sort(getter("sort")),
        "concept": normalize_concept(getter("concept")),
    }


def filters_for_url(filters):
    """Strip empty fields for cleaner URLs."""
    out = {}
    if filters.get("year_from"):
        out["year_from"] = filters["year_from"]
    if filters.get("year_to"):
        out["year_to"] = filters["year_to"]
    if filters.get("min_citations"):
        out["min_citations"] = filters["min_citations"]
    if filters.get("sort") and filters["sort"] != "relevance":
        out["sort"] = filters["sort"]
    if filters.get("concept"):
        out["concept"] = filters["concept"]
    return out


def apply_min_citations_filter(papers, min_citations):
    if not min_citations:
        return papers
    threshold = int(min_citations)
    return [p for p in papers if int(p.get("citation_count") or 0) >= threshold]


def paper_ids_for_url(papers):
    ids = []
    seen = set()
    for paper in papers:
        try:
            paper_id = int(paper.get("id"))
        except (TypeError, ValueError):
            continue
        if paper_id not in seen:
            ids.append(paper_id)
            seen.add(paper_id)
    return ",".join(str(paper_id) for paper_id in ids)


def parse_paper_ids(raw_ids):
    ids = []
    seen = set()
    for value in (raw_ids or "").split(","):
        value = value.strip()
        if not value:
            continue
        try:
            paper_id = int(value)
        except ValueError:
            continue
        if paper_id > 0 and paper_id not in seen:
            ids.append(paper_id)
            seen.add(paper_id)
    return ids


def fetch_real_papers(query, source, limit, filters=None):
    source = normalize_source(source)
    filters = filters or {}
    rows = candidate_limit(limit)
    year_from = filters.get("year_from")
    year_to = filters.get("year_to")
    min_citations = filters.get("min_citations", 0)
    concept = filters.get("concept")
    sort_key = filters.get("sort", "relevance")

    if source == "arxiv":
        raw = fetch_arxiv(query, rows=rows, year_from=year_from, year_to=year_to)
        papers = parse_arxiv_response(raw)
        papers = apply_min_citations_filter(papers, min_citations)
        return rank_papers(query, papers, limit=limit)

    if source == "openalex":
        openalex_sort = OPENALEX_SORT_MAP.get(sort_key)
        papers = []
        raw = fetch_openalex_paged(
            query,
            total_rows=rows,
            sort=openalex_sort,
            year_from=year_from,
            year_to=year_to,
            min_citations=min_citations,
            concept=concept,
        )
        papers.extend(parse_openalex_response(raw))
        if sort_key != "citations":
            try:
                cited_raw = fetch_openalex_paged(
                    query,
                    total_rows=min(rows, MAX_LIMIT_PER_PAGE * 2),
                    sort="cited_by_count:desc",
                    year_from=year_from,
                    year_to=year_to,
                    min_citations=min_citations,
                    concept=concept,
                )
                papers.extend(parse_openalex_response(cited_raw))
            except Exception:
                pass
        return rank_papers(query, papers, limit=limit)

    # crossref
    crossref_sort, crossref_order = CROSSREF_SORT_MAP.get(sort_key, ("relevance", "desc"))
    raw = fetch_crossref(
        query,
        rows=min(rows, MAX_LIMIT_PER_PAGE),
        sort=crossref_sort,
        order=crossref_order,
        year_from=year_from,
        year_to=year_to,
    )
    papers = parse_crossref_response(raw)
    if sort_key != "citations":
        try:
            cited_raw = fetch_crossref(
                query,
                rows=min(rows, MAX_LIMIT_PER_PAGE),
                sort="is-referenced-by-count",
                order="desc",
                year_from=year_from,
                year_to=year_to,
            )
            papers.extend(parse_crossref_response(cited_raw))
        except Exception:
            pass
    try:
        openalex_raw = fetch_openalex_paged(
            query,
            total_rows=min(rows, MAX_LIMIT_PER_PAGE),
            year_from=year_from,
            year_to=year_to,
            min_citations=min_citations,
            concept=concept,
        )
        papers.extend(parse_openalex_response(openalex_raw))
    except Exception:
        pass
    papers = apply_min_citations_filter(papers, min_citations)
    return rank_papers(query, papers, limit=limit)


def load_or_fetch(query, source, limit, use_cache=False, filters=None):
    source = normalize_source(source)
    if use_cache:
        cached = cached_query(query, include_demo=False)
        if cached:
            cached = apply_min_citations_filter(cached, (filters or {}).get("min_citations", 0))
            cached = rank_papers(query, cached, limit=limit)
            return cached, "cache", "已从本地 SQLite 读取历史真实 API 数据，并按关键词相关性重新排序。"

    papers = fetch_real_papers(query, source, limit, filters=filters)
    if not papers:
        cached = cached_query(query, include_demo=False)
        if cached:
            cached = apply_min_citations_filter(cached, (filters or {}).get("min_citations", 0))
            cached = rank_papers(query, cached, limit=limit)
            return cached, "cache", "API 未返回新结果，已改用本地真实缓存并按关键词相关性排序。"
        return [], source, "API 请求成功，但没有检索到匹配论文。"

    paper_ids = save_papers(papers, query)
    saved = get_papers_by_ids(paper_ids)
    saved = apply_min_citations_filter(saved, (filters or {}).get("min_citations", 0))
    saved = rank_papers(query, saved, limit=limit)
    source_name = SOURCE_LABELS.get(source, source)
    if source == "crossref":
        source_name = "CrossRef 实时 API 和 OpenAlex 引用补充"
    return saved, source, f"已通过 {source_name} 获取 {len(saved)} 条真实论文数据，并按关键词相关性、引用次数和年份排序。"


def load_papers_safely(query, source, limit, use_cache=False, filters=None):
    error = None
    try:
        return (*load_or_fetch(query, source, limit, use_cache=use_cache, filters=filters), error)
    except Exception as exc:
        source = normalize_source(source)
        if source in {"arxiv", "openalex"}:
            try:
                papers, data_source, status_message = load_or_fetch(
                    query, "crossref", limit, use_cache=False, filters=filters
                )
                source_name = "arXiv" if source == "arxiv" else "OpenAlex"
                error = f"{source_name} 请求失败，已自动改用 CrossRef 获取真实 API 数据。{source_name} 错误：{exc}"
                status_message = f"{status_message} 由于 {source_name} 连接不稳定，本次结果来自 CrossRef。"
            except Exception as backup_exc:
                papers = []
                data_source = source
                source_name = "arXiv" if source == "arxiv" else "OpenAlex"
                status_message = f"{source_name} 和 CrossRef 均暂时不可用。"
                error = f"{source_name} 错误：{exc}；CrossRef 错误：{backup_exc}"
        else:
            papers = []
            data_source = source
            status_message = "远程 API 暂时不可用。"
            error = f"远程 API 请求失败：{exc}"

        cached = cached_query(query, include_demo=False)
        if not papers and cached:
            cached = apply_min_citations_filter(cached, (filters or {}).get("min_citations", 0))
            papers = rank_papers(query, cached, limit=limit)
            data_source = "cache"
            status_message = "远程 API 暂时不可用，已改用本地真实 API 缓存。"
        elif not papers and not cached:
            data_source = source
            status_message = "未加载演示数据。本次检索没有获得真实 API 数据，请稍后重试或改用 CrossRef。"

        return papers, data_source, status_message, error


def compute_cohort_position(target, cohort):
    """Build summary stats: citation rank, same-year peers, citation comparison."""
    if not target or not cohort:
        return None
    target_id = target.get("id")
    others = [p for p in cohort if p.get("id") != target_id]
    citations_list = sorted(
        [int(p.get("citation_count") or 0) for p in cohort],
        reverse=True,
    )
    target_cit = int(target.get("citation_count") or 0)
    rank = 1
    for c in citations_list:
        if c > target_cit:
            rank += 1
    same_year = [p for p in others if p.get("year") and p.get("year") == target.get("year")]
    other_citations = [int(p.get("citation_count") or 0) for p in others] or [0]
    return {
        "citation_rank": rank,
        "cohort_size": len(cohort),
        "same_year_count": len(same_year),
        "citation_target": target_cit,
        "citation_median": int(median(other_citations)) if other_citations else 0,
        "citation_max": max(other_citations) if other_citations else 0,
    }


@app.context_processor
def inject_globals():
    return {"app_title": APP_TITLE}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        source = normalize_source(request.form.get("source", "openalex"))
        limit = normalize_limit(request.form.get("limit"))
        use_cache = request.form.get("use_cache") == "on"
        filters = collect_filters(request.form.get)
        if not query:
            return render_template("index.html", error="请输入检索关键词。")
        return redirect(
            url_for(
                "search",
                query=query,
                source=source,
                limit=limit,
                use_cache="1" if use_cache else "0",
                **filters_for_url(filters),
            )
        )
    return render_template("index.html")


@app.route("/search")
def search():
    query = request.args.get("query", "").strip()
    source = normalize_source(request.args.get("source", "openalex"))
    limit = normalize_limit(request.args.get("limit"))
    use_cache = request.args.get("use_cache", "0") == "1"
    filters = collect_filters(request.args.get)

    if not query:
        return redirect(url_for("index"))

    papers, data_source, status_message, error = load_papers_safely(
        query, source, limit, use_cache=use_cache, filters=filters
    )
    paper_ids = paper_ids_for_url(papers)
    url_filters = filters_for_url(filters)

    return render_template(
        "results.html",
        query=query,
        papers=papers,
        paper_ids=paper_ids,
        source=data_source,
        source_label=SOURCE_LABELS.get(data_source, data_source),
        status_message=status_message,
        error=error,
        filters=filters,
        sort_label=SORT_LABELS.get(filters.get("sort", "relevance"), ""),
        analysis_url=url_for(
            "analysis",
            ids=paper_ids,
            query=query,
            source=source,
            limit=limit,
            **url_filters,
        ),
        export_url=url_for("export", ids=paper_ids, query=query),
        paper_detail_query=query,
    )


@app.route("/analysis")
def analysis():
    query = request.args.get("query", "").strip()
    source = normalize_source(request.args.get("source", "openalex"))
    limit = normalize_limit(request.args.get("limit"))
    filters = collect_filters(request.args.get)
    paper_ids = parse_paper_ids(request.args.get("ids", ""))
    status_message = None
    error = None

    if paper_ids:
        papers = get_papers_by_ids(paper_ids)
        ids_param = paper_ids_for_url(papers)
        status_message = "正在分析本次关键词检索返回的论文数据。"
    elif query:
        papers, data_source, status_message, error = load_papers_safely(
            query, source, limit, use_cache=False, filters=filters
        )
        ids_param = paper_ids_for_url(papers)
    else:
        papers = []
        ids_param = ""
        status_message = "请先在首页输入关键词并调用学术 API，再查看分析结果。"

    stats = analyze_papers(papers)
    charts = generate_all_charts(papers, stats)
    network = build_author_network(papers)
    summary = generate_summary(stats)
    insights = generate_insights(stats)
    if query:
        analysis_title = f"“{query}”本次检索共 {stats['total']} 篇论文"
    else:
        analysis_title = f"当前分析数据集共 {stats['total']} 篇论文"

    return render_template(
        "analysis.html",
        query=query,
        papers=papers,
        paper_ids=ids_param,
        stats=stats,
        charts=charts,
        network=network,
        summary=summary,
        insights=insights,
        analysis_title=analysis_title,
        status_message=status_message,
        error=error,
        export_url=url_for("export", ids=ids_param, query=query)
        if ids_param or query
        else url_for("index"),
    )


@app.route("/paper/<int:paper_id>")
def paper_detail(paper_id):
    target = get_paper(paper_id)
    if not target:
        return redirect(url_for("index"))
    query = request.args.get("query", "").strip()
    paper_ids = parse_paper_ids(request.args.get("ids", ""))
    if paper_ids:
        cohort = get_papers_by_ids(paper_ids)
    elif query:
        cohort = rank_papers(query, cached_query(query, include_demo=False))
    else:
        cohort = [target]
    recommendations = recommend_by_paper(target, cohort)
    cohort_stats = compute_cohort_position(target, cohort)
    ids_param = paper_ids_for_url(cohort) if paper_ids else ""
    return render_template(
        "paper_detail.html",
        paper=target,
        cohort=cohort,
        cohort_stats=cohort_stats,
        recommendations=recommendations,
        query=query,
        paper_ids=ids_param,
        back_url=url_for("search", query=query) if query else url_for("index"),
    )


@app.route("/recommend/<int:paper_id>")
def recommend(paper_id):
    target = get_paper(paper_id)
    query = request.args.get("query", "").strip()
    paper_ids = parse_paper_ids(request.args.get("ids", ""))
    if paper_ids:
        papers = get_papers_by_ids(paper_ids)
    elif query:
        papers = rank_papers(query, cached_query(query, include_demo=False))
    else:
        papers = [target] if target else []
    ids_param = paper_ids_for_url(papers)
    recommendations = recommend_by_paper(target, papers)
    return render_template(
        "recommend.html",
        target=target,
        recommendations=recommendations,
        back_url=url_for("analysis", ids=ids_param, query=query)
        if ids_param or query
        else url_for("index"),
    )


@app.route("/export")
def export():
    paper_ids = parse_paper_ids(request.args.get("ids", ""))
    query = request.args.get("query", "").strip()
    if paper_ids:
        papers = get_papers_by_ids(paper_ids)
    elif query:
        papers = rank_papers(query, cached_query(query, include_demo=False))
    else:
        return redirect(url_for("index"))
    path = export_papers_to_csv(papers)
    return send_from_directory(EXPORT_DIR, path.name, as_attachment=True)


@app.route("/seed")
def seed():
    paper_ids = save_papers(demo_papers(), "demo")
    return redirect(url_for("analysis", query="demo", ids=",".join(map(str, paper_ids))))


if __name__ == "__main__":
    init_db()
    app.run(debug=False, port=int(os.environ.get("PORT", 5000)))
