"""Pesquisa BM25 e escrita de runs no formato TREC."""

from __future__ import annotations

from pathlib import Path

from .preprocess import preprocess_many


def search(retriever, doc_ids: list[str], queries: dict[str, str], pipeline: str, k: int = 100) -> dict:
    """Devolve um run {qid: {doc_id: score}} com os top-k documentos por query."""
    qids = list(queries)
    q_tokens = preprocess_many([queries[q] for q in qids], pipeline)
    k = min(k, len(doc_ids))
    results, scores = retriever.retrieve(q_tokens, k=k, show_progress=False)
    run = {}
    for i, qid in enumerate(qids):
        run[qid] = {
            doc_ids[int(idx)]: float(score)
            for idx, score in zip(results[i], scores[i])
            if score > 0
        }
    return run


def write_trec_run(run: dict, path: Path, tag: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for qid, docs in run.items():
            ranked = sorted(docs.items(), key=lambda x: -x[1])
            for rank, (doc_id, score) in enumerate(ranked, start=1):
                f.write(f"{qid} Q0 {doc_id} {rank} {score:.4f} {tag}\n")
