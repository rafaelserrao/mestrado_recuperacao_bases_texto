"""Carregamento do PubMedQA e construção de corpus, queries e qrels."""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PQAL_PATH = DATA_DIR / "ori_pqal.json"
PQAU_PATH = DATA_DIR / "pqau_corpus.jsonl"


def _doc_text(contexts: list[str], long_answer: str) -> str:
    return " ".join(list(contexts) + [long_answer]).strip()


def load_pqal(path: Path = PQAL_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_pqal(path: Path = PQAL_PATH):
    """Devolve (corpus, queries, qrels) para o PQA-L.

    corpus:  {doc_id: texto do abstract}
    queries: {qid: pergunta}
    qrels:   {qid: {doc_id: 1}}  (um único documento relevante por pergunta)
    """
    raw = load_pqal(path)
    corpus, queries, qrels = {}, {}, {}
    for pmid, item in raw.items():
        corpus[pmid] = _doc_text(item["CONTEXTS"], item["LONG_ANSWER"])
        queries[pmid] = item["QUESTION"]
        qrels[pmid] = {pmid: 1}
    return corpus, queries, qrels


def load_pqau_corpus(path: Path = PQAU_PATH) -> dict[str, str]:
    """Abstracts do PQA-U (distratores), gerados por scripts/download_data.py."""
    corpus = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            corpus[rec["_id"]] = rec["text"]
    return corpus


def build_corpus(name: str):
    """name ∈ {'pqal', 'pqal+pqau'}. Queries e qrels são sempre as do PQA-L."""
    corpus, queries, qrels = build_pqal()
    if name == "pqal":
        return corpus, queries, qrels
    if name == "pqal+pqau":
        extra = load_pqau_corpus()
        overlap = extra.keys() & corpus.keys()
        if overlap:
            raise ValueError(f"PMIDs repetidos entre PQA-L e PQA-U: {len(overlap)}")
        return {**corpus, **extra}, queries, qrels
    raise ValueError(f"corpus desconhecido: {name}")
