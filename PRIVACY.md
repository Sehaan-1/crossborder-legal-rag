# Privacy Policy — Cross-Border Legal RAG

> **Short version**: We do not collect, store, or sell any personal data. Queries you submit are processed by a third-party LLM API (Groq) and then discarded.

---

## What data is processed?

When you submit a query to the Hugging Face Space:

1. **Your query text** is sent to the [Groq API](https://groq.com) for LLM inference.
2. **Retrieved legal passages** are assembled from the local FAISS index (no external call).
3. The generated memo is returned to your browser and **not stored anywhere** by this application.

## What data is NOT collected?

- No IP addresses are logged by this application.
- No query history is stored.
- No personal identifiers are collected.
- No cookies are set beyond those Hugging Face Spaces itself requires to serve the UI.

## Third-party processors

| Processor | Purpose | Privacy Policy |
|---|---|---|
| **Groq Inc.** | LLM inference for query answering | [groq.com/privacy-policy](https://groq.com/privacy-policy/) |
| **Hugging Face** | Hosting the Space and serving the UI | [huggingface.co/privacy](https://huggingface.co/privacy) |

Groq's API terms apply to all text you submit in the query field. Please review their policy before submitting sensitive information.

## What you should NOT enter

Do **not** enter any of the following into the query field:

- Real client names or personal identifiers
- Case numbers or confidential legal matter details
- Names of opposing parties or witnesses
- Any information protected by legal professional privilege or attorney–client confidentiality

## Logging on Hugging Face Spaces

Hugging Face may log HTTP requests at the infrastructure level as part of normal platform operations. This is outside our control. See the [Hugging Face Privacy Policy](https://huggingface.co/privacy) for details.

## How to request data deletion

Since no personal data is stored by this application, there is nothing to delete on our side. If you are concerned about Groq retaining your query, contact them directly at [privacy@groq.com](mailto:privacy@groq.com).

## Contact

For questions about this application's data practices, open an issue at:  
[github.com/Sehaan-1/crossborder-legal-rag/issues](https://github.com/Sehaan-1/crossborder-legal-rag/issues)

---

*Last updated: May 2025*
