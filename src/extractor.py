import re
from collections import Counter

from config import STOPWORDS


DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z\-]{2,}")


def strip_html(text):
    if not text:
        return ""
    return re.sub(r"<[^>]+>", " ", str(text))


def normalize_space(text):
    return re.sub(r"\s+", " ", text or "").strip()


def extract_doi(*values):
    for value in values:
        if not value:
            continue
        match = DOI_RE.search(str(value))
        if match:
            return match.group(0).lower()
    return ""


def extract_year(*values):
    for value in values:
        if value is None:
            continue
        if isinstance(value, int) and 1900 <= value <= 2100:
            return value
        match = YEAR_RE.search(str(value))
        if match:
            return int(match.group(0))
    return None


def extract_keywords(title="", abstract="", top_n=8):
    text = normalize_space(strip_html(f"{title} {abstract}")).lower()
    words = []
    for word in WORD_RE.findall(text):
        word = word.strip("-").lower()
        if len(word) < 3 or word in STOPWORDS:
            continue
        words.append(word)
    return [word for word, _ in Counter(words).most_common(top_n)]


def keyword_counter(papers):
    counter = Counter()
    for paper in papers:
        counter.update(paper.get("keywords", []))
    return counter
