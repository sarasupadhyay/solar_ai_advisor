# Deployment Guide — Solar AI Advisor

This guide covers three deployment options: **Streamlit Community Cloud** (recommended, free),
**local machine**, and **Docker**.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Streamlit Community Cloud (Recommended)](#1-streamlit-community-cloud-recommended)
3. [Local Machine](#2-local-machine)
4. [Docker](#3-docker)
5. [Environment Variables Reference](#environment-variables-reference)
6. [Post-Deployment Checklist](#post-deployment-checklist)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.9 – 3.13 | 3.11 recommended |
| pip | latest | `pip install --upgrade pip` |
| Google Gemini API key | — | [Get it here](https://aistudio.google.com/app/apikey) |
| GitHub account | — | Needed for Streamlit Cloud |

---

## 1. Streamlit Community Cloud (Recommended)

**Cost: Free · No server management · Auto-deploys on git push**

### Step 1 — Push to GitHub

```bash
# If not already a git repo
git init
git add .
git commit -m "Initial commit"

# Create the repo on GitHub, then:
git remote add origin https://github.com/<your-username>/solar_ai_advisor.git
git branch -M main
git push -u origin main
```

> ⚠️ **FAISS index is in `.gitignore`** — see the note below.

### Step 2 — Handle the FAISS Index

The FAISS index (`faiss_index/`) is excluded from git (binary, large).  
You have two options:

**Option A — Commit the index (simplest)**
```bash
# Temporarily allow it (remove faiss_index/ line from .gitignore)
git add faiss_index/
git commit -m "chore: add pre-built faiss index"
```
The index is ~20–50 MB — acceptable for GitHub if the documents are standard size.

**Option B — Rebuild on first boot (advanced)**
Add a startup check to `app.py` that runs `build_rag.py` if `faiss_index/` is missing.
This requires the PDF documents to be present in the repo or loaded from cloud storage.

### Step 3 — Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **"New app"**.
3. Select your repository, branch `main`, and main file **`app.py`**.
4. Click **"Advanced settings"** → **"Secrets"** and paste:
   ```toml
   GEMINI_API_KEY = "your_actual_key_here"
   ```
5. Click **"Deploy"**.

Streamlit Cloud installs `requirements.txt` automatically.

### Step 4 — Verify

- The app URL will be: `https://<app-name>.streamlit.app`
- Check the logs if the app shows an error — the most common cause is a missing secret.

---

## 2. Local Machine

### Quick Start

```bash
# Clone
git clone https://github.com/<your-username>/solar_ai_advisor.git
cd solar_ai_advisor

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Mac / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
copy .env.example .env      # Windows
# cp .env.example .env      # Mac/Linux
# Edit .env and add your GEMINI_API_KEY

# Build the FAISS knowledge base (first time only)
python build_rag.py

# Run
streamlit run app.py
```

Open your browser at **http://localhost:8501**

### Helper Scripts

| Script | Platform | What it does |
|--------|----------|--------------|
| `setup.bat` | Windows | Creates venv, installs deps, copies .env.example |
| `setup.sh` | Mac/Linux | Same for Unix systems |

---

## 3. Docker

A `Dockerfile` is provided for containerised deployment.

```bash
# Build
docker build -t solar-ai-advisor .

# Run (pass your API key as an env var)
docker run -p 8501:8501 -e GEMINI_API_KEY=your_key solar-ai-advisor
```

Open **http://localhost:8501**

For production, use Docker Compose or a managed container platform (Railway, Render, Fly.io, GCP Cloud Run).

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini AI API key |

NASA POWER API is accessed without authentication — no key needed.

---

## Post-Deployment Checklist

- [ ] App loads without errors
- [ ] Map renders correctly
- [ ] "Calculate Solar Potential" returns results (NASA API reachable)
- [ ] Chatbot responds to a question (Gemini API key valid)
- [ ] Bill comparison section calculates correctly
- [ ] Generation forecast charts display

---

## Troubleshooting

### "GEMINI_API_KEY not found"
- Local: Check your `.env` file exists and contains the key.
- Streamlit Cloud: Check Settings → Secrets — make sure `GEMINI_API_KEY = "..."` is there.

### "Index folder 'faiss_index' not found"
- Run `python build_rag.py` to build the FAISS index.
- On Streamlit Cloud, either commit the `faiss_index/` folder or implement on-boot rebuild.

### NASA API returns no data / timeout
- The app automatically falls back to estimated values. The warning `⚠️ Could not reach NASA's live data service` will appear.
- NASA POWER API has rate limits. Retry after a minute.

### `torch` installation is slow / fails
- On low-RAM machines use: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
- `torch` is only needed for `sentence-transformers` (embeddings).

### Port already in use
```bash
streamlit run app.py --server.port 8502
```

---

**Deployed and stuck?** Open an issue on GitHub with the error message and your Python version.
