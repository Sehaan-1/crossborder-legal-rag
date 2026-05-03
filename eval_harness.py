#!/usr/bin/env python3
"""
Phase 11 — Expanded evaluation harness for Cross-Border Legal RAG.

Usage:
  python eval_harness.py
  python eval_harness.py --scenarios eval/scenarios.jsonl --provider groq \
      --model llama-3.1-8b-instant --k-final 4 --max-tokens 256 \
      --out eval/results/run_$(date +%Y%m%d).jsonl
"""

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path


# ── Citation normalisation ────────────────────────────────────────────────────

_INST_ALIASES = {
    "rome i": "rome i",
    "rome 1": "rome i",
    "593/2008": "rome i",
    "32008r0593": "rome i",
    "rome ii": "rome ii",
    "rome 2": "rome ii",
    "864/2007": "rome ii",
    "32007r0864": "rome ii",
    "brussels ia": "brussels ia",
    "brussels i": "brussels ia",
    "1215/2012": "brussels ia",
    "32012r1215": "brussels ia",
}


def normalise_citation(raw: str) -> tuple[str, str] | None:
    """
    Turn any citation string into (instrument_key, article_key).
    Examples:
      "Rome I (Regulation (EC) No 593/2008), Art. 6(1)"  → ("rome i", "6(1)")
      "Rome I Art. 6"                                     → ("rome i", "6")
      "Rome II, Art. 4(1)"                                → ("rome ii", "4(1)")
    Returns None if unparseable.
    """
    raw_low = raw.lower()

    # identify instrument
    inst_key = None
    for alias, canonical in _INST_ALIASES.items():
        if alias in raw_low:
            inst_key = canonical
            break
    if inst_key is None:
        return None

    # extract article number (e.g. "6(1)", "4(2)", "7")
    art_match = re.search(r"art(?:icle)?\.?\s*(\d+(?:\(\w+\))?)", raw_low)
    if not art_match:
        return None

    return (inst_key, art_match.group(1))


def normalise_set(citations: list[str]) -> set[tuple[str, str]]:
    result = set()
    for c in citations:
        norm = normalise_citation(c)
        if norm:
            result.add(norm)
    return result


def extract_cited_from_answer(answer: str, passages: list[dict]) -> set[tuple[str, str]]:
    """
    Parse [N] markers in the answer and map them back to passage citations.
    Returns the normalised set of what the answer actually cited.
    """
    cited = set()
    referenced_indices = {int(m) for m in re.findall(r"\[(\d+)\]", answer)}
    for idx in referenced_indices:
        if 1 <= idx <= len(passages):
            norm = normalise_citation(passages[idx - 1].get("citation", ""))
            if norm:
                cited.add(norm)
    return cited


# ── Metrics ───────────────────────────────────────────────────────────────────

def precision_recall(predicted: set, expected: set) -> tuple[float, float, float]:
    if not predicted and not expected:
        return 1.0, 1.0, 1.0
    if not predicted or not expected:
        return 0.0, 0.0, 0.0
    tp = len(predicted & expected)
    p = tp / len(predicted)
    r = tp / len(expected)
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f1


# ── Main eval loop ────────────────────────────────────────────────────────────

def run_eval(
    scenarios_path: Path,
    out_path: Path | None,
    k_final: int = 4,
    max_tokens: int = 256,
    provider: str = "auto",
    model: str | None = None,
) -> dict:
    # Patch environment overrides before importing rag_answer
    if provider == "groq" and not os.environ.get("GROQ_API_KEY"):
        print("[WARN] --provider=groq but GROQ_API_KEY not set. Will fall back to Ollama.")
    if model:
        os.environ["_EVAL_MODEL_OVERRIDE"] = model

    from rag_answer import answer_question  # import after env patch

    scenarios = []
    with open(scenarios_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                scenarios.append(json.loads(line))

    total = len(scenarios)
    print(f"\n▶  Running Phase 11 eval on {total} scenarios  (k={k_final})\n")

    # Accumulators
    refuse_correct = refuse_total = 0
    all_precisions, all_recalls, all_f1s = [], [], []
    latencies: list[float] = []
    results: list[dict] = []
    failures: list[dict] = []

    # bucket tracking
    buckets: dict[str, dict] = {
        "contract":   {"hits": 0, "total": 0},
        "tort":       {"hits": 0, "total": 0},
        "protective": {"hits": 0, "total": 0},
        "refusal":    {"correct": 0, "total": 0},
    }

    for i, s in enumerate(scenarios):
        query          = s["query"]
        facts          = s.get("facts", {})
        expect_refusal = s.get("expect_refusal", False)
        expected_arts  = s.get("expected_articles", s.get("expected_instruments_articles", []))
        bucket         = s.get("bucket", "contract")

        t0 = time.perf_counter()
        try:
            ans, r_p, rag_p, stats = answer_question(query, k=k_final, facts=facts)
        except Exception as e:
            ans = f"[Error] {e}"
            r_p, rag_p, stats = [], [], {}
        latency = time.perf_counter() - t0
        latencies.append(latency)

        # Deduplicated passage list (same order as answer numbering)
        passages: list[dict] = []
        seen: set[str] = set()
        for p in r_p + rag_p:
            if p["id"] not in seen:
                passages.append(p)
                seen.add(p["id"])

        is_refused = any(phrase in ans for phrase in [
            "I cannot determine", "out-of-scope", "[Error]"
        ])

        result_record = {
            "scenario_idx": i,
            "bucket": bucket,
            "query": query,
            "expect_refusal": expect_refusal,
            "expected_articles": expected_arts,
            "answer": ans,
            "is_refused": is_refused,
            "latency_s": round(latency, 3),
            "stats": stats,
            "precision": None,
            "recall": None,
            "f1": None,
        }

        failed = False
        failure_reason = ""

        # ── Refusal check ────────────────────────────────────────────────
        if expect_refusal:
            refuse_total += 1
            buckets["refusal"]["total"] += 1
            if is_refused:
                refuse_correct += 1
                buckets["refusal"]["correct"] += 1
            else:
                failed = True
                failure_reason = "Expected refusal but got an answer."

        # ── Article precision / recall ───────────────────────────────────
        else:
            b = bucket if bucket in buckets else "contract"
            buckets[b]["total"] += 1

            if is_refused:
                failed = True
                failure_reason = "Expected answer but got refusal."
                p_score, r_score, f1_score = 0.0, 0.0, 0.0
            else:
                predicted_norm = extract_cited_from_answer(ans, passages)
                expected_norm  = normalise_set(expected_arts)
                p_score, r_score, f1_score = precision_recall(predicted_norm, expected_norm)
                if r_score > 0:
                    buckets[b]["hits"] += 1
                if r_score == 0 and expected_arts:
                    failed = True
                    failure_reason = f"Recall=0 — expected {expected_arts}"

            all_precisions.append(p_score)
            all_recalls.append(r_score)
            all_f1s.append(f1_score)
            result_record.update({
                "precision": round(p_score, 3),
                "recall": round(r_score, 3),
                "f1": round(f1_score, 3),
            })

        results.append(result_record)

        if failed:
            failures.append({
                "scenario_idx": i,
                "bucket": bucket,
                "query": query,
                "expected": "Refusal" if expect_refusal else expected_arts,
                "reason": failure_reason,
                "answer": ans[:300],
            })

        tag = "✓" if not failed else "✗"
        print(
            f"  [{i+1:3}/{total}] {tag}  bucket={bucket:<10}  "
            f"lat={latency:.1f}s  "
            + (f"p={p_score:.2f} r={r_score:.2f}" if not expect_refusal else "refusal"),
            flush=True,
        )

    # ── Summary ────────────────────────────────────────────────────────────────
    refusal_acc    = (refuse_correct / refuse_total * 100) if refuse_total else 0.0
    mean_precision = (sum(all_precisions) / len(all_precisions) * 100) if all_precisions else 0.0
    mean_recall    = (sum(all_recalls) / len(all_recalls) * 100) if all_recalls else 0.0
    mean_f1        = (sum(all_f1s) / len(all_f1s) * 100) if all_f1s else 0.0
    p50 = sorted(latencies)[len(latencies) // 2] if latencies else 0
    p95 = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0

    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "scenarios": total,
        "k_final": k_final,
        "provider": provider,
        "refusal_accuracy_pct": round(refusal_acc, 1),
        "mean_precision_pct":   round(mean_precision, 1),
        "mean_recall_pct":      round(mean_recall, 1),
        "mean_f1_pct":          round(mean_f1, 1),
        "p50_latency_s":        round(p50, 2),
        "p95_latency_s":        round(p95, 2),
        "failures":             len(failures),
        "bucket_stats": {
            b: {
                "recall_pct": round(v.get("hits", v.get("correct", 0)) /
                                    v["total"] * 100, 1) if v["total"] else 0
            }
            for b, v in buckets.items()
        },
    }

    print("\n" + "="*60)
    print("  PHASE 11 EVALUATION SUMMARY")
    print("="*60)
    print(f"  Scenarios         : {total}")
    print(f"  Refusal Accuracy  : {refusal_acc:.1f}%  ({refuse_correct}/{refuse_total})")
    print(f"  Mean Precision    : {mean_precision:.1f}%")
    print(f"  Mean Recall       : {mean_recall:.1f}%")
    print(f"  Mean F1           : {mean_f1:.1f}%")
    print(f"  p50 Latency       : {p50:.2f}s")
    print(f"  p95 Latency       : {p95:.2f}s")
    print(f"  Failures          : {len(failures)}")
    print("\n  Bucket breakdown:")
    for b, v in buckets.items():
        hits = v.get("hits", v.get("correct", 0))
        pct  = hits / v["total"] * 100 if v["total"] else 0
        print(f"    {b:<12} : {pct:.1f}%  ({hits}/{v['total']})")
    print("="*60)

    # ── Persist results ────────────────────────────────────────────────────────
    if out_path is None:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_path = Path(f"eval/results/run_{ts}.jsonl")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"__summary__": True, **summary}) + "\n")
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"\n  Run saved → {out_path}")

    # Failures CSV
    if failures:
        fail_path = Path("eval/failures.csv")
        with open(fail_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(failures[0].keys()))
            writer.writeheader()
            writer.writerows(failures)
        print(f"  Failures CSV → {fail_path}")

    # Summary CSV (append row)
    summary_csv = Path("eval/results/summary.csv")
    write_header = not summary_csv.exists()
    with open(summary_csv, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "scenarios", "k_final", "provider",
            "refusal_accuracy_pct", "mean_precision_pct",
            "mean_recall_pct", "mean_f1_pct",
            "p50_latency_s", "p95_latency_s", "failures",
        ])
        if write_header:
            writer.writeheader()
        writer.writerow({k: v for k, v in summary.items() if k != "bucket_stats"})
    print(f"  Summary CSV  → {summary_csv}")

    return summary


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Phase 11 evaluation harness for Cross-Border Legal RAG"
    )
    parser.add_argument(
        "--scenarios", type=Path,
        default=Path("eval/scenarios.jsonl"),
        help="Path to scenarios JSONL file",
    )
    parser.add_argument(
        "--provider", choices=["auto", "groq", "ollama"],
        default="auto",
        help="LLM provider (auto = use GROQ_API_KEY if set, else Ollama)",
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help="Override the model name (e.g. llama-3.1-8b-instant)",
    )
    parser.add_argument(
        "--k-final", type=int, default=4,
        help="Number of passages to retrieve (default: 4)",
    )
    parser.add_argument(
        "--max-tokens", type=int, default=256,
        help="Max tokens for LLM generation",
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="Output JSONL path (default: eval/results/run_<timestamp>.jsonl)",
    )
    args = parser.parse_args()

    run_eval(
        scenarios_path=args.scenarios,
        out_path=args.out,
        k_final=args.k_final,
        max_tokens=args.max_tokens,
        provider=args.provider,
        model=args.model,
    )


if __name__ == "__main__":
    main()
