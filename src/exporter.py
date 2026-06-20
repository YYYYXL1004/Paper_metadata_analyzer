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


def export_papers_to_bibtex(papers, filename="papers.bib", export_dir=EXPORT_DIR):
    """Export papers to BibTeX format for academic citation management"""
    Path(export_dir).mkdir(parents=True, exist_ok=True)
    path = Path(export_dir) / filename

    with path.open("w", encoding="utf-8") as file:
        for paper in papers:
            # Generate unique citation key
            first_author = paper.get("authors", ["Unknown"])[0].split()[-1] if paper.get("authors") else "Unknown"
            year = paper.get("year", "")
            title_word = paper.get("title", "").split()[0][:10] if paper.get("title") else "paper"
            cite_key = f"{first_author}{year}{title_word}".replace(" ", "")

            file.write(f"@article{{{cite_key},\n")
            file.write(f"  title = {{{paper.get('title', 'Untitled')}}},\n")

            if paper.get("authors"):
                authors = " and ".join(paper.get("authors", []))
                file.write(f"  author = {{{authors}}},\n")

            if paper.get("year"):
                file.write(f"  year = {{{paper.get('year')}}},\n")

            if paper.get("journal"):
                file.write(f"  journal = {{{paper.get('journal')}}},\n")

            if paper.get("doi"):
                file.write(f"  doi = {{{paper.get('doi')}}},\n")

            if paper.get("url"):
                file.write(f"  url = {{{paper.get('url')}}},\n")

            if paper.get("abstract"):
                abstract = paper.get("abstract", "").replace("{", "\\{").replace("}", "\\}")
                file.write(f"  abstract = {{{abstract}}},\n")

            if paper.get("keywords"):
                keywords = ", ".join(paper.get("keywords", []))
                file.write(f"  keywords = {{{keywords}}},\n")

            file.write("}\n\n")

    return path
