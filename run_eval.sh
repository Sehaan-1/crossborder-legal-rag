#!/usr/bin/env bash
# run_eval.sh — Run the Phase 11 evaluation harness and print the metrics table
# Usage: bash run_eval.sh [--provider groq|ollama] [--k-final N]
# Requires: Python 3.10+, virtual environment, FAISS index built, GROQ_API_KEY if using groq

set -euo pipefail

PROVIDER="${1:---provider ollama}"
K_FINAL="${2:-4}"

echo "=============================================="
echo " Cross-Border Legal RAG — Evaluation Runner"
echo "=============================================="
echo " Scenarios : eval/scenarios.jsonl (120)"
echo " Provider  : ${PROVIDER}"
echo " k_final   : ${K_FINAL}"
echo " LLM temp  : 0.2 (fixed — no random seed needed)"
echo "=============================================="
echo ""

# Activate venv
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "[ERROR] Virtual environment not found."
    exit 1
fi

# Ensure FAISS index exists
if [ ! -f "index/faiss.index" ]; then
    echo "[INFO] Building FAISS index first..."
    python build_index.py
fi

# Determine timestamp for output file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUT="eval/results/run_${TIMESTAMP}.jsonl"

# Run the harness
python eval_harness.py \
    --scenarios eval/scenarios.jsonl \
    --provider "${PROVIDER#--provider }" \
    --k-final "${K_FINAL}" \
    --max-tokens 256 \
    --out "${OUT}"

echo ""
echo "[DONE] Results saved to: ${OUT}"
echo "       Summary appended to: eval/results/summary.csv"
