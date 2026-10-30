"""Avaliação com pytrec_eval: NDCG@5, NDCG@10, MRR@10, MAP e Recall@100."""

from __future__ import annotations

import pytrec_eval
from scipy.stats import wilcoxon

# nome da medida no pytrec_eval -> nome no relatório
MEASURES = {
    "ndcg_cut_5": "NDCG@5",
    "ndcg_cut_10": "NDCG@10",
    "recip_rank@10": "MRR@10",
    "map": "MAP",
    "recall_100": "R@100",
}


def truncate_run(run: dict, k: int) -> dict:
    """Mantém apenas os top-k documentos de cada query."""
    return {
        qid: dict(sorted(docs.items(), key=lambda x: -x[1])[:k])
        for qid, docs in run.items()
    }


def evaluate(qrels: dict, run: dict) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    """Devolve (médias, valores por query).

    O trec_eval não tem corte para o recip_rank, por isso o MRR@10 é o
    recip_rank calculado sobre o run truncado aos 10 primeiros.
    Queries presentes nos qrels mas sem resultados no run contam como 0.
    """
    evaluator = pytrec_eval.RelevanceEvaluator(qrels, {"ndcg_cut.5,10", "map", "recall.100"})
    per_query = evaluator.evaluate(run)
    rr10 = pytrec_eval.RelevanceEvaluator(qrels, {"recip_rank"}).evaluate(truncate_run(run, 10))
    for qid, values in rr10.items():
        per_query.setdefault(qid, {})["recip_rank@10"] = values["recip_rank"]
    means = {}
    for measure, label in MEASURES.items():
        total = sum(per_query.get(qid, {}).get(measure, 0.0) for qid in qrels)
        means[label] = total / len(qrels)
    return means, per_query


def paired_wilcoxon(qrels: dict, per_query_a: dict, per_query_b: dict, measure: str) -> float:
    """p-value do teste de Wilcoxon emparelhado (por query) entre dois sistemas."""
    a = [per_query_a.get(q, {}).get(measure, 0.0) for q in qrels]
    b = [per_query_b.get(q, {}).get(measure, 0.0) for q in qrels]
    return float(wilcoxon(a, b).pvalue)
