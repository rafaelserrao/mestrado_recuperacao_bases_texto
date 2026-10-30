"""Corre a grelha corpus × pré-processamento × (k1, b) e grava runs e resultados.

Uso:
    python scripts/run_experiments.py                 # ambos os corpora
    python scripts/run_experiments.py --corpora pqal  # só PQA-L
"""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rbt.data import build_corpus  # noqa: E402
from rbt.evaluate import evaluate, paired_wilcoxon  # noqa: E402
from rbt.index import INDEX_DIR, index_tokens, save_index  # noqa: E402
from rbt.preprocess import PIPELINES, preprocess_many  # noqa: E402
from rbt.search import search, write_trec_run  # noqa: E402

K1_VALUES = (0.9, 1.2, 1.5)
B_VALUES = (0.4, 0.75)
DEFAULT_PARAMS = (1.2, 0.75)
RESULTS_DIR = ROOT / "results"
RUNS_DIR = ROOT / "runs"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpora", nargs="+", default=["pqal", "pqal+pqau"])
    args = parser.parse_args()

    RESULTS_DIR.mkdir(exist_ok=True)
    rows, stats, per_query_all, qrels_all = [], [], {}, {}
    for corpus_name in args.corpora:
        corpus, queries, qrels = build_corpus(corpus_name)
        qrels_all[corpus_name] = qrels
        doc_ids = list(corpus)
        texts = [corpus[d] for d in doc_ids]
        for pipeline in PIPELINES:
            t0 = time.perf_counter()
            tokens = preprocess_many(texts, pipeline)
            prep_s = time.perf_counter() - t0
            stats.append({
                "corpus": corpus_name,
                "pipeline": pipeline,
                "docs": len(doc_ids),
                "vocab": len({t for doc in tokens for t in doc}),
                "avg_doc_len": sum(map(len, tokens)) / len(tokens),
                "prep_s": round(prep_s, 1),
            })
            for k1 in K1_VALUES:
                for b in B_VALUES:
                    t0 = time.perf_counter()
                    retriever = index_tokens(tokens, k1, b)
                    index_s = time.perf_counter() - t0
                    t0 = time.perf_counter()
                    run = search(retriever, doc_ids, queries, pipeline, k=100)
                    search_s = time.perf_counter() - t0
                    means, per_query = evaluate(qrels, run)
                    per_query_all[(corpus_name, pipeline, k1, b)] = per_query
                    tag = f"{corpus_name.replace('+', '_')}_{pipeline}_k{k1}_b{b}"
                    write_trec_run(run, RUNS_DIR / f"{tag}.trec", tag)
                    if (k1, b) == DEFAULT_PARAMS:
                        save_index(retriever, doc_ids, INDEX_DIR / f"{corpus_name.replace('+', '_')}_{pipeline}")
                    rows.append({
                        "corpus": corpus_name, "pipeline": pipeline, "k1": k1, "b": b,
                        **{m: round(v, 4) for m, v in means.items()},
                        "index_s": round(index_s, 2), "search_s": round(search_s, 2),
                    })
                    print(rows[-1], flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_DIR / "results.csv", index=False)
    (RESULTS_DIR / "results.md").write_text(df.to_markdown(index=False) + "\n")
    (RESULTS_DIR / "significance.md").write_text(significance(df, per_query_all, qrels_all))
    st = pd.DataFrame(stats)
    st["avg_doc_len"] = st["avg_doc_len"].round(1)
    (RESULTS_DIR / "stats.md").write_text(st.to_markdown(index=False) + "\n")
    print(df.to_markdown(index=False))


def significance(df: pd.DataFrame, per_query_all: dict, qrels_all: dict) -> str:
    """Testes de Wilcoxon emparelhados entre a melhor configuração de cada pipeline."""
    rows = []
    for corpus_name, qrels in qrels_all.items():
        sub = df[df.corpus == corpus_name]
        best = {
            pipeline: tuple(sub[sub.pipeline == pipeline].sort_values("NDCG@10").iloc[-1][["k1", "b"]])
            for pipeline in sub.pipeline.unique()
        }
        pairs = [
            (("stop", *best["stop"]), ("lower", *best["lower"])),
            (("stop_stem", *best["stop_stem"]), ("lower", *best["lower"])),
            (("stop_stem", *best["stop_stem"]), ("stop", *best["stop"])),
            (("stop_stem", *best["stop_stem"]), ("stop_stem", *DEFAULT_PARAMS)),
        ]
        for a, b in pairs:
            if a == b:
                continue
            pq_a, pq_b = per_query_all[(corpus_name, *a)], per_query_all[(corpus_name, *b)]
            row = {"corpus": corpus_name, "A": "{} k1={} b={}".format(*a), "B": "{} k1={} b={}".format(*b)}
            for measure, label in (("ndcg_cut_10", "NDCG@10"), ("recip_rank@10", "MRR@10")):
                mean_a = sum(pq_a.get(q, {}).get(measure, 0.0) for q in qrels) / len(qrels)
                mean_b = sum(pq_b.get(q, {}).get(measure, 0.0) for q in qrels) / len(qrels)
                row[f"Δ {label}"] = round(mean_a - mean_b, 4)
                row[f"p {label}"] = float(f"{paired_wilcoxon(qrels, pq_a, pq_b, measure):.2g}")
            rows.append(row)
    return pd.DataFrame(rows).to_markdown(index=False) + "\n"


if __name__ == "__main__":
    main()
