
from pydantic import BaseModel
from typing import Dict

class InsightResponse(BaseModel):
    user_id: str
    savings_recommendation: str
    spending_breakdown: Dict[str, float]
    credit_utilization: float
    narrative: str = None  # Optional Gemini-generated narrative
