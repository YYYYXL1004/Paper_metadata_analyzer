import csv
from pathlib import Path

from config import EXPORT_DIR


def export_papers_to_csv(papers, filename="papers.csv", export_dir=EXPORT_DIR):
    Path(export_dir).mkdir(parents=True, exist_ok=True)
    path = Path(export_dir) / filename
    columns = [
        "id",
        "title",
        "doi",
        "year",
        "journal",
        "citation_count",
        "source",
        "url",
        "authors",
        "keywords",
    ]

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for paper in papers:
            row = {key: paper.get(key, "") for key in columns}
            row["authors"] = "; ".join(paper.get("authors", []))
            row["keywords"] = "; ".join(paper.get("keywords", []))
            writer.writerow(row)
    return path
