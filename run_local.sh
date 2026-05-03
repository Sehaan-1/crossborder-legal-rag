#!/usr/bin/env bash
# run_local.sh — Start the Cross-Border Legal RAG app locally
# Usage: bash run_local.sh [--groq | --ollama]
# Requires: Python 3.10+, virtual environment at .venv/, FAISS index built

set -euo pipefail

PROVIDER="${1:---ollama}"

echo "=============================================="
echo " Cross-Border Legal RAG — Local Startup"
echo "=============================================="

# 1. Activate venv
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate   # Windows Git Bash
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate       # Linux / macOS
else
    echo "[ERROR] Virtual environment not found. Run: python -m venv .venv && pip install -r requirements.txt"
    exit 1
fi

# 2. Build FAISS index if missing
if [ ! -f "index/faiss.index" ]; then
    echo "[INFO] Building FAISS index..."
    python build_index.py
else
    echo "[OK] FAISS index found."
fi

# 3. Provider configuration
if [ "$PROVIDER" = "--groq" ]; then
    if [ -z "${GROQ_API_KEY:-}" ]; then
        echo "[ERROR] --groq selected but GROQ_API_KEY is not set."
        echo "        Export it first: export GROQ_API_KEY=gsk_..."
        exit 1
    fi
    echo "[INFO] Using Groq API (llama-3.1-8b-instant)"
else
    echo "[INFO] Using local Ollama (qwen2.5:3b-instruct-q4_0)"
    echo "       Ensure Ollama is running: ollama serve"
    echo "       And the model is pulled:  ollama pull qwen2.5:3b-instruct-q4_0"
fi

echo ""
echo "[INFO] Starting Gradio UI..."
echo "       Open http://localhost:7860 in your browser."
echo ""

# 4. Launch app (temperature fixed at 0.2; no randomness in retrieval)
python app.py
