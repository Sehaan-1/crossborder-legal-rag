import json
import math
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

from embeddings import load_embedding_model


INDEX_DIR = Path("index")


def load_meta():
    recs = []
    with open(INDEX_DIR / "meta.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            recs.append(json.loads(line))
    return recs


def l2_normalize(x):
    norms = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / norms


def _adjust_score(query, record, score):
    q = query.lower()
    title = record["title"].lower()
    citation = record["citation"].lower()

    asks_jurisdiction = any(
        term in q for term in ("jurisdiction", "court", "courts", "sued", "sue", "forum")
    )
    asks_applicable_law = any(
        term in q
        for term in ("which law", "law applies", "applicable law", "governing law", "governs")
    )

    if asks_jurisdiction:
        if "brussels ia" in citation or "jurisdiction" in title:
            score += 0.12
        if "rome i" in citation or "rome ii" in citation:
            score -= 0.05
    elif asks_applicable_law:
        if "rome i" in citation or "rome ii" in citation:
            score += 0.08
        if "jurisdiction" in title:
            score -= 0.12

    return score


def retrieve(query, k=5):
    index = faiss.read_index(str(INDEX_DIR / "faiss.index"))
    meta = load_meta()
    model = load_embedding_model()
    q = model.encode([query], convert_to_numpy=True)
    q = l2_normalize(q.astype("float32"))

    search_k = min(len(meta), max(k, min(6, len(meta))))
    scores, idxs = index.search(q, search_k)

    results = []
    for score, idx in zip(scores[0], idxs[0]):
        r = meta[idx]
        raw_score = float(score)
        results.append(
            {
                "score": _adjust_score(query, r, raw_score),
                "raw_score": raw_score,
                "id": r["id"],
                "citation": r["citation"],
                "text": r["chunk"],
            }
        )

    return sorted(results, key=lambda item: item["score"], reverse=True)[:k]


_META_CACHE = None
_FAISS_INDEX_CACHE = None
_MODEL_CACHE = None
_BM25_INDEX = None
_CROSS_ENCODER = None

def _initialize_indices():
    global _META_CACHE, _FAISS_INDEX_CACHE, _MODEL_CACHE, _BM25_INDEX, _CROSS_ENCODER
    if _META_CACHE is None:
        _META_CACHE = load_meta()
    if _FAISS_INDEX_CACHE is None:
        _FAISS_INDEX_CACHE = faiss.read_index(str(INDEX_DIR / "faiss.index"))
    if _MODEL_CACHE is None:
        _MODEL_CACHE = load_embedding_model()
    if _BM25_INDEX is None:
        tokenized_corpus = []
        for r in _META_CACHE:
            content = (r["title"] + " " + r["text"]).lower()
            tokenized_corpus.append(content.split())
        _BM25_INDEX = BM25Okapi(tokenized_corpus)
    if _CROSS_ENCODER is None:
        _CROSS_ENCODER = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device="cpu")

def hybrid_retrieve(query, k_final=8):
    _initialize_indices()
    
    # Synonym expansion
    synonyms_path = Path("synonyms.json")
    expanded_query = query
    if synonyms_path.exists():
        with open(synonyms_path, "r", encoding="utf-8") as f:
            syns = json.load(f)
            extra_tokens = []
            q_lower = query.lower()
            for k, v_list in syns.items():
                if k.lower() in q_lower:
                    for v in v_list:
                        extra_tokens.extend(v.lower().split())
            if extra_tokens:
                # Deduplicate tokens
                unique_extras = list(set(extra_tokens))
                expanded_query = query + " " + " ".join(unique_extras)
    
    tokenized_query = expanded_query.lower().split()
    bm25_scores = _BM25_INDEX.get_scores(tokenized_query)
    
    top_bm25_k = min(150, len(_META_CACHE))
    top_bm25_idx = np.argsort(bm25_scores)[::-1][:top_bm25_k]
    
    if np.max(bm25_scores) > 0:
        bm25_norm = bm25_scores / np.max(bm25_scores)
    else:
        bm25_norm = bm25_scores
        
    q_emb = _MODEL_CACHE.encode([expanded_query], convert_to_numpy=True)
    q_emb = l2_normalize(q_emb.astype("float32"))
    top_dense_k = min(40, len(_META_CACHE))
    dense_scores, dense_idxs = _FAISS_INDEX_CACHE.search(q_emb, top_dense_k)
    
    combined_scores = {}
    
    for idx in top_bm25_idx:
        combined_scores[idx] = {"bm25": bm25_norm[idx], "dense": 0.0}
        
    for i, idx in enumerate(dense_idxs[0]):
        if idx not in combined_scores:
            combined_scores[idx] = {"bm25": bm25_norm[idx], "dense": 0.0}
        combined_scores[idx]["dense"] = float(dense_scores[0][i])
        
    results = []
    for idx, scores in combined_scores.items():
        r = _META_CACHE[idx]
        blend_score = 0.6 * scores["dense"] + 0.4 * scores["bm25"]
        results.append({
            "score": blend_score,
            "raw_dense": scores["dense"],
            "raw_bm25": scores["bm25"],
            "unnormalized_bm25": bm25_scores[idx],
            "id": r["id"],
            "citation": r["citation"],
            "text": r["chunk"]
        })
        
    # Re-rank top 30 with CrossEncoder
    top_hybrid = sorted(results, key=lambda item: item["score"], reverse=True)[:30]
    if not top_hybrid:
        return []
        
    # De-duplicate near-identical passages (cosine sim > 0.95)
    texts = [p["text"] for p in top_hybrid]
    embs = _MODEL_CACHE.encode(texts, convert_to_numpy=True)
    embs = l2_normalize(embs.astype("float32"))
    
    deduped = []
    deduped_embs = []
    for i, p in enumerate(top_hybrid):
        emb = embs[i]
        is_dup = False
        for kept_emb in deduped_embs:
            sim = np.dot(emb, kept_emb)
            if sim > 0.95:
                is_dup = True
                break
        if not is_dup:
            deduped.append(p)
            deduped_embs.append(emb)
            
    top_hybrid = deduped
        
    cross_inp = [[query, p["text"]] for p in top_hybrid]
    ce_scores = _CROSS_ENCODER.predict(cross_inp)
    
    # Sigmoid-normalize logits → [0, 1] for consistent display
    for i, p in enumerate(top_hybrid):
        logit = float(ce_scores[i])
        p["score"] = 1.0 / (1.0 + math.exp(-logit))
        
    return sorted(top_hybrid, key=lambda item: item["score"], reverse=True)[:k_final]

def get_chunk_by_citation(instrument, article):
    _initialize_indices()
    for r in _META_CACHE:
        # fuzzy match on instrument and article just in case
        if r["instrument"] == instrument and r["article"] == article:
            return {
                "score": 1.0, # Rule matches have high synthetic score
                "id": r["id"],
                "citation": r["citation"],
                "text": r["chunk"]
            }
    return None
