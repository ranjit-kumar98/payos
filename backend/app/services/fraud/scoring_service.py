import logging
from datetime import datetime
from typing import List, Optional

from app.services.fraud.ml_service import FraudMLService, FraudPredictionResult
from app.services.fraud.rules import score_transaction as rule_score_transaction
from app.services.fraud.models import RuleScoreResult

logger = logging.getLogger(__name__)

class FraudAssessment:
    def __init__(
        self,
        rule_score: int,
        ml_score: Optional[float],
        final_score: float,
        risk_tier: str,
        triggered_rules: List[str],
        ml_available: bool
    ):
        self.rule_score = rule_score
        self.ml_score = ml_score
        self.final_score = final_score
        self.risk_tier = risk_tier
        self.triggered_rules = triggered_rules
        self.ml_available = ml_available

class FraudScoringService:
    def __init__(self):
        self._ml_service = FraudMLService()

    def assess(
        self,
        amount: float,
        currency: str,
        payment_method: str,
        transaction_timestamp: datetime,
        merchant_created_at: datetime,
        merchant_risk_tier: str,
        is_weekend: int
    ) -> FraudAssessment:
        logger.info("Starting rule-based fraud scoring")
        rule_result: RuleScoreResult = rule_score_transaction(
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            transaction_timestamp=transaction_timestamp,
            merchant_created_at=merchant_created_at
        )
        logger.info(f"Rule score: {rule_result.total_score}")
        logger.info(f"Triggered rules: {rule_result.triggered_rules}")

        ml_result: FraudPredictionResult = self._ml_service.predict_probability(
            amount=amount,
            hour_of_day=transaction_timestamp.hour,
            is_weekend=is_weekend,
            payment_method=payment_method,
            is_international=1 if currency.upper() != "INR" else 0,
            merchant_risk_tier=merchant_risk_tier,
            merchant_age_days=(transaction_timestamp - merchant_created_at).days
        )

        if ml_result.model_available:
            ml_score = ml_result.fraud_probability
            logger.info(f"ML score: {ml_score}")
            final_score = round(rule_result.total_score * 0.40 + ml_score * 0.60, 2)
            logger.info(f"Final blended score: {final_score}")
        else:
            ml_score = None
            final_score = float(rule_result.total_score)
            logger.warning("ML model unavailable, falling back to rule-based scoring only")
            logger.info(f"Final score (rule only): {final_score}")

        if final_score <= 30:
            risk_tier = "LOW"
        elif final_score <= 70:
            risk_tier = "MEDIUM"
        else:
            risk_tier = "HIGH"

        logger.info(f"Final risk tier: {risk_tier}")

        return FraudAssessment(
            rule_score=rule_result.total_score,
            ml_score=ml_score,
            final_score=final_score,
            risk_tier=risk_tier,
            triggered_rules=rule_result.triggered_rules,
            ml_available=ml_result.model_available
        )