# mestrado_recuperacao_bases_texto
Projeto para a disciplina Recuperação de informações em bases de texto.

## Milestone 1 — BM25 sobre PubMedQA

Indexação do corpus PubMedQA, pré-processamento, pesquisa lexical BM25 e avaliação com
`pytrec_eval` (NDCG@5, NDCG@10, MRR@10, MAP, Recall@100) e testes de Wilcoxon entre configurações. O relatório técnico está em [`report/relatorio.md`](report/relatorio.md)
e os resultados em [`results/`](results/).

### Formulação
- **Queries**: as 1 000 perguntas do PQA-L (`QUESTION`).
- **Documentos**: abstracts (`CONTEXTS` + `LONG_ANSWER`), identificados pelo PMID.
- **Qrels**: cada pergunta tem como único relevante o abstract de onde foi extraída.
- **Corpora**: `pqal` (1 000 abstracts) e `pqal+pqau` (PQA-L + 61 249 abstracts do PQA-U como distratores).

### Como executar

**Requisitos:** Python 3.10 ou superior, cerca de 1 GB livre em disco (ambiente, dados, índices e runs) e ligação à internet
para descarregar os dados. Não é preciso GPU nem Java: tudo corre em CPU.

**1. Clonar o repositório e criar o ambiente virtual**
```bash
git clone https://github.com/rafaelserrao/mestrado_recuperacao_bases_texto.git
cd mestrado_recuperacao_bases_texto
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```
No Windows, use `.venv\Scripts\python` em vez de `.venv/bin/python`.

**2. Descarregar os dados** (cerca de 100 MB, para `data/`)
```bash
.venv/bin/python scripts/download_data.py
```
Descarrega o `ori_pqal.json` (PQA-L) do repositório oficial do PubMedQA e os abstracts do PQA-U
do Hugging Face (`qiaojin/PubMedQA`). Os ficheiros que já existem não são descarregados de novo.

**3. Correr os testes**
```bash
.venv/bin/python -m pytest
```

**4. Correr as experiências**
```bash
.venv/bin/python scripts/run_experiments.py                  # ambos os corpora (~1 min)
.venv/bin/python scripts/run_experiments.py --corpora pqal   # só PQA-L (segundos)
```
Corre a grelha corpus × pré-processamento × k1 ∈ {0,9; 1,2; 1,5} × b ∈ {0,4; 0,75}
(36 configurações) e gera:

| Saída | Conteúdo |
|---|---|
| `results/results.md`, `results/results.csv` | NDCG@5, NDCG@10, MRR@10, MAP, R@100 e tempos de cada configuração |
| `results/significance.md` | testes de Wilcoxon emparelhados entre as melhores configurações |
| `results/stats.md` | estatísticas do corpus (documentos, vocabulário, comprimento médio) |
| `runs/*.trec` | top-100 por query em formato TREC (`qid Q0 docid rank score tag`) |
| `indexes/` | índices BM25 guardados com os parâmetros por omissão (k1 = 1,2; b = 0,75) |

As pastas `data/`, `runs/` e `indexes/` não estão no repositório porque são geradas pelos passos 2 e 4.

### Estrutura
| Caminho | Conteúdo |
|---|---|
| `src/rbt/data.py` | carregamento do PubMedQA → corpus, queries, qrels |
| `src/rbt/preprocess.py` | pipelines `lower`, `stop`, `stop_stem` |
| `src/rbt/index.py` | indexação BM25 (bm25s, variante Lucene) |
| `src/rbt/search.py` | pesquisa top-100 e escrita de runs TREC |
| `src/rbt/evaluate.py` | avaliação com pytrec_eval e teste de Wilcoxon |
| `scripts/run_experiments.py` | grelha corpus × pré-processamento × (k1, b) |
| `results/results.md` | métricas das 36 configurações |
| `results/significance.md` | testes de Wilcoxon emparelhados |
