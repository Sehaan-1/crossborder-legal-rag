# System Card — Cross-Border Legal RAG

> **Educational use only — Not legal advice.**  
> This system is a research prototype demonstrating Retrieval-Augmented Generation on EU statutory text. It must not be used as a substitute for qualified legal counsel.

---

## 1. Architecture

```
User Query
    │
    ▼
┌──────────────────────────────┐
│  Synonym / Abbreviation      │  synonyms.json  (B2C → business-to-consumer, etc.)
│  Expansion                   │
└──────────────────────────────┘
    │ expanded query
    ▼
┌──────────────────────────────┐   ┌──────────────────────┐
│  Deterministic Rule Engine   │──►│  rules/rome_rules.csv │
│  (rules_evaluator.py)        │   └──────────────────────┘
│  Fires on boolean facts:     │
│  consumer, tort, employment, │──► prepends mandatory article chunks
│  contract, no_choice_of_law  │
└──────────────────────────────┘
    │ rule passages (may be empty)
    ▼
┌──────────────────────────────────────────────────────────────┐
│  Hybrid Retrieval  (retrieval.py → hybrid_retrieve())         │
│                                                              │
│  BM25 top-150  ──┐                                           │
│                  ├─► Reciprocal Rank Fusion → top-20        │
│  FAISS top-40  ──┘   (blended score = 0.6·dense + 0.4·BM25) │
└──────────────────────────────────────────────────────────────┘
    │ top-20 candidates
    ▼
┌──────────────────────────────┐
│  Cosine Similarity Dedup     │  threshold: similarity > 0.95 → drop
│  (sentence-transformers)     │
└──────────────────────────────┘
    │ deduplicated candidates
    ▼
┌──────────────────────────────┐
│  Cross-Encoder Reranker      │  ms-marco-MiniLM-L-6-v2
│  (disabled on HF Spaces      │  (saves RAM on free CPU tier)
│   via SPACE_ID env var)      │
└──────────────────────────────┘
    │ top-k reranked passages (k=4)
    ▼
┌──────────────────────────────┐
│  Confidence & Refusal        │
│  best_dense < 0.65 AND       │──► "I cannot determine from the provided sources."
│  best_bm25  < 4.0            │    (only if no rule fired)
│  (bypassed if rule matched)  │
└──────────────────────────────┘
    │ approved passages + rule passages
    ▼
┌──────────────────────────────┐
│  LLM Generation              │
│  Provider: Groq API          │  llama-3.1-8b-instant (~500 tok/s)
│  Fallback: Ollama (local)    │  qwen2.5:3b-instruct-q4_0
└──────────────────────────────┘
    │ raw LLM output
    ▼
┌──────────────────────────────┐
│  ensure_inline_citations()   │  appends [1] to any bullet lacking a citation
└──────────────────────────────┘
    │
    ▼
  Structured Legal Memo (5–7 bullets + Citations line)
```

---

## 2. Prompt Format

**System message** (constant):
```
You are a cautious legal research assistant.
Use only the user's Sources.
Prefer specific rules over general fallback rules.
Do not cite a source number unless that exact source supports the sentence.
Every substantive sentence must include an inline citation like [1].
If facts are missing, state the uncertainty instead of inventing facts.
Educational use only. Not legal advice.
```

**User message** (constructed per query):
```
Question: {user_query}

Sources:
[1] {citation_1}
{text_1}

[2] {citation_2}
{text_2}
...

Using ONLY the sources above, answer in 5-7 short bullet points.
You MUST use these sources — they are directly relevant.
Each bullet must end with an inline citation like [1].
Final bullet must be: - Citations: [1] Instrument, Article; [2] ...
Do not say you cannot determine the answer.
```

**Expected output format:**
```
- [Governing law determination] [1]
- [Key mandatory provision] [2]
- [Consumer/employment/tort exception, if applicable] [1]
- [Jurisdiction rule] [3]
- [Practical consequence or caveat] [2]
- Citations: [1] Rome I, Art. 6(1); [2] Rome I, Art. 4; [3] Brussels Ia, Art. 7(1)
```

---

## 3. Refusal Thresholds

The system **refuses to generate** a memo when retrieval confidence is too low AND no deterministic rule matched:

| Metric | Threshold | Description |
|---|---|---|
| `best_dense` | `< 0.65` | Cosine similarity of top FAISS result |
| `best_bm25` | `< 4.0` | Raw BM25 score of top BM25 result |
| Rule matched? | Any rule fired | **Overrides** both thresholds — always answers if a rule hit |

**Refusal message:** `"I cannot determine from the provided sources. The query appears to be out-of-scope."`

---

## 4. Confidence Heuristic (UI Badge)

| Badge | Condition |
|---|---|
| 🟢 **High** | `best_dense ≥ 0.70` AND `sources_cited ≥ 3` |
| 🟡 **Medium** | `best_dense ≥ 0.60` AND `sources_cited ≥ 1` |
| 🔴 **Low** | All other cases |

`sources_cited` = count of unique `[N]` citation tokens in the generated memo.

---

## 5. LLM Provider Configuration

| Environment | Provider | Model | Speed |
|---|---|---|---|
| HF Spaces (production) | **Groq API** | `llama-3.1-8b-instant` | ~5s |
| Local (dev) | **Ollama** | `qwen2.5:3b-instruct-q4_0` | ~10s |

**Priority logic in `generate_llm()`:**
1. If `GROQ_API_KEY` env var is set → use Groq (cloud).
2. Otherwise → fall back to Ollama on `localhost:11434`.

**API key**: Stored as a Hugging Face Space secret (`GROQ_API_KEY`). Never committed to version control.

---

## 6. Retrieval Corpus

| Instrument | CELEX | Sub-articles |
|---|---|---|
| Rome I (Reg. (EC) No 593/2008) | 32008R0593 | Art. 4, 6, 8 |
| Rome II (Reg. (EC) No 864/2007) | 32007R0864 | Art. 4 |
| Brussels Ia (Reg. (EU) No 1215/2012) | 32012R1215 | Art. 7(1), 7(2) |

Corpus is publicly available as a Hugging Face Dataset: [`SehaanCuda/crossborder_legal_core`](https://huggingface.co/datasets/SehaanCuda/crossborder_legal_core).

---

## 7. Known Limitations & Failure Modes

| Limitation | Impact | Mitigation |
|---|---|---|
| Partial corpus coverage (3 instruments, ~15 articles) | Queries about national law or non-EU PIL will be refused | Refusal threshold + out-of-scope message |
| Cross-encoder disabled in HF Spaces (saves RAM) | Ranking quality slightly lower than local | Hybrid blended score still provides good ordering |
| LLM may hallucinate citation numbers | Memo could cite `[5]` when only 4 sources exist | `ensure_inline_citations()` post-processes; users should verify |
| Groq free tier rate limits (6,000 tok/min) | Queuing under heavy load | Graceful error message returned |
| No case law | Statute-only answers; factual nuance from precedent missing | Documented in disclaimer |
| Static index | New regulations/amendments not reflected | Rebuild index with `build_index.py` after corpus update |

---

## 8. Privacy

- **No personal data is collected or logged** by this application.
- Queries are forwarded to the Groq API; see [Groq's privacy policy](https://groq.com/privacy-policy/) for their data handling.
- Do not enter real client names, case numbers, or identifying information into the query field.

---

## 9. Intended Use vs. Misuse

| ✅ Intended Use | ❌ Out of Scope |
|---|---|
| Learning EU PIL concepts | Obtaining legal advice for a real case |
| RAG benchmarking experiments | Replacing a qualified lawyer |
| Demonstrating hybrid retrieval techniques | Jurisdictions outside EU PIL |
| Exploring AI-assisted legal research | Generating documents for court submission |
