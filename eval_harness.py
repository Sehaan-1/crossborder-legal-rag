import json
import csv
from pathlib import Path
from rag_answer import answer_question

EVAL_FILE = Path("eval/scenarios.jsonl")
FAILURES_FILE = Path("eval/failures.csv")

def run_eval():
    scenarios = []
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        for line in f:
            scenarios.append(json.loads(line))
            
    total = len(scenarios)
    refuse_correct = 0
    refuse_total = 0
    article_hits = 0
    article_total = 0
    
    failures = []

    print(f"Running evaluation on {total} scenarios...")
    
    for i, s in enumerate(scenarios):
        query = s["query"]
        facts = s.get("facts", {})
        expect_refusal = s["expect_refusal"]
        expected_arts = s.get("expected_instruments_articles", [])
        
        # We know LLM takes time. For testing harness speed, if you want full, just wait.
        ans, r_p, rag_p = answer_question(query, facts=facts)
        
        is_refused = "I cannot determine" in ans or "out-of-scope" in ans
        
        failed = False
        reason = ""
        
        if expect_refusal:
            refuse_total += 1
            if is_refused:
                refuse_correct += 1
            else:
                failed = True
                reason = "Expected refusal, but got an answer."
        else:
            article_total += 1
            if is_refused:
                failed = True
                reason = "Expected answer, but got refusal."
            else:
                pass
                
        passages = []
        seen = set()
        for p in r_p + rag_p:
            if p["id"] not in seen:
                passages.append(p)
                seen.add(p["id"])
                
        if not expect_refusal and not is_refused:
            hit = False
            for p_idx, p in enumerate(passages, start=1):
                marker = f"[{p_idx}]"
                if marker in ans:
                    if any(exp in p["citation"] for exp in expected_arts) or any(exp.split(", ")[-1] in p["citation"] for exp in expected_arts):
                        hit = True
                        break
            if hit:
                article_hits += 1
            else:
                failed = True
                reason = "Answer did not cite the expected article."
                
        if failed:
            failures.append({
                "scenario_idx": i,
                "query": query,
                "expected": "Refusal" if expect_refusal else expected_arts,
                "reason": reason,
                "answer": ans
            })
            
        print(f"Processed {i+1}/{total}...", flush=True)

    print("\n=== METRICS TABLE ===", flush=True)
    refusal_acc = (refuse_correct / refuse_total * 100) if refuse_total else 0
    article_acc = (article_hits / article_total * 100) if article_total else 0
    print(f"Refusal Accuracy: {refusal_acc:.1f}% ({refuse_correct}/{refuse_total})")
    print(f"Article Match (Recall): {article_acc:.1f}% ({article_hits}/{article_total})")
    
    if failures:
        with open(FAILURES_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["scenario_idx", "query", "expected", "reason", "answer"])
            writer.writeheader()
            writer.writerows(failures)
        print(f"\nSaved {len(failures)} failures to {FAILURES_FILE}")
    else:
        print("\nNo failures! Perfect score.")

if __name__ == "__main__":
    run_eval()
