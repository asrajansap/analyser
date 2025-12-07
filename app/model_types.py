rom pydantic import BaseModel
from typing import Any, Dict


class DumpRequest(BaseModel):
dump_json: Dict[str, Any]
