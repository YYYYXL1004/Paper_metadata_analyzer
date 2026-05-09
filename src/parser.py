import xml.etree.ElementTree as ET

from src.extractor import extract_doi, extract_keywords, extract_year, normalize_space, strip_html


def first_text(value, default=""):
    if isinstance(value, list) and value:
        return normalize_space(strip_html(value[0]))
    if isinstance(value, str):
        return normalize_space(strip_html(value))
    return default


def date_parts_to_year(date_obj):
    try:
        return int(date_obj["date-parts"][0][0])
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def restore_openalex_abstract(index):
    if not index:
        return ""
    positions = []
    for word, word_positions in index.items():
        for position in word_positions:
            positions.append((position, word))
    return normalize_space(" ".join(word for _, word in sorted(positions)))


def openalex_source_name(item):
    location = item.get("primary_location") or {}
    source = location.get("source") or {}
    return source.get("display_name") or source.get("host_organization_name") or ""


def openalex_url(item):
    location = item.get("primary_location") or {}
    if location.get("landing_page_url"):
        return location["landing_page_url"]
    return item.get("doi") or item.get("id", "")


def parse_crossref_response(data):
    items = data.get("message", {}).get("items", [])
    papers = []
    for item in items:
        title = first_text(item.get("title"))
        abstract = first_text(item.get("abstract"))
        doi = extract_doi(item.get("DOI"), item.get("URL"), title, abstract)

        year = (
            date_parts_to_year(item.get("published-print"))
            or date_parts_to_year(item.get("published-online"))
            or date_parts_to_year(item.get("issued"))
            or extract_year(title, abstract)
        )

        authors = []
        for author in item.get("author", []) or []:
            name = normalize_space(
                " ".join(
                    part
                    for part in [author.get("given", ""), author.get("family", "")]
                    if part
                )
            )
            if name:
                authors.append(name)

        subject_words = []
        for subject in item.get("subject", []) or []:
            subject_words.extend(extract_keywords(subject, "", top_n=3))

        keywords = extract_keywords(title, abstract, top_n=8)
        for word in subject_words:
            if word not in keywords:
                keywords.append(word)

        papers.append(
            {
                "title": title or "未命名论文",
                "doi": doi,
                "year": year,
                "journal": first_text(item.get("container-title")),
                "abstract": abstract,
                "citation_count": int(item.get("is-referenced-by-count") or 0),
                "source": "crossref",
                "url": item.get("URL", ""),
                "authors": authors,
                "keywords": keywords[:10],
            }
        )
    return papers


def parse_arxiv_response(xml_text):
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    papers = []

    for entry in root.findall("atom:entry", namespace):
        title = normalize_space(entry.findtext("atom:title", default="", namespaces=namespace))
        abstract = normalize_space(entry.findtext("atom:summary", default="", namespaces=namespace))
        published = entry.findtext("atom:published", default="", namespaces=namespace)
        url = entry.findtext("atom:id", default="", namespaces=namespace)
        doi = extract_doi(abstract, url)
        for link in entry.findall("atom:link", namespace):
            title_attr = (link.attrib.get("title") or "").lower()
            href = link.attrib.get("href", "")
            if title_attr == "doi" or "doi.org" in href:
                doi = extract_doi(href) or doi

        authors = []
        for node in entry.findall("atom:author", namespace):
            name = normalize_space(node.findtext("atom:name", default="", namespaces=namespace))
            if name:
                authors.append(name)

        papers.append(
            {
                "title": title or "未命名论文",
                "doi": doi.lower() if doi else "",
                "year": extract_year(published),
                "journal": "arXiv",
                "abstract": abstract,
                "citation_count": 0,
                "source": "arxiv",
                "url": url,
                "authors": authors,
                "keywords": extract_keywords(title, abstract, top_n=10),
            }
        )
    return papers


def parse_openalex_response(data):
    items = data.get("results", [])
    papers = []
    for item in items:
        title = normalize_space(item.get("display_name", ""))
        abstract = restore_openalex_abstract(item.get("abstract_inverted_index"))
        authors = []
        for authorship in item.get("authorships", []) or []:
            author = authorship.get("author") or {}
            name = normalize_space(author.get("display_name", ""))
            if name:
                authors.append(name)

        keywords = extract_keywords(title, abstract, top_n=8)
        for concept in item.get("concepts", []) or []:
            concept_name = normalize_space(concept.get("display_name", "")).lower()
            if concept_name and concept_name not in keywords:
                keywords.append(concept_name)

        papers.append(
            {
                "title": title or "未命名论文",
                "doi": extract_doi(item.get("doi")) or extract_doi(item.get("id")),
                "year": item.get("publication_year"),
                "journal": openalex_source_name(item),
                "abstract": abstract,
                "citation_count": int(item.get("cited_by_count") or 0),
                "source": "openalex",
                "url": openalex_url(item),
                "authors": authors,
                "keywords": keywords[:10],
            }
        )
    return papers
