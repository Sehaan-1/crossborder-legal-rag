import json
from pathlib import Path

import faiss
import numpy as np

from embeddings import load_embedding_model


RAW = Path("data/raw/legal_core.jsonl")
INDEX_DIR = Path("index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)


def load_records(path):
    recs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                recs.append(json.loads(line))
    return recs


def l2_normalize(x):
    norms = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / norms


def main():
    records = load_records(RAW)
    for i, r in enumerate(records):
        r["id"] = i
        r["citation"] = f'{r["instrument"]}, {r["article"]}'
        r["chunk"] = f'{r["title"]}: {r["text"]}'

    model = load_embedding_model()
    texts = [r["chunk"] for r in records]
    emb = model.encode(
        texts,
        batch_size=32,
        convert_to_numpy=True,
        show_progress_bar=True,
    )
    emb = l2_normalize(emb).astype("float32")

    d = emb.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(emb)
    faiss.write_index(index, str(INDEX_DIR / "faiss.index"))

    with open(INDEX_DIR / "meta.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Built index with {len(records)} chunks, dim={d}")


if __name__ == "__main__":
    main()
