---
title: Cross-Border Legal RAG
emoji: ⚖️
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 4.42.0
app_file: app.py
pinned: false
license: mit
python_version: 3.10.14
---

<div align="center">

# ⚖️ Cross-Border Legal RAG

### Production-grade Retrieval-Augmented Generation for EU Private International Law

[![Hugging Face Space](https://img.shields.io/badge/🤗%20Space-Live%20Demo-blue)](https://huggingface.co/spaces/SehaanCuda/crossborder-legal-rag)
[![HF Dataset](https://img.shields.io/badge/🤗%20Dataset-crossborder__legal__core-orange)](https://huggingface.co/datasets/SehaanCuda/crossborder_legal_core)
[![GitHub Release](https://img.shields.io/badge/release-v1.0.0-green)](https://github.com/Sehaan-1/crossborder-legal-rag/releases/tag/v1.0.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10](https://img.shields.io/badge/Python-3.10.14-blue)](https://python.org)
[![Eval: 78% Recall](https://img.shields.io/badge/Eval-78%25%20Recall-brightgreen)](eval/REPORT.md)

> **Educational use only — Not legal advice.**  
> Do not submit personal data, client names, or confidential case details.

</div>

---

## 🔗 Artifact Index

| Artifact | Link |
|---|---|
| 🌐 **Live Demo** | [huggingface.co/spaces/SehaanCuda/crossborder-legal-rag](https://huggingface.co/spaces/SehaanCuda/crossborder-legal-rag) |
| 📦 **Code (v1.0.0)** | [github.com/Sehaan-1/crossborder-legal-rag](https://github.com/Sehaan-1/crossborder-legal-rag/releases/tag/v1.0.0) |
| 🗂️ **Dataset** | [SehaanCuda/crossborder_legal_core](https://huggingface.co/datasets/SehaanCuda/crossborder_legal_core) |
| 📊 **Eval Report** | [eval/REPORT.md](eval/REPORT.md) |
| 🏗️ **System Card** | [SYSTEM_CARD.md](SYSTEM_CARD.md) |
| 🔒 **Privacy Policy** | [PRIVACY.md](PRIVACY.md) |

---

## ✨ What It Does

The system answers **cross-border legal scenario queries** using EU regulations as its knowledge base. Given a factual scenario — e.g. a French consumer buying from a German online trader — it:

1. **Fires deterministic rules** (e.g. Rome I Art. 6 for consumer contracts) based on your checked facts
2. **Retrieves** the most relevant statutory provisions using hybrid BM25 + dense embeddings
3. **Reranks** candidates with a cross-encoder for maximum precision
4. **Generates** a concise, cited 5–7 bullet legal memo via the Groq API

Every output includes **inline citations** (`[1]`, `[2]`, ...) mapped back to specific EU regulation articles, and a **confidence badge** (🟢 High / 🟡 Medium / 🔴 Low) based on retrieval quality.

---

## 🏗️ Architecture

```
User Query + Facts
        │
        ▼
┌─────────────────────────────┐
│  Synonym Expansion          │  B2C → business-to-consumer; PIL → private international law
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐   ┌───────────────────────┐
│  Deterministic Rule Engine  │──►│  rome_rules.csv        │
│  (rules_evaluator.py)       │   └───────────────────────┘
│  consumer / tort /          │──► prepends mandatory article chunks
│  employment / no_choice     │
└─────────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────┐
│  Hybrid Retrieval                                    │
│  BM25 top-150 ──┐                                    │
│                 ├── Blended (0.6 dense + 0.4 BM25)  │
│  FAISS top-40 ──┘   → top-20 candidates             │
└──────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  Cosine Similarity Dedup    │  drops passages with similarity > 0.95
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  Cross-Encoder Reranker     │  ms-marco-MiniLM-L-6-v2 (local only)
│  (disabled on HF Spaces)    │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  Refusal Guard              │  dense < 0.65 AND bm25 < 4.0 → refuse
│  (bypassed if rule fired)   │
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│  LLM Generation             │  Groq llama-3.1-8b-instant (~5s)
│  Fallback: Ollama (local)   │  qwen2.5:3b-instruct-q4_0
└─────────────────────────────┘
        │
        ▼
  5–7 Bullet Legal Memo with Inline Citations
```

---

## 📦 Corpus

Official text from **EUR-Lex** (public domain). CELEX IDs preserved for traceability.

| Instrument | CELEX | Provisions | Topic |
|---|---|---|---|
| **Rome I** Reg. (EC) No 593/2008 | 32008R0593 | Art. 3, 4, 6, 8, 9 | Choice of law — contracts |
| **Rome II** Reg. (EC) No 864/2007 | 32007R0864 | Art. 4(1–3), 5 | Choice of law — torts |
| **Brussels Ia** Reg. (EU) No 1215/2012 | 32012R1215 | Art. 7(1), 7(2) | Jurisdiction |

Dataset: [SehaanCuda/crossborder_legal_core](https://huggingface.co/datasets/SehaanCuda/crossborder_legal_core)

---

## 📊 Evaluation Results (v1.0.0)

**Config**: Hybrid k=4 · Rules ON · Groq llama-3.1-8b-instant · T=0.2

| Metric | Value | Target |
|---|---|---|
| Article Recall (overall) | **~78%** | ≥ 75% ✅ |
| Article Recall (consumer/employment) | **~88%** | ≥ 85% ✅ |
| Refusal Accuracy | **~85%** | ≥ 80% ✅ |
| p95 Latency (Space, warm) | **~9s** | ≤ 10s ✅ |
| p95 Latency (local, Ollama) | **~14s** | ≤ 15s ✅ |

📄 Full report with ablations and error analysis: [eval/REPORT.md](eval/REPORT.md)

---

## 🚀 Quickstart

### Cloud (Hugging Face Space)
Visit [huggingface.co/spaces/SehaanCuda/crossborder-legal-rag](https://huggingface.co/spaces/SehaanCuda/crossborder-legal-rag) — no setup required.

### Local Setup

**Prerequisites**: Python 3.10+, Git, [Ollama](https://ollama.com) (for local inference)

```bash
# 1. Clone
git clone https://github.com/Sehaan-1/crossborder-legal-rag.git
cd crossborder-legal-rag

# 2. Install (pinned exact versions in requirements.lock.txt)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Build the FAISS index
python build_index.py

# 4a. Run with Groq API (fast, free)
export GROQ_API_KEY=gsk_...
bash run_local.sh --groq

# 4b. Run with local Ollama (no API key needed)
ollama pull qwen2.5:3b-instruct-q4_0
bash run_local.sh --ollama
```

Open **http://localhost:7860** in your browser.

### Run Evaluation

```bash
# Full eval suite (120 scenarios)
bash run_eval.sh groq 4

# With specific options
python eval_harness.py \
    --scenarios eval/scenarios.jsonl \
    --provider groq \
    --model llama-3.1-8b-instant \
    --k-final 4 \
    --max-tokens 256 \
    --out eval/results/my_run.jsonl
```

---

## 🗂️ Repository Structure

```
crossborder-legal-rag/
│
├── app.py                       # Gradio UI entrypoint
├── rag_answer.py                # LLM orchestration + Groq/Ollama backend
├── retrieval.py                 # Hybrid BM25+FAISS retrieval + dedup + reranker
├── rules_evaluator.py           # Deterministic rule engine
├── embeddings.py                # Sentence-transformer loader
├── build_index.py               # Builds FAISS + BM25 index from corpus
├── search.py                    # CLI quick-search utility
│
├── run_local.sh                 # Reproducibility: local startup script
├── run_eval.sh                  # Reproducibility: evaluation runner
├── generate_eval_scenarios_v2.py# Generates expanded 120-scenario eval set
├── eval_harness.py              # Phase 11 evaluation harness (CLI)
│
├── data/raw/
│   └── legal_core.jsonl         # EU PIL corpus (Rome I/II, Brussels Ia)
│
├── index/
│   ├── faiss.index              # FAISS vector index (LFS tracked)
│   └── meta.jsonl               # Passage metadata
│
├── models/                      # Local GGUF model (optional, LFS tracked)
│
├── rules/
│   └── rome_rules.csv           # Deterministic rule definitions
│
├── synonyms.json                # Query expansion map
│
├── eval/
│   ├── scenarios.jsonl          # 120 evaluation scenarios (4 buckets)
│   ├── failures.csv             # Most recent failure log
│   ├── ablations.md             # Ablation study results
│   ├── REPORT.md                # Final evaluation report
│   └── results/                 # Per-run JSONL + summary.csv
│
├── README.md                    # This file
├── SYSTEM_CARD.md               # Architecture, prompt format, thresholds
├── ARCHITECTURE.md              # Phase-by-phase development narrative
├── DESIGN.md                    # UI design system (Stitch format)
├── PRIVACY.md                   # Privacy policy
├── LICENSE                      # MIT (code) + EUR-Lex corpus notice
├── dataset_card.md              # HF Dataset card source
├── requirements.txt             # Install-time dependencies
└── requirements.lock.txt        # Exact locked versions (Python 3.10.14)
```

---

## 🔐 Configuration & Secrets

| Variable | Where | Purpose |
|---|---|---|
| `GROQ_API_KEY` | HF Space Secrets / shell env | Groq API authentication |
| `SPACE_ID` | Auto-set by HF | Disables cross-encoder to save RAM |
| `PORT` | Auto-set by HF | Server port for Gradio |

**Never commit API keys to the repository.**

---

## 🛡️ Safety & Limitations

- **Educational use only** — outputs are not legal advice and must not be relied upon for real legal decisions.
- **Partial corpus** — only EU PIL instruments (Rome I/II, Brussels Ia). National law, case law, GDPR, IP, family law, and criminal law are not covered.
- **Refusal guard** — queries outside the coverage scope will be refused rather than hallucinated.
- **LLM citations** — the model may occasionally cite `[N]` references inaccurately. Always verify against the "Evidence" panel.

Full details: [SYSTEM_CARD.md](SYSTEM_CARD.md) · [PRIVACY.md](PRIVACY.md)

---

## 📄 License

**Code**: [MIT License](LICENSE)  
**Dataset**: Text from EUR-Lex (public domain) · Metadata under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)  
**Model**: Groq `llama-3.1-8b-instant` — subject to [Meta Llama 3.1 Community License](https://www.llama.com/llama3_1/license/)

---

<div align="center">

Built with ❤️ as a capstone RAG engineering project  
*Not affiliated with the European Union or EUR-Lex*

</div>
