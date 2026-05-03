---
title: Cross-Border Legal RAG
emoji: ⚖️
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
license: mit
python_version: 3.10.14
---
# Cross-Border Legal RAG

A **Retrieval-Augmented Generation (RAG)** system for cross-border private international law research, combining deterministic rule matching with hybrid dense+BM25 retrieval and a CPU cross-encoder reranker.

> **Educational use only — Not legal advice.**

---

## Features

- **Phase 1** — Real article corpus (Rome I, Rome II, Brussels Ia official texts)
- **Phase 2** — Hybrid retrieval: BM25 (top-150) + FAISS dense (top-40) → blended score
- **Phase 3** — Calibrated refusal: rejects out-of-scope queries below confidence threshold
- **Phase 4** — Deterministic rule layer: fact-driven article prepending before RAG
- **Phase 5** — Evaluation harness with 40 scenarios, refusal accuracy & article recall metrics
- **Phase 6** — Gradio UI with facts form, cited memo, and collapsible evidence panel
- **Phase 7** — CPU cross-encoder reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`)

---

## Quick Start

```bash
# 1. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build the FAISS index
python build_index.py

# 4. Launch the Gradio UI (requires Ollama running locally)
python app.py
```

The UI will be available at **http://localhost:7860**

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com/) running locally with `qwen2.5:3b-instruct-q4_0` pulled
  ```
  ollama pull qwen2.5:3b-instruct-q4_0
  ```

---

## Project Structure

```
crossborder-legal-rag/
├── app.py                    # Gradio UI (Phase 6)
├── build_index.py            # Build FAISS + BM25 index
├── embeddings.py             # Embedding model loader
├── retrieval.py              # Hybrid retrieval + cross-encoder reranker
├── rag_answer.py             # LLM orchestration + refusal logic
├── rules_evaluator.py        # Deterministic rule engine (Phase 4)
├── eval_harness.py           # Evaluation harness (Phase 5)
├── generate_eval_scenarios.py# Scenario dataset generator
├── search.py                 # CLI quick search utility
├── data/
│   └── raw/
│       └── legal_core.jsonl  # Official EU regulation texts
├── rules/
│   └── rome_rules.csv        # Rule definitions
└── eval/
    └── scenarios.jsonl       # 40 evaluation scenarios
```

---

## Corpus

Official texts from EUR-Lex:

| Instrument | CELEX | Articles |
|-----------|-------|---------|
| Rome I (Regulation (EC) No 593/2008) | 32008R0593 | Art. 4, 6, 8 |
| Rome II (Regulation (EC) No 864/2007) | 32007R0864 | Art. 4 |
| Brussels Ia (Regulation (EU) No 1215/2012) | 32012R1215 | Art. 7(1), 7(2) |
