---
tags:
  - law
  - rag
  - eu
  - conflicts-of-law
license: cc-by-4.0
pretty_name: Cross-Border Legal Core (EU PIL subset)
task_categories:
  - question-answering
  - text-retrieval
language:
  - en
---

# Cross-Border Legal Core (EU PIL Subset)

A curated subset of **EU private international law provisions** used as the retrieval corpus for the [Cross-Border Legal RAG](https://huggingface.co/spaces/SehaanCuda/crossborder-legal-rag) system.

> **Educational use only — Not legal advice.**

---

## What is in this dataset?

Selected mandatory provisions from three foundational EU regulations governing choice-of-law and jurisdiction in cross-border civil and commercial matters:

| Instrument | CELEX | Provisions Included |
|---|---|---|
| **Rome I** — Reg. (EC) No 593/2008 | 32008R0593 | Arts. 4, 6, 8 (sub-articles split) |
| **Rome II** — Reg. (EC) No 864/2007 | 32007R0864 | Art. 4 (sub-articles split) |
| **Brussels Ia** — Reg. (EU) No 1215/2012 | 32012R1215 | Art. 7(1), 7(2) |

Each record corresponds to one meaningful sub-article chunk, optimised for dense retrieval (~150–250 tokens per chunk).

---

## Fields

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique chunk identifier (e.g. `rome_i_art_6_1`) |
| `instrument` | string | Short name of the legal instrument (e.g. `Rome I`) |
| `jurisdiction` | string | Governing jurisdiction (always `EU` for this subset) |
| `article` | string | Article reference (e.g. `Art. 6(1)`) |
| `title` | string | Human-readable title of the provision |
| `text` | string | Verbatim statutory text of the provision |
| `url` | string | Permalink to the source EUR-Lex HTML page |
| `topics` | list[str] | Thematic tags (e.g. `["consumer protection", "choice of law"]`) |
| `date` | string | Date of the regulation (ISO 8601) |
| `celex` | string | Official EUR-Lex CELEX identifier |

---

## Source and Reuse

Text is sourced from the official **EUR-Lex** portal. Official EU legal acts are in the public domain under the [EUR-Lex reuse policy](https://eur-lex.europa.eu/content/legal-notice/legal-notice.html). Always cite CELEX IDs and link to the source pages when reproducing this material.

The dataset metadata is licensed under **CC BY 4.0**.

---

## Intended Use

- Educational legal research
- Retrieval-Augmented Generation (RAG) experiments in the legal domain
- Benchmarking embedding models on EU statutory text

---

## Limitations

- **Partial coverage**: Only the specific sub-articles most relevant to cross-border PIL scenarios are included.
- **EU focus**: Does not cover national laws, case law, or non-EU jurisdictions.
- **Static snapshot**: Regulation amendments enacted after the scrape date are not reflected.
- **Not legal advice**: This dataset must not be used as the sole basis for legal decisions.

---

## Citation

If you use this dataset in your work, please cite:

```bibtex
@misc{crossborder_legal_core_2025,
  title        = {Cross-Border Legal Core (EU PIL Subset)},
  author       = {SehaanCuda},
  year         = {2025},
  howpublished = {Hugging Face Datasets},
  url          = {https://huggingface.co/datasets/SehaanCuda/crossborder_legal_core}
}
```
