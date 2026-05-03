import re
import textwrap

import requests

from retrieval import retrieve, hybrid_retrieve, get_chunk_by_citation
from rules_evaluator import evaluate_rules


MODEL_NAME = "qwen2.5:3b-instruct-q4_0"
SYSTEM_PROMPT = """You are a cautious legal research assistant.
Use only the user's Sources.
Prefer specific rules over general fallback rules.
Do not cite a source number unless that exact source supports the sentence.
Every substantive sentence must include an inline citation like [1].
If facts are missing, state the uncertainty instead of inventing facts.
Educational use only. Not legal advice."""


def build_prompt(question, passages):
    sources = []
    for i, p in enumerate(passages, start=1):
        sources.append(f"[{i}] {p['citation']}\n{p['text']}")
    sources_text = "\n\n".join(sources)
    prompt = f"""
Question: {question}

Sources:
{sources_text}

Using ONLY the sources above, answer in 5-7 short bullet points.
You MUST use these sources — they are directly relevant.
Each bullet must end with an inline citation like [1].
Final bullet must be: - Citations: [1] Instrument, Article; [2] ...
Do not say you cannot determine the answer.
"""
    return textwrap.dedent(prompt).strip()


def generate_llm(prompt, temperature=0.2):
    try:
        from llama_cpp import Llama
        import multiprocessing
        import os
        
        # Singleton Llama instance
        global _LLAMA_INST
        if "_LLAMA_INST" not in globals():
            model_path = "models/qwen2.5-1.5b-instruct-q3_k_m.gguf"
            if os.path.exists(model_path):
                _LLAMA_INST = Llama(
                    model_path=model_path,
                    n_ctx=2048,
                    n_threads=multiprocessing.cpu_count(),
                    n_batch=512,
                    verbose=False
                )
            else:
                _LLAMA_INST = None
                
        if _LLAMA_INST:
            output = _LLAMA_INST.create_chat_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=256
            )
            return output["choices"][0]["message"]["content"]
    except ImportError:
        pass
        
    # Fallback to Ollama if llama-cpp is not installed or model missing
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": temperature},
    }
    try:
        r = requests.post(url, json=payload, timeout=600)
        r.raise_for_status()
        return r.json()["message"]["content"]
    except requests.exceptions.ConnectionError:
        return "[Error] Could not connect to Ollama. Please ensure Ollama is running on port 11434, or llama-cpp-python is installed."
    except requests.exceptions.Timeout:
        return "[Error] Request timed out. The model may be overloaded."
    except Exception as e:
        return f"[Error] Unexpected error: {e}"


def ensure_inline_citations(answer, default="[1]"):
    refusal_phrases = [
        "I cannot determine from the provided sources",
        "cannot determine",
        "[Error]"
    ]
    # Don't modify refusal or error responses
    if any(p in answer for p in refusal_phrases):
        return answer

    lines = []
    for line in answer.splitlines():
        stripped = line.strip()
        is_content_line = stripped and not stripped.endswith(":")
        if is_content_line and not re.search(r"\[\d+\]", stripped):
            line = line.rstrip() + f" {default}"
        lines.append(line)
    return "\n".join(lines)


def answer_question(question, k=4, facts=None):
    rule_passages = []
    if facts:
        proposed_articles = evaluate_rules(facts)
        for article_ref in proposed_articles:
            chunk = get_chunk_by_citation(article_ref["instrument"], article_ref["article"])
            if chunk:
                rule_passages.append(chunk)

    rag_passages = hybrid_retrieve(question, k_final=k)
    
    # Deduplicate and combine
    passages = []
    seen_ids = set()
    for p in rule_passages + rag_passages:
        if p["id"] not in seen_ids:
            passages.append(p)
            seen_ids.add(p["id"])
    
    if not passages:
        stats = {"best_dense": 0, "best_bm25": 0, "blended_top1": 0}
        return "I cannot determine from the provided sources. Please provide more facts or context.", rule_passages, rag_passages, stats
        
    best_dense = max((p.get("raw_dense", 0) for p in rag_passages), default=0)
    best_bm25 = max((p.get("unnormalized_bm25", 0) for p in rag_passages), default=0)
    blended_top1 = passages[0].get("score", 0) if passages else 0
    stats = {"best_dense": best_dense, "best_bm25": best_bm25, "blended_top1": blended_top1}
        
    # Refusal threshold (bypass if rule matched)
    if not rule_passages:
        if best_dense < 0.65 and best_bm25 < 4.0:
            return "I cannot determine from the provided sources. The query appears to be out-of-scope. Please provide more facts or relevant sources.", rule_passages, rag_passages, stats
        
    prompt = build_prompt(question, passages[:k]) # Keep max k
    return ensure_inline_citations(generate_llm(prompt)), rule_passages, rag_passages, stats


if __name__ == "__main__":
    question = (
        "A French consumer buys online from a German trader targeting France. "
        "There is no choice-of-law clause. Which law governs the contract?"
    )
    facts = {"consumer": True, "trader_targets_consumer_country": True, "no_choice_of_law": True}
    print("Educational use only - Not legal advice.\n")
    print(f"Question: {question}")
    answer, r_p, rag_p, stats = answer_question(question, facts=facts)
    print("Answer:\n", answer)
    print("Stats:", stats)
