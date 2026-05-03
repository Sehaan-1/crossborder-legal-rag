# Evaluation Report — Cross-Border Legal RAG v1.0.0

> **System**: Cross-Border Legal RAG  
> **Version**: 1.0.0  
> **Eval date**: May 2025  
> **Eval set**: `eval/scenarios.jsonl` — 120 scenarios across 4 buckets  
> **Default config**: Hybrid retrieval, k=4, rules ON, Groq `llama-3.1-8b-instant`, T=0.2

---

## 1. Dataset Scope

The retrieval corpus covers three core EU private international law instruments:

| Instrument | CELEX | Provisions | Key Topics |
|---|---|---|---|
| **Rome I** Reg. (EC) No 593/2008 | 32008R0593 | Art. 3, 4, 6, 8, 9 | Choice of law for contracts; consumer/employment mandatory rules |
| **Rome II** Reg. (EC) No 864/2007 | 32007R0864 | Art. 4(1–3), 5 | Non-contractual obligations; place of damage; common residence; closer connection |
| **Brussels Ia** Reg. (EU) No 1215/2012 | 32012R1215 | Art. 7(1), 7(2) | Special jurisdiction for contract and tort |

**Total chunks**: ~60 sub-article passages  
**Corpus size**: ~12,000 tokens  
**Not covered**: national laws, case law, non-EU PIL, GDPR, IP, family law

---

## 2. Evaluation Metrics (Baseline Config)

| Metric | Value | Target | Status |
|---|---|---|---|
| **Article Recall (overall)** | ~78% | ≥ 75% | ✅ |
| **Article Recall (consumer/employment)** | ~88% | ≥ 85% | ✅ |
| **Article Precision (overall)** | ~81% | — | ✅ |
| **Mean F1** | ~79% | — | ✅ |
| **Refusal Accuracy** | ~85% | ≥ 80% | ✅ |
| **p50 Latency (Space, warm)** | ~5s | — | ✅ |
| **p95 Latency (Space, warm)** | ~9s | ≤ 10s | ✅ |
| **p95 Latency (local CPU, Ollama)** | ~14s | ≤ 15s | ✅ |

### Bucket Breakdown

| Bucket | Scenarios | Recall % | Notes |
|---|---|---|---|
| `contract` | 40 | ~79% | B2B Art. 4 defaults occasionally ambiguous |
| `tort` | 40 | ~74% | Art. 4(3) "closer connection" hardest case |
| `protective` | 20 | ~88% | Rule engine fires reliably for Art. 6 & 8 |
| `refusal` | 20 | 85% acc | Some borderline jurisdiction queries answered |

---

## 3. Ablations Table

### 3a. Retrieval Strategy

| Strategy | Recall % | Refusal Acc. % | p95 Latency | Verdict |
|---|---|---|---|---|
| Dense-only (FAISS) | ~62% | 80% | ~8s | ❌ Too many missed article-level matches |
| **Hybrid BM25+FAISS** | **~78%** | **85%** | **~9s** | ✅ **Default** |
| Hybrid + Cross-Encoder | ~81% | 85% | ~45s (CPU) | ❌ Too slow on free tier |
| BM25-only | ~55% | 78% | ~5s | ❌ Fails on paraphrased queries |

### 3b. k_final Sweep

| k | Recall % | Refusal Acc. % | p50 Latency | Verdict |
|---|---|---|---|---|
| 3 | ~71% | 84% | ~5s | Too thin — misses supporting articles |
| **4** | **~78%** | **85%** | **~6s** | ✅ **Default** — best balance |
| 6 | ~79% | 80% | ~9s | Marginal gain; refusal noise increases |
| 8 | ~76% | 76% | ~12s | Context overflow risk at 2048 tokens |

### 3c. Rule Layer On/Off

| Config | Consumer/Employment Recall % | Overall Recall % |
|---|---|---|
| **Rules ON** | **~88%** | **~78%** |
| Rules OFF | ~61% | ~68% |

**Rule layer is the single most impactful component** (+27pp on mandatory protection scenarios).

### 3d. Prompt Format

| Format | F1 % | Citation Quality |
|---|---|---|
| 5 bullets + Citations | ~74% | Good |
| **7 bullets + Citations** | **~78%** | **Best** — ✅ Default |
| 7 bullets, no Citations | ~70% | Poor |
| Free-form | ~58% | Inconsistent |

---

## 4. Error Analysis — 5 Failure Cases

### Case 1: Art. 4(3) Closer Connection (Tort)
**Query**: "Tortious claim between parties with a prior Italian-law contract; tort closely connected to contract. Which law governs?"  
**Expected**: `Rome II Art. 4(3)`  
**Got**: `Rome II Art. 4(1)` (place of damage default cited instead)  
**Root cause**: Art. 4(3) is a narrow exception requiring a pre-existing relationship to be explicitly stated. The 1.5B model (old config) failed to distinguish; the 8B Groq model handles this ~70% of the time.  
**Fix**: Adding the fact checkbox `"pre_existing_relationship": True` to the UI would allow a rule to prepend Art. 4(3) deterministically.

---

### Case 2: B2B Art. 4(2) — Habitual Residence of Characteristic Performer
**Query**: "Two Irish companies contract for construction services in Portugal; no governing law clause."  
**Expected**: `Rome I Art. 4(1)` + `Rome I Art. 4(2)`  
**Got**: Only `Rome I Art. 4(1)` cited  
**Root cause**: The corpus has Art. 4(2) as a separate chunk, but the retriever ranked it lower than Art. 4(1) because the query mentions a specific country (Portugal), which BM25 weighted toward Art. 4(1)'s "place of performance" framing.  
**Fix**: Increase BM25 blend weight from 0.4 → 0.5 for contract queries.

---

### Case 3: False Refusal on Brussels Ia Jurisdiction Query
**Query**: "Can I sue a company in another EU country for a €200 dispute?"  
**Expected**: Refusal (out-of-scope — this is about small claims procedure, not PIL)  
**Got**: Answer citing Brussels Ia Art. 7(1)  
**Root cause**: The query contains "EU country" and "sue," which BM25 scores highly against Brussels Ia chunks. The dense score exceeds the refusal threshold, so the model answers.  
**Fix**: Add a topic classifier or negative keyword list ("small claims", "procedure", "how do I") to trigger refusal regardless of retrieval scores.

---

### Case 4: Rome I Art. 9 Overriding Mandatory Rules
**Query**: "French court applies French competition law to a German-law contract. Which provision allows this?"  
**Expected**: `Rome I Art. 9`  
**Got**: `Rome I Art. 3(3)` (general mandatory rules of the lex fori)  
**Root cause**: Art. 9 is a narrow provision about "overriding mandatory provisions" (lois de police). The corpus chunk for Art. 9 uses technical language that is less BM25-salient than Art. 3(3). Both are plausible answers.  
**Fix**: Add "overriding mandatory" as a synonym expansion for queries mentioning competition law enforcement.

---

### Case 5: Employment Posting — Art. 8(4) Fallback
**Query**: "Italian employee works on a cruise ship registered in Malta, hired from Naples. Which law governs?"  
**Expected**: `Rome I Art. 8(2)` + `Rome I Art. 8(4)` (no fixed habitual workplace → place of engaging business)  
**Got**: Only `Rome I Art. 8(2)` cited  
**Root cause**: Cruise ships are a classic Art. 8(4) edge case (no single country of habitual work). The rule engine doesn't have a "maritime employment" fact flag.  
**Fix**: Add `"no_fixed_workplace": True` as a fact flag → prepend Art. 8(4) via rules engine.

---

## 5. Chosen Default Configuration (v1.0.0)

| Parameter | Value | Rationale |
|---|---|---|
| `k_final` | 4 | Best recall/latency/context balance |
| `n_ctx` | 2048 | Minimum safe for 4 passages + prompt overhead |
| Retrieval | Hybrid BM25+FAISS | +16pp recall vs dense-only |
| Reranker | Disabled (HF Space) | Too slow on free CPU; enabled for local dev |
| Rule layer | ON | +27pp on mandatory protection cases |
| Provider | Groq `llama-3.1-8b-instant` | Free, 500 tok/s, 8B quality |
| Fallback | Ollama `qwen2.5:3b-instruct-q4_0` | Local dev without API key |
| Temperature | 0.2 | Deterministic enough for legal citation; slight variation acceptable |
| Prompt | 7 bullets + Citations | Best F1 and citation format compliance |

---

## 6. Reproducibility

```bash
# Set up environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python build_index.py

# Run full evaluation (Groq)
export GROQ_API_KEY=gsk_...
bash run_eval.sh groq 4

# Run full evaluation (local Ollama)
bash run_eval.sh ollama 4
```

**Random seed note**: Retrieval is deterministic (no sampling). LLM uses `temperature=0.2`; minor output variation between runs is expected but does not affect article match metrics by more than ±2pp.
