"""Pipelines de pré-processamento de texto.

- ``lower``:      minúsculas + tokenização regex (tokens alfanuméricos com ≥ 2 caracteres)
- ``stop``:       ``lower`` + remoção de stopwords em inglês
- ``stop_stem``:  ``stop`` + stemming Snowball (inglês)
"""

from __future__ import annotations

import re
from functools import lru_cache

import Stemmer
from bm25s.stopwords import STOPWORDS_EN

PIPELINES = ("lower", "stop", "stop_stem")

_TOKEN_RE = re.compile(r"(?u)\b\w\w+\b")
_STOPWORDS = frozenset(STOPWORDS_EN)


@lru_cache(maxsize=1)
def _stemmer():
    return Stemmer.Stemmer("english")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def preprocess(text: str, pipeline: str) -> list[str]:
    if pipeline not in PIPELINES:
        raise ValueError(f"pipeline desconhecido: {pipeline}")
    tokens = tokenize(text)
    if pipeline in ("stop", "stop_stem"):
        tokens = [t for t in tokens if t not in _STOPWORDS]
    if pipeline == "stop_stem":
        tokens = _stemmer().stemWords(tokens)
    return tokens


def preprocess_many(texts: list[str], pipeline: str) -> list[list[str]]:
    return [preprocess(t, pipeline) for t in texts]
