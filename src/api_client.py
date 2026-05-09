import time

import requests

from config import ARXIV_API, CROSSREF_API, DEFAULT_LIMIT, OPENALEX_API


HEADERS = {
    "User-Agent": "PaperMetadataAnalyzer/1.0 (mailto:student@example.com)"
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


def fetch_crossref(query, rows=DEFAULT_LIMIT, sort=None, order="desc"):
    params = {
        "query": query,
        "rows": rows,
        "select": "DOI,title,author,published-print,published-online,issued,container-title,is-referenced-by-count,abstract,URL,subject",
    }
    if sort:
        params["sort"] = sort
        params["order"] = order
    response = get_with_retry(CROSSREF_API, params=params, timeout=(6, 30), attempts=3)
    return response.json()


def fetch_arxiv(query, rows=DEFAULT_LIMIT):
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": rows,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    response = get_with_retry(ARXIV_API, params=params, timeout=(8, 45), attempts=2)
    return response.text


def fetch_openalex(query, rows=DEFAULT_LIMIT, sort=None):
    params = {
        "search": query,
        "per-page": rows,
        "mailto": "student@example.com",
        "select": "id,doi,display_name,publication_year,primary_location,authorships,cited_by_count,abstract_inverted_index,concepts",
    }
    if sort:
        params["sort"] = sort
    response = get_with_retry(OPENALEX_API, params=params, timeout=(6, 30), attempts=3)
    return response.json()


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
