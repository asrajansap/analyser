from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
import json
from prompt import SHORTDUMP_PROMPT
from model_types import DumpRequest
from healthcheck import health

app = FastAPI(title="SAP Short Dump Analyzer")

# -----------------------------------------------------------
# Read environment variables (set these via secrets/config in AI Core)
# -----------------------------------------------------------

#AICORE_CHAT_URL = os.environ.get("AICORE_CHAT_URL")
AICORE_CHAT_URL = 'https://api.ai.prod.eu-central-1.aws.ml.hana.ondemand.com/v2/inference/deployments/d140b0f59064958a/chat/completions?api-version=2023-05-15'
#TOKEN_URL = os.environ.get("TOKEN_URL")
TOKEN_URL = 'https://hclbuild-g03o2ijo.authentication.eu10.hana.ondemand.com/oauth/token'
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
#TENANT_ID = os.environ.get("TENANT_ID")
TENANT_ID = 'c4ab076f-04d6-4ab4-9648-c9e626254aaa'
RESOURCE_GROUP = os.environ.get("RESOURCE_GROUP", "default")

# Debug prints
print("WARNING: AICORE_CHAT_URL:", AICORE_CHAT_URL)
print("WARNING: TOKEN_URL:", TOKEN_URL)
print("WARNING: CLIENT_ID:", CLIENT_ID)
print("WARNING: CLIENT_SECRET:", CLIENT_SECRET)
print("WARNING: TENANT_ID:", TENANT_ID)

# If any required variable is missing, do NOT break container startup
if not all([AICORE_CHAT_URL, TOKEN_URL, CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
    app.logger = app.logger if hasattr(app, "logger") else None


# -----------------------------------------------------------
# Token Retrieval Function
# -----------------------------------------------------------

def get_token():
    """Get OAuth token from SAP token endpoint using client_credentials."""
    # Read environment variable
    TOKEN_URL = os.environ.get("TOKEN_URL")
    if not TOKEN_URL:
        raise ValueError("TOKEN_URL environment variable not set!")
    # Remove accidental surrounding quotes, if any
    TOKEN_URL = TOKEN_URL.strip('\'"')  # removes both ' and " from start/end
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    resp = requests.post(TOKEN_URL, data=payload, timeout=10)

    try:
        resp.raise_for_status()
    except requests.HTTPError:
        raise HTTPException(status_code=502, detail=f"Token endpoint error: {resp.text}")

    return resp.json().get("access_token")


# -----------------------------------------------------------
# Main /analyze endpoint
# -----------------------------------------------------------

@app.post("/analyze")
def analyze_dump(req: DumpRequest):
    """Accepts a JSON dump (as JSON object) and returns LLM analysis."""
    if not req.dump_json:
        raise HTTPException(status_code=400, detail="dump_json payload required")

    prompt = SHORTDUMP_PROMPT.format(dump=json.dumps(req.dump_json, indent=2))

    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "AI-Tenant-Id": TENANT_ID,
        "AI-Resource-Group": RESOURCE_GROUP,
    }

    body = {"messages": [{"role": "user", "content": prompt}]}

    try:
        resp = requests.post(AICORE_CHAT_URL, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
    except requests.HTTPError:
        raise HTTPException(status_code=502, detail=f"AI Core error: {resp.text}")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Communication error: {str(e)}")

    data = resp.json()

    # safe access
    if isinstance(data, dict) and "choices" in data and len(data["choices"]) > 0:
        content = data["choices"][0]["message"]["content"]

        # try parse JSON returned by LLM
        try:
            parsed = json.loads(content)
            return {"analysis": parsed}
        except Exception:
            return {"analysis_text": content}

    return {"raw": data}


# -----------------------------------------------------------
# Health Check Endpoint
# -----------------------------------------------------------

@app.get("/healthz")
def healthz():
    return health()
