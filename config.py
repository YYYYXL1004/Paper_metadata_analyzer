from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXPORT_DIR = BASE_DIR / "exports"
CHART_DIR = BASE_DIR / "static" / "charts"

DB_PATH = DATA_DIR / "papers.db"

CROSSREF_API = "https://api.crossref.org/works"
ARXIV_API = "https://export.arxiv.org/api/query"
OPENALEX_API = "https://api.openalex.org/works"

DEFAULT_LIMIT = 20
APP_TITLE = "学术论文元数据分析工具"

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "using",
    "with",
    "based",
    "study",
    "analysis",
    "research",
    "paper",
    "approach",
    "method",
    "methods",
    "model",
    "models",
}
