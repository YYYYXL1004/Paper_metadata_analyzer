from math import log1p


def jaccard(left, right):
    left_set = set(left or [])
    right_set = set(right or [])
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def normalize(value, max_value):
    if not max_value:
        return 0.0
    return value / max_value


def recommend_by_paper(target, papers, limit=5):
    if not target:
        return []

    max_citation = max((int(paper.get("citation_count") or 0) for paper in papers), default=0)
    current_year = max((int(paper.get("year") or 0) for paper in papers), default=0)

    recommendations = []
    for paper in papers:
        if paper["id"] == target["id"]:
            continue

        keyword_score = jaccard(target.get("keywords", []), paper.get("keywords", []))
        citation_score = normalize(log1p(int(paper.get("citation_count") or 0)), log1p(max_citation))
        year = int(paper.get("year") or 0)
        freshness_score = 0 if not current_year or not year else max(0, 1 - (current_year - year) / 10)

        score = keyword_score * 0.6 + citation_score * 0.3 + freshness_score * 0.1
        if score > 0:
            recommendations.append(
                {
                    "paper": paper,
                    "score": round(score, 3),
                    "keyword_score": round(keyword_score, 3),
                    "citation_score": round(citation_score, 3),
                    "freshness_score": round(freshness_score, 3),
                }
            )

    return sorted(recommendations, key=lambda item: item["score"], reverse=True)[:limit]
