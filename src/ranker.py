import re
from math import log1p

from config import STOPWORDS
from src.extractor import normalize_space, strip_html


TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-]{1,}|[\u4e00-\u9fff]{2,}")


def tokenize_query(query):
    tokens = []
    seen = set()
    for token in TOKEN_RE.findall(normalize_space(query).lower()):
        token = token.strip("-")
        if len(token) < 2 or token in STOPWORDS or token in seen:
            continue
        tokens.append(token)
        seen.add(token)
    return tokens


def normalize_text(*values):
    return normalize_space(strip_html(" ".join(str(value or "") for value in values))).lower()


def contains_term(text, term):
    if not text or not term:
        return False
    if re.search(r"[\u4e00-\u9fff]", term):
        return term in text
    return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None


def keyword_text(paper):
    return normalize_text(" ".join(paper.get("keywords", [])))


def calculate_relevance(query, paper):
    terms = tokenize_query(query)
    if not terms:
        return 0.0

    title = normalize_text(paper.get("title"))
    abstract = normalize_text(paper.get("abstract"))
    keywords = keyword_text(paper)
    journal = normalize_text(paper.get("journal"))
    authors = normalize_text(" ".join(paper.get("authors", [])))
    searchable = " ".join([title, abstract, keywords, journal, authors])
    phrase = normalize_text(query)

    score = 0.0
    if phrase and len(phrase) >= 3:
        if phrase in title:
            score += 32
        if phrase in keywords:
            score += 22
        if phrase in abstract:
            score += 12

    matched_terms = 0
    title_matches = 0
    for term in terms:
        term_matched = False
        if contains_term(title, term):
            score += 9
            title_matches += 1
            term_matched = True
        if contains_term(keywords, term):
            score += 7
            term_matched = True
        if contains_term(abstract, term):
            score += 3
            term_matched = True
        if contains_term(journal, term):
            score += 1.5
            term_matched = True
        if contains_term(authors, term):
            score += 1
            term_matched = True
        if term_matched:
            matched_terms += 1

    coverage = matched_terms / len(terms)
    title_coverage = title_matches / len(terms)
    score += coverage * 22
    score += title_coverage * 12

    if matched_terms == len(terms):
        score += 12
    if all(contains_term(title, term) or contains_term(keywords, term) for term in terms):
        score += 8
    if not any(contains_term(searchable, term) for term in terms):
        return 0.0

    return round(min(score, 100), 2)


def dedupe_papers(papers):
    deduped = []
    index_by_key = {}
    for paper in papers:
        doi = normalize_text(paper.get("doi"))
        url = normalize_text(paper.get("url"))
        title = normalize_text(paper.get("title"))
        key = doi or url or title
        if not key:
            continue
        if key in index_by_key:
            existing = deduped[index_by_key[key]]
            existing["citation_count"] = max(
                int(existing.get("citation_count") or 0),
                int(paper.get("citation_count") or 0),
            )
            for field in ["doi", "year", "journal", "abstract", "url"]:
                if not existing.get(field) and paper.get(field):
                    existing[field] = paper[field]
            if len(str(paper.get("abstract") or "")) > len(str(existing.get("abstract") or "")):
                existing["abstract"] = paper["abstract"]
            for field in ["authors", "keywords"]:
                combined = list(existing.get(field, []))
                for value in paper.get(field, []):
                    if value not in combined:
                        combined.append(value)
                existing[field] = combined
            if existing.get("source") != paper.get("source") and paper.get("source"):
                sources = []
                for source in str(existing.get("source") or "").split("+"):
                    if source and source not in sources:
                        sources.append(source)
                if paper["source"] not in sources:
                    sources.append(paper["source"])
                existing["source"] = "+".join(sources)
            continue

        deduped.append(dict(paper))
        index_by_key[key] = len(deduped) - 1
    return deduped


def rank_papers(query, papers, limit=None):
    papers = dedupe_papers(papers)
    max_citation = max((int(paper.get("citation_count") or 0) for paper in papers), default=0)
    max_citation_log = log1p(max_citation) or 1
    latest_year = max((int(paper.get("year") or 0) for paper in papers), default=0)

    ranked = []
    for paper in papers:
        relevance = calculate_relevance(query, paper)
        citation = int(paper.get("citation_count") or 0)
        citation_score = log1p(citation) / max_citation_log * 100 if max_citation else 0
        year = int(paper.get("year") or 0)
        recency_score = 0 if not latest_year or not year else max(0, 100 - (latest_year - year) * 8)
        rank_score = relevance * 0.72 + citation_score * 0.23 + recency_score * 0.05

        enriched = dict(paper)
        enriched["relevance_score"] = round(relevance, 2)
        enriched["rank_score"] = round(rank_score, 2)
        ranked.append(enriched)

    positive_relevance_count = sum(1 for paper in ranked if paper.get("relevance_score", 0) > 0)
    if positive_relevance_count > 0:
        for paper in ranked:
            if paper.get("relevance_score", 0) == 0:
                paper["rank_score"] = round(paper.get("rank_score", 0) * 0.35, 2)

    ranked.sort(
        key=lambda paper: (
            paper.get("relevance_score", 0),
            paper.get("rank_score", 0),
            int(paper.get("citation_count") or 0),
            int(paper.get("year") or 0),
        ),
        reverse=True,
    )
    return ranked[:limit] if limit else ranked
