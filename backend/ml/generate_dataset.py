import csv
import logging
import random
from datetime import datetime
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PAYMENT_METHODS = ["UPI", "CARD", "NETBANKING", "WALLET"]
MERCHANT_RISK_TIERS = ["LOW", "MEDIUM", "HIGH"]

def generate_amount() -> float:
    """
    Generate a realistic transaction amount.
    Mostly small and medium payments, some high-value.
    """
    p = random.random()
    if p < 0.7:
        # Small amounts: 10 to 1000
        return round(random.uniform(10, 1000), 2)
    elif p < 0.95:
        # Medium amounts: 1000 to 20000
        return round(random.uniform(1000, 20000), 2)
    else:
        # High amounts: 20000 to 200000
        return round(random.uniform(20000, 200000), 2)

def generate_hour_of_day() -> int:
    """Generate hour of day 0-23."""
    return random.randint(0, 23)

def generate_is_weekend() -> int:
    """Generate 0 or 1 for weekend."""
    return random.choice([0, 1])

def generate_payment_method() -> str:
    """Randomly select a payment method."""
    return random.choice(PAYMENT_METHODS)

def generate_is_international() -> int:
    """Randomly decide if transaction is international."""
    # Assume 10% international transactions
    return 1 if random.random() < 0.1 else 0

def generate_merchant_risk_tier() -> str:
    """Randomly select merchant risk tier."""
    p = random.random()
    if p < 0.6:
        return "LOW"
    elif p < 0.9:
        return "MEDIUM"
    else:
        return "HIGH"

def generate_merchant_age_days() -> int:
    """Generate merchant age in days between 1 and 1000."""
    return random.randint(1, 1000)

def calculate_risk_score(
    amount: float,
    is_international: int,
    merchant_age_days: int,
    payment_method: str,
    hour_of_day: int,
    merchant_risk_tier: str,
) -> int:
    """
    Calculate a deterministic fraud risk score.
    Maximum score = 100.
    """

    score = 0

    if amount > 100000:
        score += 35
    elif amount >= 50000:
        score += 20

    if is_international:
        score += 25

    if merchant_age_days < 30:
        score += 20

    if payment_method == "CARD" and amount > 20000:
        score += 10

    if 0 <= hour_of_day <= 5:
        score += 15

    if merchant_risk_tier == "HIGH":
        score += 20

    return min(score, 100)

def generate_dataset(num_records: int = 15000) -> List[Dict]:
    """
    Generate a synthetic fraud dataset.

    Strategy:
    1. Generate all transactions.
    2. Calculate deterministic risk score.
    3. Add small noise.
    4. Label approximately top 3% as fraud.
    """

    random.seed(42)

    dataset = []

    for _ in range(num_records):

        amount = generate_amount()
        hour_of_day = generate_hour_of_day()
        is_weekend = generate_is_weekend()
        payment_method = generate_payment_method()
        is_international = generate_is_international()
        merchant_risk_tier = generate_merchant_risk_tier()
        merchant_age_days = generate_merchant_age_days()

        risk_score = calculate_risk_score(
            amount,
            is_international,
            merchant_age_days,
            payment_method,
            hour_of_day,
            merchant_risk_tier,
        )

        # Small noise so labels aren't perfectly deterministic
        noisy_score = risk_score + random.uniform(-5, 5)

        dataset.append(
            {
                "amount": amount,
                "hour_of_day": hour_of_day,
                "is_weekend": is_weekend,
                "payment_method": payment_method,
                "is_international": is_international,
                "merchant_risk_tier": merchant_risk_tier,
                "merchant_age_days": merchant_age_days,
                "risk_score": noisy_score,
                "is_fraud": 0,
            }
        )

    # ------------------------------------------------------------------
    # Mark top ~3% as fraud
    # ------------------------------------------------------------------

    dataset.sort(key=lambda x: x["risk_score"], reverse=True)

    fraud_count = int(num_records * 0.03)

    for i in range(fraud_count):
        dataset[i]["is_fraud"] = 1

    for row in dataset:
        del row["risk_score"]

    random.shuffle(dataset)

    return dataset
import os

def save_dataset(dataset: List[Dict], filepath: str) -> None:
    """Save dataset to CSV file."""
    fieldnames = [
        "amount",
        "hour_of_day",
        "is_weekend",
        "payment_method",
        "is_international",
        "merchant_risk_tier",
        "merchant_age_days",
        "is_fraud"
    ]
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, mode="w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in dataset:
            writer.writerow(row)
    logger.info(f"Dataset saved to {filepath}")

def print_summary(dataset: List[Dict]) -> None:
    """Print dataset summary statistics."""
    total = len(dataset)
    fraud_count = sum(d["is_fraud"] for d in dataset)
    fraud_pct = fraud_count / total * 100

    payment_method_counts = {}
    merchant_risk_counts = {}

    for d in dataset:
        pm = d["payment_method"]
        mr = d["merchant_risk_tier"]
        payment_method_counts[pm] = payment_method_counts.get(pm, 0) + 1
        merchant_risk_counts[mr] = merchant_risk_counts.get(mr, 0) + 1

    logger.info(f"Total transactions: {total}")
    logger.info(f"Fraud count: {fraud_count}")
    logger.info(f"Fraud percentage: {fraud_pct:.2f}%")
    logger.info("Payment method distribution:")
    for pm, count in payment_method_counts.items():
        logger.info(f"  {pm}: {count}")
    logger.info("Merchant risk tier distribution:")
    for mr, count in merchant_risk_counts.items():
        logger.info(f"  {mr}: {count}")

def main() -> None:
    dataset = generate_dataset()
    filepath = "backend/ml/datasets/synthetic_transactions.csv"
    save_dataset(dataset, filepath)
    print_summary(dataset)




if __name__ == "__main__":
    main()