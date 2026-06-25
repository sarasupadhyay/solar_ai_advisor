#!/usr/bin/env bash
set -e

echo "============================================"
echo "  Solar AI Advisor — Unix Setup Script"
echo "============================================"
echo ""

# Step 1 — Virtual environment
if [ ! -d "venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[1/4] Virtual environment already exists, skipping."
fi

# Step 2 — Install dependencies
echo "[2/4] Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt

# Step 3 — Create .env from template
if [ ! -f ".env" ]; then
    echo "[3/4] Copying .env.example to .env..."
    cp .env.example .env
    echo "      ^^^ Edit .env and add your GEMINI_API_KEY before running."
else
    echo "[3/4] .env already exists, skipping."
fi

# Step 4 — Done
echo ""
echo "[4/4] Setup complete!"
echo ""
echo " Next steps:"
echo "  1. Edit .env and set GEMINI_API_KEY"
echo "  2. Run:  python build_rag.py     (builds the knowledge base)"
echo "  3. Run:  streamlit run app.py    (starts the app)"
echo ""
