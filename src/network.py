from itertools import combinations

import numpy as np


def build_author_network(papers):
    authors = sorted({author for paper in papers for author in paper.get("authors", [])})
    index = {author: i for i, author in enumerate(authors)}
    matrix = np.zeros((len(authors), len(authors)), dtype=int)

    for paper in papers:
        paper_authors = sorted(set(paper.get("authors", [])))
        for a, b in combinations(paper_authors, 2):
            i, j = index[a], index[b]
            matrix[i, j] += 1
            matrix[j, i] += 1

    centrality = []
    if len(authors):
        scores = matrix.sum(axis=1)
        centrality = sorted(
            [(authors[i], int(scores[i])) for i in range(len(authors))],
            key=lambda item: item[1],
            reverse=True,
        )

    edges = []
    for i, author in enumerate(authors):
        for j in range(i + 1, len(authors)):
            if matrix[i, j] > 0:
                edges.append((author, authors[j], int(matrix[i, j])))

    edge_count = len(edges)
    possible_edges = len(authors) * (len(authors) - 1) / 2
    density = round(edge_count / possible_edges, 3) if possible_edges else 0
    isolated_count = 0
    if len(authors):
        isolated_count = int((matrix.sum(axis=1) == 0).sum())

    return {
        "authors": authors,
        "matrix": matrix,
        "centrality": centrality[:10],
        "edges": sorted(edges, key=lambda item: item[2], reverse=True)[:20],
        "edge_count": edge_count,
        "density": density,
        "isolated_count": isolated_count,
        "max_weight": max((edge[2] for edge in edges), default=0),
    }
