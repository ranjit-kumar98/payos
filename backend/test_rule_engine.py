from datetime import datetime, timedelta

from app.services.fraud.rules import score_transaction

print("Script started")
def test_case(name, **kwargs):
    print(f"\n{name}")
    result = score_transaction(**kwargs)
    print(result)


now = datetime.now()

# 1. Low risk
test_case(
    "Low Risk",
    amount=1000,
    currency="INR",
    payment_method="UPI",
    transaction_timestamp=now.replace(hour=12, minute=0),
    merchant_created_at=now - timedelta(days=100),
)

# 2. High amount
test_case(
    "High Amount",
    amount=150000,
    currency="INR",
    payment_method="UPI",
    transaction_timestamp=now.replace(hour=12, minute=0),
    merchant_created_at=now - timedelta(days=100),
)

# 3. International
test_case(
    "International",
    amount=1000,
    currency="USD",
    payment_method="UPI",
    transaction_timestamp=now.replace(hour=12, minute=0),
    merchant_created_at=now - timedelta(days=100),
)

# 4. New merchant
test_case(
    "New Merchant",
    amount=1000,
    currency="INR",
    payment_method="UPI",
    transaction_timestamp=now.replace(hour=12, minute=0),
    merchant_created_at=now - timedelta(days=10),
)

# 5. Midnight
test_case(
    "Midnight",
    amount=1000,
    currency="INR",
    payment_method="UPI",
    transaction_timestamp=now.replace(hour=2, minute=30),
    merchant_created_at=now - timedelta(days=100),
)

# 6. High value card
test_case(
    "High Value Card",
    amount=25000,
    currency="INR",
    payment_method="CARD",
    transaction_timestamp=now.replace(hour=12, minute=0),
    merchant_created_at=now - timedelta(days=100),
)

# 7. Everything triggered
test_case(
    "Everything",
    amount=150000,
    currency="USD",
    payment_method="CARD",
    transaction_timestamp=now.replace(hour=2, minute=30),
    merchant_created_at=now - timedelta(days=5),
)

print(score_transaction(
    amount=49999,
    currency="INR",
    payment_method="UPI",
    transaction_timestamp=now.replace(hour=12),
    merchant_created_at=now - timedelta(days=100)
))

print(score_transaction(
    amount=50000,
    currency="INR",
    payment_method="UPI",
    transaction_timestamp=now.replace(hour=12),
    merchant_created_at=now - timedelta(days=100)
))

print(score_transaction(
    amount=100000,
    currency="INR",
    payment_method="UPI",
    transaction_timestamp=now.replace(hour=12),
    merchant_created_at=now - timedelta(days=100)
))

print(score_transaction(
    amount=100001,
    currency="INR",
    payment_method="UPI",
    transaction_timestamp=now.replace(hour=12),
    merchant_created_at=now - timedelta(days=100)
))

print(
    score_transaction(
        amount=1000,
        currency="INR",
        payment_method="UPI",
        transaction_timestamp=now.replace(hour=12),
        merchant_created_at=now - timedelta(days=29),
    )
)

print(
    score_transaction(
        amount=1000,
        currency="INR",
        payment_method="UPI",
        transaction_timestamp=now.replace(hour=12),
        merchant_created_at=now - timedelta(days=30),
    )
)

print(
    score_transaction(
        amount=1000,
        currency="INR",
        payment_method="UPI",
        transaction_timestamp=now.replace(hour=0, minute=0),
        merchant_created_at=now - timedelta(days=100),
    )
)

print(
    score_transaction(
        amount=1000,
        currency="INR",
        payment_method="UPI",
        transaction_timestamp=now.replace(hour=5, minute=0),
        merchant_created_at=now - timedelta(days=100),
    )
)

print(
    score_transaction(
        amount=1000,
        currency="INR",
        payment_method="UPI",
        transaction_timestamp=now.replace(hour=5, minute=1),
        merchant_created_at=now - timedelta(days=100),
    )
)