from fastapi import HTTPException

def health():
    return {"status": "ok"}
