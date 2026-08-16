from pydantic import BaseModel, RootModel
from typing import List

class DailyGMVTrendItem(BaseModel):
    date: str  # YYYY-MM-DD
    total_gmv: float
    transaction_count: int
    success_count: int
    failed_count: int
    blocked_count: int

class DailyGMVTrendResponse(RootModel[list[DailyGMVTrendItem]]):
    pass

class AnalyticsOverviewResponse(BaseModel):
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    pending_transactions: int
    blocked_transactions: int
    total_successful_volume: float
    success_rate: float
