import logging
from datetime import datetime, time
from typing import List

from .models import RuleScoreResult

logger = logging.getLogger(__name__)

def _rule_high_amount(amount: float) -> int:
    """Rule 1: Amount > 100000 -> +35 points"""
    if amount > 100000:
        logger.info("Rule triggered: HIGH_AMOUNT")
        return 35
    return 0

def _rule_medium_amount(amount: float) -> int:
    """Rule 2: Amount >= 50000 and <= 100000 -> +20 points"""
    if 50000 <= amount <= 100000:
        logger.info("Rule triggered: MEDIUM_AMOUNT")
        return 20
    return 0

def _rule_international_currency(currency: str) -> int:
    """Rule 3: Currency is not INR -> +25 points"""
    if currency.upper() != "INR":
        logger.info("Rule triggered: INTERNATIONAL")
        return 25
    return 0

def _rule_night_transaction(transaction_timestamp: datetime) -> int:
    """Rule 4: Transaction time between 00:00 and 05:00 (inclusive) -> +15 points"""
    txn_time = transaction_timestamp.time()
    if time(0, 0) <= txn_time <= time(5, 0):
        logger.info("Rule triggered: NIGHT_TRANSACTION")
        return 15
    return 0

def _rule_new_merchant(merchant_created_at: datetime, transaction_timestamp: datetime) -> int:
    """Rule 5: Merchant age less than 30 days -> +20 points"""
    age_days = (transaction_timestamp - merchant_created_at).days
    if age_days < 30:
        logger.info("Rule triggered: NEW_MERCHANT")
        return 20
    return 0

def _rule_card_high_amount(payment_method: str, amount: float) -> int:
    """Rule 6: Payment method is CARD and amount > 20000 -> +10 points"""
    if payment_method.upper() == "CARD" and amount > 20000:
        logger.info("Rule triggered: CARD_HIGH_AMOUNT")
        return 10
    return 0

def score_transaction(
    amount: float,
    currency: str,
    payment_method: str,
    transaction_timestamp: datetime,
    merchant_created_at: datetime
) -> RuleScoreResult:
    """
    Calculate fraud risk score for a transaction based on defined rules.

    Returns:
        RuleScoreResult: total score, risk tier, and triggered rules.
    """
    logger.info("Starting fraud scoring")

    total_score = 0
    triggered_rules: List[str] = []

    # Apply rules
    score = _rule_high_amount(amount)
    if score:
        total_score += score
        triggered_rules.append("HIGH_AMOUNT")

    score = _rule_medium_amount(amount)
    if score:
        total_score += score
        triggered_rules.append("MEDIUM_AMOUNT")

    score = _rule_international_currency(currency)
    if score:
        total_score += score
        triggered_rules.append("INTERNATIONAL")

    score = _rule_night_transaction(transaction_timestamp)
    if score:
        total_score += score
        triggered_rules.append("NIGHT_TRANSACTION")

    score = _rule_new_merchant(merchant_created_at, transaction_timestamp)
    if score:
        total_score += score
        triggered_rules.append("NEW_MERCHANT")

    score = _rule_card_high_amount(payment_method, amount)
    if score:
        total_score += score
        triggered_rules.append("CARD_HIGH_AMOUNT")

    if total_score > 100:
        total_score = 100

    if total_score <= 30:
        risk_tier = "LOW"
    elif total_score <= 70:
        risk_tier = "MEDIUM"
    else:
        risk_tier = "HIGH"

    logger.info(f"Final fraud score: {total_score}, risk tier: {risk_tier}")

    return RuleScoreResult(
        total_score=total_score,
        risk_tier=risk_tier,
        triggered_rules=triggered_rules
    )