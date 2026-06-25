# ─────────────────────────────────────────────────────────────────────────────
#  Solar AI Advisor — Dockerfile
#  Build:  docker build -t solar-ai-advisor .
#  Run:    docker run -p 8501:8501 -e GEMINI_API_KEY=<your_key> solar-ai-advisor
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# System dependencies for faiss-cpu and torch (CPU-only)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app.py solar_calculator.py query_rag.py build_rag.py ./
COPY Solar_documents/ ./Solar_documents/
COPY faiss_index/ ./faiss_index/
COPY .streamlit/ ./.streamlit/

# Expose Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run
ENTRYPOINT ["streamlit", "run", "app.py", \
            "--server.port=8501", \
            "--server.address=0.0.0.0", \
            "--server.headless=true"]
