from retrieval import retrieve


if __name__ == "__main__":
    q = "Which law applies to a consumer contract with cross-border elements?"
    for r in retrieve(q, k=3):
        print(r["score"], r["citation"])
