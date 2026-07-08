from typing import List
from pydantic import BaseModel

class RuleScoreResult(BaseModel):
    total_score: int
    risk_tier: str
    triggered_rules: List[str]