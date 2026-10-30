"""Descarrega os dados necessários para data/.

- ori_pqal.json (PQA-L, 1000 perguntas anotadas) do repositório oficial do PubMedQA
- pqau_corpus.jsonl: abstracts do PQA-U (~61k) do HuggingFace (qiaojin/PubMedQA),
  usados como documentos distratores.
"""

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rbt.data import DATA_DIR, PQAL_PATH, PQAU_PATH, _doc_text  # noqa: E402

PQAL_URL = "https://raw.githubusercontent.com/pubmedqa/pubmedqa/master/data/ori_pqal.json"


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    if not PQAL_PATH.exists():
        print(f"A descarregar {PQAL_URL}")
        urllib.request.urlretrieve(PQAL_URL, PQAL_PATH)
    print(f"PQA-L: {PQAL_PATH}")

    if not PQAU_PATH.exists():
        from datasets import load_dataset

        ds = load_dataset("qiaojin/PubMedQA", "pqa_unlabeled", split="train")
        with open(PQAU_PATH, "w", encoding="utf-8") as f:
            for rec in ds:
                text = _doc_text(rec["context"]["contexts"], rec["long_answer"])
                f.write(json.dumps({"_id": str(rec["pubid"]), "text": text}) + "\n")
    print(f"PQA-U: {PQAU_PATH}")


if __name__ == "__main__":
    main()
