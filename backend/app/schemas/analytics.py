from pydantic import BaseModel

class AnalyticsOverviewResponse(BaseModel):
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    pending_transactions: int
    blocked_transactions: int
    total_successful_volume: float
    success_rate: float