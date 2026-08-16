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

class PaymentMethodBreakdownItem(BaseModel):
    method: str
    count: int
    total_gmv: float
    success_rate: float

class PaymentMethodBreakdownResponse(RootModel[list[PaymentMethodBreakdownItem]]):
    pass

class DeclineReasonItem(BaseModel):
    reason: str
    count: int
    percentage: float

class DeclineReasonsResponse(RootModel[list[DeclineReasonItem]]):
    pass

class FraudHeatmapItem(BaseModel):
    hour: int  # 0-23
    low_risk_count: int
    medium_risk_count: int
    high_risk_count: int

class FraudHeatmapResponse(RootModel[list[FraudHeatmapItem]]):
    pass

class TopMerchantItem(BaseModel):
    merchant_name: str
    business_type: str
    gmv: float
    transaction_count: int
    success_rate: float
    dispute_rate: float

class TopMerchantsResponse(RootModel[list[TopMerchantItem]]):
    pass
