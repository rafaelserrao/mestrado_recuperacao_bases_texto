from rbt.index import build_index
from rbt.preprocess import preprocess
from rbt.search import search

TEXT = "Do the Mitochondria play a role in remodelling of plant leaves?"


def test_lower_tokenizes_and_lowercases():
    assert preprocess(TEXT, "lower") == [
        "do", "the", "mitochondria", "play", "role", "in", "remodelling", "of", "plant", "leaves",
    ]


def test_stop_removes_stopwords():
    tokens = preprocess(TEXT, "stop")
    assert "the" not in tokens and "of" not in tokens
    assert "mitochondria" in tokens


def test_stop_stem_stems():
    tokens = preprocess(TEXT, "stop_stem")
    assert "leav" in tokens and "remodel" in tokens


def test_search_finds_matching_document():
    corpus = {
        "a": "Mitochondria dynamics during programmed cell death in plants.",
        "b": "Randomized trial of statins in cardiovascular disease.",
        "c": "Survey of nurses about workload in intensive care units.",
    }
    for pipeline in ("lower", "stop", "stop_stem"):
        retriever, doc_ids = build_index(corpus, pipeline)
        run = search(retriever, doc_ids, {"q": "Do statins reduce cardiovascular events?"}, pipeline, k=3)
        assert max(run["q"], key=run["q"].get) == "b"
