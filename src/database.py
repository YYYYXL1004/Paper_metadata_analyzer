import sqlite3
from pathlib import Path

from config import DB_PATH


def ensure_column(conn, table, column, definition):
    columns = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def get_connection(db_path=DB_PATH):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DB_PATH):
    with get_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                doi TEXT UNIQUE,
                year INTEGER,
                journal TEXT,
                abstract TEXT,
                citation_count INTEGER DEFAULT 0,
                relevance_score REAL DEFAULT 0,
                rank_score REAL DEFAULT 0,
                source TEXT,
                url TEXT,
                query TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS paper_authors (
                paper_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                author_order INTEGER,
                PRIMARY KEY (paper_id, author_id),
                FOREIGN KEY (paper_id) REFERENCES papers(id),
                FOREIGN KEY (author_id) REFERENCES authors(id)
            );

            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS paper_keywords (
                paper_id INTEGER NOT NULL,
                keyword_id INTEGER NOT NULL,
                PRIMARY KEY (paper_id, keyword_id),
                FOREIGN KEY (paper_id) REFERENCES papers(id),
                FOREIGN KEY (keyword_id) REFERENCES keywords(id)
            );

            CREATE INDEX IF NOT EXISTS idx_papers_query ON papers(query);
            CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year);
            CREATE INDEX IF NOT EXISTS idx_papers_citation ON papers(citation_count);
            CREATE INDEX IF NOT EXISTS idx_papers_created_at ON papers(created_at);
            """
        )
        ensure_column(conn, "papers", "relevance_score", "REAL DEFAULT 0")
        ensure_column(conn, "papers", "rank_score", "REAL DEFAULT 0")


def upsert_paper(conn, paper, query):
    doi = paper.get("doi") or None
    existing_id = None
    if doi:
        existing = conn.execute("SELECT id FROM papers WHERE doi = ?", (doi,)).fetchone()
        if existing:
            existing_id = existing["id"]

    if existing_id:
        conn.execute(
            """
            UPDATE papers
            SET title = ?, year = ?, journal = ?, abstract = ?, citation_count = ?,
                relevance_score = ?, rank_score = ?, source = ?, url = ?, query = ?
            WHERE id = ?
            """,
            (
                paper.get("title", "Untitled"),
                paper.get("year"),
                paper.get("journal", ""),
                paper.get("abstract", ""),
                int(paper.get("citation_count") or 0),
                float(paper.get("relevance_score") or 0),
                float(paper.get("rank_score") or 0),
                paper.get("source", ""),
                paper.get("url", ""),
                query,
                existing_id,
            ),
        )
        paper_id = existing_id
    else:
        cursor = conn.execute(
            """
            INSERT INTO papers
            (title, doi, year, journal, abstract, citation_count, relevance_score, rank_score, source, url, query)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paper.get("title", "Untitled"),
                doi,
                paper.get("year"),
                paper.get("journal", ""),
                paper.get("abstract", ""),
                int(paper.get("citation_count") or 0),
                float(paper.get("relevance_score") or 0),
                float(paper.get("rank_score") or 0),
                paper.get("source", ""),
                paper.get("url", ""),
                query,
            ),
        )
        paper_id = cursor.lastrowid

    conn.execute("DELETE FROM paper_authors WHERE paper_id = ?", (paper_id,))
    conn.execute("DELETE FROM paper_keywords WHERE paper_id = ?", (paper_id,))

    for order, author_name in enumerate(paper.get("authors", []), start=1):
        conn.execute("INSERT OR IGNORE INTO authors(name) VALUES (?)", (author_name,))
        author_id = conn.execute("SELECT id FROM authors WHERE name = ?", (author_name,)).fetchone()["id"]
        conn.execute(
            """
            INSERT OR IGNORE INTO paper_authors(paper_id, author_id, author_order)
            VALUES (?, ?, ?)
            """,
            (paper_id, author_id, order),
        )

    for word in paper.get("keywords", []):
        conn.execute("INSERT OR IGNORE INTO keywords(word) VALUES (?)", (word,))
        keyword_id = conn.execute("SELECT id FROM keywords WHERE word = ?", (word,)).fetchone()["id"]
        conn.execute(
            "INSERT OR IGNORE INTO paper_keywords(paper_id, keyword_id) VALUES (?, ?)",
            (paper_id, keyword_id),
        )

    return paper_id


def save_papers(papers, query, db_path=DB_PATH):
    init_db(db_path)
    with get_connection(db_path) as conn:
        ids = [upsert_paper(conn, paper, query) for paper in papers]
    return ids


def rows_to_dicts(rows):
    return [dict(row) for row in rows]


def list_papers(query=None, limit=100, db_path=DB_PATH, include_demo=True):
    init_db(db_path)
    with get_connection(db_path) as conn:
        if query:
            like = f"%{query}%"
            sql = """
                SELECT *
                FROM papers
                WHERE (query LIKE ? OR title LIKE ? OR abstract LIKE ?)
            """
            params = [like, like, like]
            if not include_demo:
                sql += " AND COALESCE(source, '') != 'demo'"
            sql += """
                ORDER BY relevance_score DESC, rank_score DESC, citation_count DESC, COALESCE(year, 0) DESC
                LIMIT ?
            """
            params.append(limit)
            rows = conn.execute(
                sql,
                params,
            ).fetchall()
        else:
            sql = """
                SELECT *
                FROM papers
            """
            params = []
            if not include_demo:
                sql += " WHERE COALESCE(source, '') != 'demo'"
            sql += """
                ORDER BY created_at DESC, citation_count DESC
                LIMIT ?
            """
            params.append(limit)
            rows = conn.execute(
                sql,
                params,
            ).fetchall()
    return rows_to_dicts(rows)


def get_paper(paper_id, db_path=DB_PATH):
    init_db(db_path)
    with get_connection(db_path) as conn:
        paper = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
        if not paper:
            return None
        data = dict(paper)
        data["authors"] = [
            row["name"]
            for row in conn.execute(
                """
                SELECT a.name
                FROM authors a
                JOIN paper_authors pa ON pa.author_id = a.id
                WHERE pa.paper_id = ?
                ORDER BY pa.author_order
                """,
                (paper_id,),
            )
        ]
        data["keywords"] = [
            row["word"]
            for row in conn.execute(
                """
                SELECT k.word
                FROM keywords k
                JOIN paper_keywords pk ON pk.keyword_id = k.id
                WHERE pk.paper_id = ?
                ORDER BY k.word
                """,
                (paper_id,),
            )
        ]
    return data


def get_all_papers(db_path=DB_PATH):
    papers = list_papers(limit=1000, db_path=db_path)
    return [get_paper(paper["id"], db_path=db_path) for paper in papers]


def get_papers_by_ids(paper_ids, db_path=DB_PATH):
    if not paper_ids:
        return []
    return [paper for paper in (get_paper(paper_id, db_path=db_path) for paper_id in paper_ids) if paper]


def cached_query(query, db_path=DB_PATH, include_demo=False, limit=50):
    if not query:
        return []
    papers = list_papers(query=query, limit=limit, db_path=db_path, include_demo=include_demo)
    return [get_paper(paper["id"], db_path=db_path) for paper in papers]


def get_recent_queries(limit=5, db_path=DB_PATH):
    """Get recent search queries with count and last search time"""
    init_db(db_path)
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT query, COUNT(*) as count, MAX(created_at) as last_search
            FROM papers
            WHERE query IS NOT NULL AND query != '' AND COALESCE(source, '') != 'demo'
            GROUP BY query
            ORDER BY last_search DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return rows_to_dicts(rows)
