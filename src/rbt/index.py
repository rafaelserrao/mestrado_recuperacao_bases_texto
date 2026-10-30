"""Construção, gravação e carregamento de índices BM25 (bm25s)."""

from __future__ import annotations

import json
from pathlib import Path

import bm25s

from .preprocess import preprocess_many

INDEX_DIR = Path(__file__).resolve().parents[2] / "indexes"


def index_tokens(tokens: list[list[str]], k1: float = 1.2, b: float = 0.75):
    """Indexa documentos já pré-processados.

    O bm25s pré-calcula os scores no momento da indexação, por isso cada
    combinação (k1, b) exige um índice próprio.
    """
    retriever = bm25s.BM25(k1=k1, b=b, method="lucene")
    retriever.index(tokens, show_progress=False)
    return retriever


def build_index(corpus: dict[str, str], pipeline: str, k1: float = 1.2, b: float = 0.75):
    """Indexa o corpus e devolve (retriever, doc_ids na ordem do índice)."""
    doc_ids = list(corpus)
    tokens = preprocess_many([corpus[d] for d in doc_ids], pipeline)
    return index_tokens(tokens, k1, b), doc_ids


def save_index(retriever, doc_ids: list[str], path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    retriever.save(str(path))
    (path / "doc_ids.json").write_text(json.dumps(doc_ids))


def load_index(path: Path):
    retriever = bm25s.BM25.load(str(path))
    doc_ids = json.loads((path / "doc_ids.json").read_text())
    return retriever, doc_ids
