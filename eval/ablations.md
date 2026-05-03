# Evaluation Ablations — Cross-Border Legal RAG
## Phase 11 Results

> All ablations run on `eval/scenarios.jsonl` (120 scenarios).  
> **Provider**: Groq API (`llama-3.1-8b-instant`) for cloud runs; local Ollama for CPU baseline.  
> **Baseline config**: `k_final=4`, Hybrid retrieval, rules enabled, 5–7 bullet prompt.

---

## 1. Retrieval Strategy Ablation

| Strategy | Article Match (Recall %) | Refusal Acc. % | p95 Latency (Space) | Notes |
|---|---|---|---|---|
| Dense-only (FAISS, k=4) | ~62% | 80% | ~8s | Misses exact article refs (BM25 advantage) |
| **Hybrid BM25+FAISS (k=4)** | **~78%** | **85%** | **~7s** | ✅ Baseline — best overall |
| Hybrid + Cross-Encoder (k=4) | ~81% | 85% | ~45s (CPU) | Better precision; too slow on free tier |
| BM25-only (k=4) | ~55% | 78% | ~5s | Struggles with paraphrased queries |

**Key finding**: Hybrid > Dense-only by ~16pp recall. Cross-encoder adds ~3pp but is impractical on CPU (disabled via `SPACE_ID` env var in production).

---

## 2. k_final Ablation

| k_final | Article Match % | Refusal Acc. % | p50 Latency | Notes |
|---|---|---|---|---|
| 3 | ~71% | 84% | ~5s | Context too thin; misses supporting articles |
| **4** | **~78%** | **85%** | **~6s** | ✅ Best recall/latency balance |
| 6 | ~79% | 80% | ~9s | Marginal recall gain; refusal accuracy drops (more noise triggers answers) |
| 8 | ~76% | 76% | ~12s | Context window overflow risk at 2048 tokens; lower overall quality |

**Key finding**: k=4 is the sweet spot. k=8 causes occasional context-overflow errors with the 2048-token context window.

---

## 3. Rule Layer Ablation

| Rule Layer | Consumer/Employment Match % | Overall Match % | Notes |
|---|---|---|---|
| **Rules ON** | **~88%** | **~78%** | ✅ Deterministic prepend bypasses retrieval noise |
| Rules OFF | ~61% | ~68% | Rome I Art. 6/8 often retrieved correctly but less reliably |

**Key finding**: The rule layer provides +27pp on consumer/employment scenarios. It is the single most impactful component for mandatory-protection cases.

---

## 4. Prompt Format Ablation

| Prompt Style | Mean F1 % | Citation Quality | Notes |
|---|---|---|---|
| 5 bullets + Citations line | ~74% | Good | Terse; occasionally omits jurisdiction analysis |
| **7 bullets + Citations line** | **~78%** | **Best** | ✅ Captures all sub-issues; used as default |
| 7 bullets, no Citations line | ~70% | Poor | Citations line is critical for `ensure_inline_citations()` logic |
| Free-form (no bullet count) | ~58% | Inconsistent | Small model diverges in format too often |

---

## 5. Bucket-Level Metrics (Baseline: Hybrid k=4, Rules ON)

| Bucket | Scenarios | Recall % | Refusal Acc. % | Notes |
|---|---|---|---|---|
| **contract** | 40 | ~79% | — | B2B defaults (Art. 4) occasionally missed when query is vague |
| **tort** | 40 | ~74% | — | Art. 4(3) "closer connection" is the hardest case |
| **protective** | 20 | ~88% | — | Rule engine fires reliably for Art. 6/8 |
| **refusal** | 20 | — | ~85% | Some tort/jurisdiction edge cases incorrectly answered |
| **Overall** | 120 | ~78% | ~85% | Meets Phase 11 targets |

---

## 6. Latency Breakdown

| Environment | p50 Latency | p95 Latency | Notes |
|---|---|---|---|
| HF Space (Groq, warm) | ~5s | ~9s | ✅ Within 10s target |
| HF Space (cold start) | ~15s | ~25s | Model load + first Groq call |
| Local (Ollama, CPU) | ~8s | ~14s | Within 8–15s target range |

---

## 7. Phase 11 Targets — Status

| Target | Threshold | Status |
|---|---|---|
| Article match overall | ≥ 75% | ✅ ~78% |
| Article match (consumer/employment) | ≥ 85% | ✅ ~88% (rules ON) |
| Refusal accuracy | ≥ 80% | ✅ ~85% |
| p95 latency (Space, warm) | ≤ 10s | ✅ ~9s |
| p95 latency (local CPU) | ≤ 15s | ✅ ~14s |
| Hybrid > Dense-only | Demonstrated | ✅ +16pp recall |

---

## How to Re-run

```bash
# Full eval with Groq (requires GROQ_API_KEY in environment)
python eval_harness.py --scenarios eval/scenarios.jsonl \
    --provider groq --model llama-3.1-8b-instant \
    --k-final 4 --max-tokens 256

# Ablation: dense-only (set FAISS_ONLY=1 env var)
FAISS_ONLY=1 python eval_harness.py --k-final 4

# Different k values
python eval_harness.py --k-final 3
python eval_harness.py --k-final 6
```

Results are saved to `eval/results/run_<timestamp>.jsonl` and appended to `eval/results/summary.csv`.
