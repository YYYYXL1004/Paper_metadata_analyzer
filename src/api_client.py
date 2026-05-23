import time

import requests

from config import (
    ARXIV_API,
    CROSSREF_API,
    DEFAULT_LIMIT,
    MAX_LIMIT_PER_PAGE,
    OPENALEX_API,
)


HEADERS = {
    "User-Agent": "PaperMetadataAnalyzer/1.0 (mailto:student@example.com)"
}


OPENALEX_SORT_MAP = {
    "relevance": None,
    "citations": "cited_by_count:desc",
    "recent": "publication_date:desc",
}

CROSSREF_SORT_MAP = {
    "relevance": ("relevance", "desc"),
    "citations": ("is-referenced-by-count", "desc"),
    "recent": ("published", "desc"),
}


def get_with_retry(url, params=None, timeout=(6, 30), attempts=3):
    last_error = None
    for attempt in range(attempts):
        try:
            response = requests.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=timeout,
            )
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(1 + attempt)
    raise last_error


def build_openalex_filter(year_from=None, year_to=None, min_citations=0, concept=None):
    clauses = []
    if year_from:
        clauses.append(f"from_publication_date:{int(year_from)}-01-01")
    if year_to:
        clauses.append(f"to_publication_date:{int(year_to)}-12-31")
    if min_citations and int(min_citations) > 0:
        # OpenAlex supports `>` but not `>=`; subtract 1 to make it inclusive.
        clauses.append(f"cited_by_count:>{int(min_citations) - 1}")
    if concept:
        concept_clean = str(concept).strip().replace(",", " ")
        if concept_clean:
            clauses.append(f"concepts.display_name.search:{concept_clean}")
    return ",".join(clauses) if clauses else None


def fetch_crossref(query, rows=DEFAULT_LIMIT, sort=None, order="desc", year_from=None, year_to=None):
    params = {
        "query": query,
        "rows": rows,
        "select": "DOI,title,author,published-print,published-online,issued,container-title,is-referenced-by-count,abstract,URL,subject",
    }
    if sort:
        params["sort"] = sort
        params["order"] = order
    filter_clauses = []
    if year_from:
        filter_clauses.append(f"from-pub-date:{int(year_from)}-01-01")
    if year_to:
        filter_clauses.append(f"until-pub-date:{int(year_to)}-12-31")
    if filter_clauses:
        params["filter"] = ",".join(filter_clauses)
    response = get_with_retry(CROSSREF_API, params=params, timeout=(6, 30), attempts=3)
    return response.json()


def fetch_arxiv(query, rows=DEFAULT_LIMIT, year_from=None, year_to=None):
    search_query = f"all:{query}"
    if year_from or year_to:
        start = f"{int(year_from)}01010000" if year_from else "190001010000"
        end = f"{int(year_to)}12312359" if year_to else "203012312359"
        search_query = f"{search_query} AND submittedDate:[{start} TO {end}]"
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": rows,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    response = get_with_retry(ARXIV_API, params=params, timeout=(8, 45), attempts=2)
    return response.text


def fetch_openalex(
    query,
    rows=DEFAULT_LIMIT,
    sort=None,
    year_from=None,
    year_to=None,
    min_citations=0,
    concept=None,
    cursor=None,
):
    per_page = min(int(rows), MAX_LIMIT_PER_PAGE)
    params = {
        "search": query,
        "per-page": per_page,
        "mailto": "student@example.com",
        "select": "id,doi,display_name,publication_year,primary_location,authorships,cited_by_count,abstract_inverted_index,concepts",
    }
    if sort:
        params["sort"] = sort
    filter_expr = build_openalex_filter(year_from, year_to, min_citations, concept)
    if filter_expr:
        params["filter"] = filter_expr
    if cursor:
        params["cursor"] = cursor
    response = get_with_retry(OPENALEX_API, params=params, timeout=(6, 30), attempts=3)
    return response.json()


def fetch_openalex_paged(
    query,
    total_rows,
    sort=None,
    year_from=None,
    year_to=None,
    min_citations=0,
    concept=None,
):
    """Fetch up to total_rows OpenAlex works via cursor pagination."""
    collected = []
    cursor = "*"
    remaining = int(total_rows)
    while remaining > 0 and cursor:
        page_size = min(remaining, MAX_LIMIT_PER_PAGE)
        data = fetch_openalex(
            query,
            rows=page_size,
            sort=sort,
            year_from=year_from,
            year_to=year_to,
            min_citations=min_citations,
            concept=concept,
            cursor=cursor,
        )
        results = data.get("results", []) or []
        if not results:
            break
        collected.extend(results)
        remaining -= len(results)
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not cursor:
            break
    return {"results": collected}


def demo_papers():
    return [
        {
            "title": "面向教育数据挖掘的深度学习方法研究",
            "doi": "10.1000/demo.education.001",
            "year": 2021,
            "journal": "学习分析演示期刊",
            "abstract": "本文使用深度学习方法分析学生成绩、学习行为和教学反馈数据。",
            "citation_count": 42,
            "source": "demo",
            "url": "https://example.com/demo1",
            "authors": ["陈晓", "李博"],
            "keywords": ["深度学习", "教育", "数据挖掘", "学习分析", "学生表现"],
        },
        {
            "title": "基于知识图谱的学术论文推荐方法",
            "doi": "10.1000/demo.recommendation.002",
            "year": 2022,
            "journal": "信息系统演示期刊",
            "abstract": "本文提出一种结合关键词重合度和引用网络的论文推荐方法。",
            "citation_count": 31,
            "source": "demo",
            "url": "https://example.com/demo2",
            "authors": ["李博", "王可"],
            "keywords": ["知识图谱", "论文推荐", "关键词", "引用网络", "相似度"],
        },
        {
            "title": "人工智能教育领域的研究趋势分析",
            "doi": "10.1000/demo.trends.003",
            "year": 2023,
            "journal": "人工智能综述演示期刊",
            "abstract": "本文分析人工智能教育方向的研究趋势、作者合作关系和高频主题。",
            "citation_count": 55,
            "source": "demo",
            "url": "https://example.com/demo3",
            "authors": ["陈晓", "张迪"],
            "keywords": ["人工智能", "教育", "研究趋势", "作者合作", "主题分析"],
        },
    ]
