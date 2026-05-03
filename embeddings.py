from sentence_transformers import SentenceTransformer


EMBED_MODEL = "BAAI/bge-small-en-v1.5"


def load_embedding_model():
    try:
        return SentenceTransformer(EMBED_MODEL, local_files_only=True)
    except Exception:
        return SentenceTransformer(EMBED_MODEL)
