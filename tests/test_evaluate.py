import pytest

from rbt.evaluate import evaluate, paired_wilcoxon, truncate_run

QRELS = {"q1": {"d1": 1}, "q2": {"d2": 1}}


def test_perfect_run_scores_one():
    run = {"q1": {"d1": 2.0, "d9": 1.0}, "q2": {"d2": 3.0}}
    means, _ = evaluate(QRELS, run)
    for label in ("NDCG@5", "NDCG@10", "MRR@10", "MAP", "R@100"):
        assert means[label] == pytest.approx(1.0)


def test_relevant_at_rank_two():
    run = {"q1": {"d9": 2.0, "d1": 1.0}, "q2": {"d8": 2.0, "d2": 1.0}}
    means, _ = evaluate(QRELS, run)
    assert means["MRR@10"] == pytest.approx(0.5)
    assert means["MAP"] == pytest.approx(0.5)  # 1 relevante por query → MAP = MRR


def test_missing_query_counts_as_zero():
    run = {"q1": {"d1": 1.0}}
    means, _ = evaluate(QRELS, run)
    assert means["MRR@10"] == pytest.approx(0.5)
    assert means["NDCG@10"] == pytest.approx(0.5)


def test_mrr10_ignores_relevant_below_rank_ten():
    # relevante na posição 11: conta para o MAP mas não para o MRR@10 nem para o NDCG@10
    docs = {f"x{i}": 100.0 - i for i in range(10)}
    run = {"q1": {**docs, "d1": 1.0}}
    means, _ = evaluate({"q1": {"d1": 1}}, run)
    assert means["MRR@10"] == 0.0
    assert means["NDCG@10"] == 0.0
    assert means["MAP"] == pytest.approx(1 / 11)


def test_ndcg5_cut():
    docs = {f"x{i}": 100.0 - i for i in range(5)}
    run = {"q1": {**docs, "d1": 1.0}}  # relevante na posição 6
    means, _ = evaluate({"q1": {"d1": 1}}, run)
    assert means["NDCG@5"] == 0.0
    assert means["NDCG@10"] > 0.0


def test_truncate_run_keeps_best_scores():
    run = {"q": {"a": 1.0, "b": 3.0, "c": 2.0}}
    assert set(truncate_run(run, 2)["q"]) == {"b", "c"}


def test_wilcoxon_detects_consistent_difference():
    qrels = {f"q{i}": {"d": 1} for i in range(30)}
    better = {q: {"ndcg_cut_10": 1.0} for q in qrels}
    worse = {q: {"ndcg_cut_10": 0.5 - i / 100} for i, q in enumerate(qrels)}
    assert paired_wilcoxon(qrels, better, worse, "ndcg_cut_10") < 0.001
