from fastapi import FastAPI, HTTPException


def get_token():
"""Get OAuth token from SAP token endpoint using client_credentials."""
payload = {
"grant_type": "client_credentials",
"client_id": CLIENT_ID,
"client_secret": CLIENT_SECRET,
}
resp = requests.post(TOKEN_URL, data=payload, timeout=10)
try:
resp.raise_for_status()
except requests.HTTPError as e:
raise HTTPException(status_code=502, detail=f"Token endpoint error: {resp.text}")


return resp.json().get("access_token")




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
except requests.HTTPError as e:
raise HTTPException(status_code=502, detail=f"AI Core error: {resp.text}")
except requests.RequestException as e:
raise HTTPException(status_code=502, detail=f"Communication error: {str(e)}")


data = resp.json()
# safe access to choices
if isinstance(data, dict) and "choices" in data and len(data["choices"]) > 0:
content = data["choices"][0]["message"]["content"]
# Optionally try to parse JSON from the model if it returns JSON
try:
parsed = json.loads(content)
return {"analysis": parsed}
except Exception:
return {"analysis_text": content}


return {"raw": data}




@app.get("/healthz")
def healthz():
return health()
