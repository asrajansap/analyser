

# SAP Short Dump Analyzer
https://chatgpt.com/c/69354d64-7f84-8324-9167-3ff96bb3a084

This repository packages a FastAPI service that analyzes SAP ST22 short dumps by calling an LLM deployed in SAP AI Core.


## What's included


- FastAPI service (`app/`) to receive ST22 JSON and call the LLM
- Dockerfile to build the service container
- AI Core Serving Template (`deployment/serving.yaml`) to host the container inside AI Core
- GitHub Actions workflow that builds and pushes the image


## Quickstart (local)


1. Copy `.env.example` to `.env` and fill values.
2. Start locally (recommended in a Python venv):


```bash
pip install -r app/requirements.txt
export TOKEN_URL=... # or use a .env loader
export CLIENT_ID=...
export CLIENT_SECRET=...
export AICORE_CHAT_URL=...
export TENANT_ID=...
uvicorn app.main:app --reload --port 8080# analyser
Analyser
