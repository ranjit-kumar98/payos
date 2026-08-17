import asyncio
import random
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session
from app.models import (
    User,
    Merchant,
    PaymentRoute,
    Transaction,
    Dispute,
    BnplLoan,
    BusinessType,
    RiskTier,
    PaymentMethod,
    TransactionStatus,
    DisputeReason,
    DisputeStatus,
    BnplStatus,
)
from app.core.config import settings
from app.core.security import get_password_hash
from app.services.fraud.scoring_service import FraudScoringService


NUM_MERCHANTS = 30
NUM_TRANSACTIONS = 8000
NUM_DISPUTES = 150
NUM_BNPL_LOANS = 300

PROGRESS_INTERVAL = 500
BLOCKED_TARGET_PERCENT = 0.03

fraud_service = FraudScoringService()


async def get_existing_counts(db: AsyncSession):
    return {
        "merchants": (
            await db.execute(select(func.count()).select_from(Merchant))
        ).scalar_one(),
        "users": (
            await db.execute(select(func.count()).select_from(User))
        ).scalar_one(),
        "payment_routes": (
            await db.execute(select(func.count()).select_from(PaymentRoute))
        ).scalar_one(),
        "transactions": (
            await db.execute(select(func.count()).select_from(Transaction))
        ).scalar_one(),
        "disputes": (
            await db.execute(select(func.count()).select_from(Dispute))
        ).scalar_one(),
        "bnpl_loans": (
            await db.execute(select(func.count()).select_from(BnplLoan))
        ).scalar_one(),
    }


async def get_or_create_demo_user(db: AsyncSession):
    demo_email = settings.DEMO_EMAIL
    demo_password = settings.DEMO_PASSWORD

    result = await db.execute(
        select(User).where(User.email == demo_email)
    )
    user = result.scalars().first()

    if user:
        print(f"Demo user already exists: {demo_email}")
        return user

    user = User(
        email=demo_email,
        hashed_password=get_password_hash(demo_password),
        full_name="Demo User",
        is_active=True,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    print(f"Created demo user: {demo_email}")

    return user


async def get_or_create_payment_routes(db: AsyncSession):
    count = (
        await db.execute(select(func.count()).select_from(PaymentRoute))
    ).scalar_one()

    if count > 0:
        print(
            f"Payment routes already exist ({count}), "
            "skipping payment route creation."
        )
        return

    demo_routes = [
        {
            "gateway_name": "Razorpay",
            "payment_method": PaymentMethod.UPI,
            "success_rate": 0.962,
            "avg_latency_ms": 150,
            "daily_limit": 1_000_000,
        },
        {
            "gateway_name": "Razorpay",
            "payment_method": PaymentMethod.CARD,
            "success_rate": 0.891,
            "avg_latency_ms": 200,
            "daily_limit": 500_000,
        },
        {
            "gateway_name": "PayU",
            "payment_method": PaymentMethod.UPI,
            "success_rate": 0.934,
            "avg_latency_ms": 160,
            "daily_limit": 1_200_000,
        },
        {
            "gateway_name": "PayU",
            "payment_method": PaymentMethod.CARD,
            "success_rate": 0.912,
            "avg_latency_ms": 210,
            "daily_limit": 450_000,
        },
        {
            "gateway_name": "Cashfree",
            "payment_method": PaymentMethod.UPI,
            "success_rate": 0.948,
            "avg_latency_ms": 140,
            "daily_limit": 900_000,
        },
        {
            "gateway_name": "Cashfree",
            "payment_method": PaymentMethod.WALLET,
            "success_rate": 0.876,
            "avg_latency_ms": 200,
            "daily_limit": 320_000,
        },
        {
            "gateway_name": "Paytm",
            "payment_method": PaymentMethod.WALLET,
            "success_rate": 0.921,
            "avg_latency_ms": 220,
            "daily_limit": 400_000,
        },
        {
            "gateway_name": "Paytm",
            "payment_method": PaymentMethod.NETBANKING,
            "success_rate": 0.883,
            "avg_latency_ms": 270,
            "daily_limit": 210_000,
        },
    ]

    for entry in demo_routes:
        route = PaymentRoute(
            gateway_name=entry["gateway_name"],
            payment_method=entry["payment_method"],
            success_rate=entry["success_rate"],
            avg_latency_ms=entry["avg_latency_ms"],
            daily_limit=entry["daily_limit"],
            is_active=True,
            last_updated=datetime.utcnow(),
        )
        db.add(route)

    await db.commit()

    print("Created 8 payment gateway routes.")


async def create_merchants(
    db: AsyncSession,
    user: User,
    existing_merchants_count: int,
):
    if existing_merchants_count >= NUM_MERCHANTS:
        print(
            f"Merchants already exist ({existing_merchants_count}), "
            "skipping merchant creation."
        )

        result = await db.execute(
            select(Merchant).limit(NUM_MERCHANTS)
        )
        return result.scalars().all()

    company_names = [
        "Reliance Industries",
        "Tata Consultancy Services",
        "HDFC Bank",
        "Infosys",
        "ICICI Bank",
        "Larsen & Toubro",
        "State Bank of India",
        "Bharti Airtel",
        "Kotak Mahindra Bank",
        "Axis Bank",
        "Maruti Suzuki",
        "Mahindra & Mahindra",
        "Wipro",
        "HCL Technologies",
        "ITC Limited",
        "Asian Paints",
        "Nestle India",
        "Bajaj Finance",
        "UltraTech Cement",
        "Power Grid Corporation",
        "Tata Steel",
        "Hero MotoCorp",
        "Dr. Reddy's Laboratories",
        "Sun Pharmaceutical",
        "Adani Ports",
        "Grasim Industries",
        "JSW Steel",
        "Titan Company",
        "Eicher Motors",
        "Divi's Laboratories",
    ]

    # Read actual existing risk distribution.
    existing_risk_counts = {
        RiskTier.LOW: 0,
        RiskTier.MEDIUM: 0,
        RiskTier.HIGH: 0,
    }

    result = await db.execute(select(Merchant.risk_tier))
    for risk in result.scalars().all():
        if risk in existing_risk_counts:
            existing_risk_counts[risk] += 1

    desired_distribution = {
        RiskTier.LOW: 18,
        RiskTier.MEDIUM: 9,
        RiskTier.HIGH: 3,
    }

    new_risk_counts = {
        tier: max(
            0,
            desired_distribution[tier] - existing_risk_counts[tier],
        )
        for tier in desired_distribution
    }

    new_merchants_needed = NUM_MERCHANTS - existing_merchants_count

    risk_distribution = []

    for tier in (
        RiskTier.LOW,
        RiskTier.MEDIUM,
        RiskTier.HIGH,
    ):
        risk_distribution.extend(
            [tier] * new_risk_counts[tier]
        )

    # Safety check.
    if len(risk_distribution) != new_merchants_needed:
        raise RuntimeError(
            "Merchant risk distribution does not match "
            "the number of merchants to create."
        )

    random.shuffle(risk_distribution)

    merchants = []

    for i in range(new_merchants_needed):
        merchant_number = existing_merchants_count + i + 1

        merchant = Merchant(
            name=company_names[existing_merchants_count + i],
            business_type=random.choice(list(BusinessType)),
            risk_tier=risk_distribution[i],
            email=f"merchant{merchant_number}@demo.com",
            phone=f"9999999{str(merchant_number).zfill(4)}",
            gstin=f"GSTIN{str(merchant_number).zfill(8)}",
            website=f"https://demo-merchant{merchant_number}.com",
            is_active=True,
            owner_id=user.id,
            created_at=(
                datetime.utcnow()
                - timedelta(days=random.randint(30, 365))
            ),
        )

        db.add(merchant)
        merchants.append(merchant)

        if (i + 1) % PROGRESS_INTERVAL == 0:
            print(f"Created {i + 1} merchants...")

    await db.commit()

    for merchant in merchants:
        await db.refresh(merchant)

    result = await db.execute(
        select(Merchant).limit(NUM_MERCHANTS)
    )
    all_merchants = result.scalars().all()

    print(
        f"Merchant seeding complete. Total merchants: "
        f"{len(all_merchants)}"
    )

    return all_merchants


def generate_normal_transaction_inputs(merchant):
    amount = round(random.uniform(10, 5_000), 2)

    payment_methods = (
        [PaymentMethod.UPI] * 45
        + [PaymentMethod.CARD] * 30
        + [PaymentMethod.WALLET] * 15
        + [PaymentMethod.NETBANKING] * 10
    )

    payment_method = random.choice(payment_methods)

    base_date = datetime.utcnow() - timedelta(
        days=random.randint(0, 89)
    )

    # More activity between 10 AM and 8 PM.
    hour_weights = (
        [0.5] * 10
        + [2.0] * 10
        + [0.5] * 4
    )

    hour = random.choices(
        range(24),
        weights=hour_weights,
        k=1,
    )[0]

    created_at = base_date.replace(
        hour=hour,
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0,
    )

    # Increase weekend probability.
    if created_at.weekday() < 5 and random.random() < 0.6:
        days_until_saturday = 5 - created_at.weekday()
        created_at += timedelta(days=days_until_saturday)

    return {
        "amount": amount,
        "currency": "INR",
        "payment_method": payment_method,
        "created_at": created_at,
    }


def generate_high_risk_transaction_inputs(merchant):
    """
    Generate a realistic high-risk transaction scenario using
    the application's existing fraud rules.

    We intentionally use:
      - high amount
      - international currency
      - CARD
      - night transaction

    This triggers the existing HIGH_AMOUNT, INTERNATIONAL,
    NIGHT_TRANSACTION and CARD_HIGH_AMOUNT rules. The final
    BLOCKED decision is still made ONLY by FraudScoringService.
    """

    base_date = datetime.utcnow() - timedelta(
        days=random.randint(0, 89)
    )

    created_at = base_date.replace(
        hour=random.randint(0, 5),
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0,
    )

    return {
        "amount": round(
            random.uniform(100_001, 250_000),
            2,
        ),
        "currency": random.choice(
            ["USD", "EUR", "GBP", "AED"]
        ),
        "payment_method": PaymentMethod.CARD,
        "created_at": created_at,
    }


def build_assessment(merchant, inputs):
    return fraud_service.assess(
        amount=inputs["amount"],
        currency=inputs["currency"],
        payment_method=inputs["payment_method"].value,
        transaction_timestamp=inputs["created_at"],
        merchant_created_at=merchant.created_at,
        merchant_risk_tier=merchant.risk_tier.value,
        is_weekend=(
            1
            if inputs["created_at"].weekday() >= 5
            else 0
        ),
    )


async def get_existing_blocked_count(db: AsyncSession):
    result = await db.execute(
        select(func.count())
        .select_from(Transaction)
        .where(
            Transaction.status == TransactionStatus.BLOCKED,
            Transaction.risk_tier == RiskTier.HIGH,
        )
    )

    return result.scalar_one()


async def create_transactions(
    db: AsyncSession,
    merchants: list,
    existing_transactions_count: int,
):
    if existing_transactions_count >= NUM_TRANSACTIONS:
        print(
            f"Transactions already exist "
            f"({existing_transactions_count}), "
            "skipping transaction creation."
        )

        result = await db.execute(
            select(Transaction).limit(NUM_TRANSACTIONS)
        )
        return result.scalars().all()

    transactions_to_create = (
        NUM_TRANSACTIONS - existing_transactions_count
    )

    existing_blocked_count = await get_existing_blocked_count(db)

    target_blocked_count = round(
        NUM_TRANSACTIONS * BLOCKED_TARGET_PERCENT
    )

    high_risk_needed = max(
        0,
        target_blocked_count - existing_blocked_count,
    )

    print(
        f"Target final HIGH/BLOCKED transactions: "
        f"{target_blocked_count}"
    )
    print(
        f"Existing HIGH/BLOCKED transactions: "
        f"{existing_blocked_count}"
    )
    print(
        f"New HIGH/BLOCKED transactions needed: "
        f"{high_risk_needed}"
    )

    transactions = []
    high_risk_created = 0

    normal_statuses = [
        TransactionStatus.PENDING,
        TransactionStatus.SUCCESS,
        TransactionStatus.FAILED,
        TransactionStatus.REFUNDED,
    ]

    normal_status_weights = [
        0.10,
        0.70,
        0.10,
        0.10,
    ]

    decline_reasons = [
        "Insufficient Funds",
        "Card Expired",
        "Invalid CVV",
        "Suspected Fraud",
        "Payment Gateway Timeout",
        "Duplicate Transaction",
        "Account Closed",
        "Limit Exceeded",
    ]

    i = 0

    while i < transactions_to_create:
        # Until we reach the target, deliberately generate
        # high-risk scenarios and let the fraud engine decide.
        need_high_risk = high_risk_created < high_risk_needed

        merchant = random.choice(merchants)

        if need_high_risk:
            inputs = generate_high_risk_transaction_inputs(
                merchant
            )

            assessment = build_assessment(
                merchant,
                inputs,
            )

            # If this candidate is not HIGH, discard it and
            # try another high-risk candidate.
            if assessment.risk_tier != "HIGH":
                continue

        else:
            inputs = generate_normal_transaction_inputs(
                merchant
            )

            assessment = build_assessment(
                merchant,
                inputs,
            )

        transaction = Transaction(
            merchant_id=merchant.id,
            razorpay_order_id=str(uuid4()),
            razorpay_payment_id=str(uuid4()),
            amount=inputs["amount"],
            currency=inputs["currency"],
            payment_method=inputs["payment_method"],
            status=TransactionStatus.PENDING,
            decline_reason=None,
            customer_email=(
                f"customer{random.randint(1, 10000)}"
                "@demo.com"
            ),
            customer_phone=(
                f"9999999{random.randint(1000, 9999)}"
            ),
            created_at=inputs["created_at"],
            updated_at=inputs["created_at"],
            risk_score=assessment.final_score,
            risk_tier=RiskTier(assessment.risk_tier),
            triggered_rules=assessment.triggered_rules,
        )

        # BLOCKED is determined exclusively by fraud scoring.
        if assessment.risk_tier == "HIGH":
            transaction.status = TransactionStatus.BLOCKED
            high_risk_created += 1
        else:
            transaction.status = random.choices(
                normal_statuses,
                weights=normal_status_weights,
                k=1,
            )[0]

            if transaction.status == TransactionStatus.FAILED:
                transaction.decline_reason = random.choice(
                    decline_reasons
                )

        db.add(transaction)
        transactions.append(transaction)

        i += 1

        if i % PROGRESS_INTERVAL == 0:
            print(
                f"Created {i} transactions... "
                f"HIGH/BLOCKED: {high_risk_created}"
            )

    await db.commit()

    for transaction in transactions:
        await db.refresh(transaction)

    print(
        f"Transaction seeding complete. "
        f"Created {len(transactions)} new transactions. "
        f"HIGH/BLOCKED created: {high_risk_created}"
    )

    return transactions


async def get_existing_sla_breached_count(db: AsyncSession):
    result = await db.execute(
        select(func.count())
        .select_from(Dispute)
        .where(
            Dispute.is_sla_breached.is_(True),
            Dispute.resolved_at.is_(None),
            Dispute.raised_at
            < datetime.utcnow() - timedelta(days=7),
        )
    )

    return result.scalar_one()


async def create_disputes(
    db: AsyncSession,
    transactions: list,
    existing_disputes_count: int,
):
    if existing_disputes_count >= NUM_DISPUTES:
        print(
            f"Disputes already exist "
            f"({existing_disputes_count}), "
            "skipping dispute creation."
        )

        result = await db.execute(
            select(Dispute).limit(NUM_DISPUTES)
        )
        return result.scalars().all()

    disputes_to_create = (
        NUM_DISPUTES - existing_disputes_count
    )

    existing_valid_sla_breached = (
        await get_existing_sla_breached_count(db)
    )

    sla_needed = max(
        0,
        15 - existing_valid_sla_breached,
    )

    print(
        f"Existing valid SLA-breached disputes: "
        f"{existing_valid_sla_breached}"
    )
    print(
        f"New SLA-breached disputes needed: "
        f"{sla_needed}"
    )

    disputes = []

    dispute_reasons = list(DisputeReason)

    normal_statuses = (
        [DisputeStatus.RAISED] * 50
        + [DisputeStatus.UNDER_REVIEW] * 50
        + [DisputeStatus.RESOLVED] * 35
        + [DisputeStatus.REJECTED] * 15
    )

    sla_created = 0

    for i in range(disputes_to_create):
        transaction = random.choice(transactions)

        if sla_created < sla_needed:
            status = random.choice(
                [
                    DisputeStatus.RAISED,
                    DisputeStatus.UNDER_REVIEW,
                ]
            )

            # Guaranteed older than 7 days.
            raised_at = datetime.utcnow() - timedelta(
                days=random.randint(8, 30)
            )

            is_sla_breached = True
            resolved_at = None

            sla_created += 1

        else:
            status = random.choice(normal_statuses)

            raised_at = datetime.utcnow() - timedelta(
                days=random.randint(1, 30)
            )

            is_sla_breached = False

            if status == DisputeStatus.RESOLVED:
                resolved_at = raised_at + timedelta(
                    days=random.randint(1, 5)
                )
            else:
                resolved_at = None

        dispute = Dispute(
            transaction_id=transaction.id,
            merchant_id=transaction.merchant_id,
            reason=random.choice(dispute_reasons),
            description="Demo dispute created by seed script",
            status=status,
            raised_at=raised_at,
            resolved_at=resolved_at,
            is_sla_breached=is_sla_breached,
        )

        db.add(dispute)
        disputes.append(dispute)

        if (i + 1) % PROGRESS_INTERVAL == 0:
            print(f"Created {i + 1} disputes...")

    await db.commit()

    for dispute in disputes:
        await db.refresh(dispute)

    print(
        f"Dispute seeding complete. "
        f"Created {len(disputes)} new disputes. "
        f"SLA-breached created: {sla_created}"
    )

    return disputes


async def get_existing_bnpl_status_counts(db: AsyncSession):
    result = await db.execute(
        select(
            BnplLoan.status,
            func.count(BnplLoan.id),
        ).group_by(BnplLoan.status)
    )

    counts = {
        BnplStatus.ACTIVE: 0,
        BnplStatus.CLOSED: 0,
        BnplStatus.DEFAULTED: 0,
    }

    for status, count in result.all():
        if status in counts:
            counts[status] = count

    return counts


async def create_bnpl_loans(
    db: AsyncSession,
    users: list,
    transactions: list,
    existing_bnpl_count: int,
):
    if existing_bnpl_count >= NUM_BNPL_LOANS:
        print(
            f"BNPL loans already exist "
            f"({existing_bnpl_count}), "
            "skipping BNPL loan creation."
        )

        result = await db.execute(
            select(BnplLoan).limit(NUM_BNPL_LOANS)
        )
        return result.scalars().all()

    loans_to_create = (
        NUM_BNPL_LOANS - existing_bnpl_count
    )

    existing_status_counts = (
        await get_existing_bnpl_status_counts(db)
    )

    desired_status_counts = {
        BnplStatus.ACTIVE: 180,
        BnplStatus.CLOSED: 105,
        BnplStatus.DEFAULTED: 15,
    }

    status_pool = []

    for status, desired_count in desired_status_counts.items():
        missing = max(
            0,
            desired_count
            - existing_status_counts.get(status, 0),
        )

        status_pool.extend([status] * missing)

    if len(status_pool) < loans_to_create:
        raise RuntimeError(
            "Unable to build BNPL status pool for "
            "the requested final distribution."
        )

    random.shuffle(status_pool)

    status_pool = status_pool[:loans_to_create]

    bnpl_loans = []

    for i in range(loans_to_create):
        user = random.choice(users)
        transaction = random.choice(transactions)

        loan = BnplLoan(
            user_id=str(user.id),
            transaction_id=transaction.id,
            principal=round(
                random.uniform(1_000, 100_000),
                2,
            ),
            tenure_months=random.choice(
                [3, 6, 9, 12]
            ),
            interest_rate_pa=round(
                random.uniform(8, 24),
                2,
            ),
            emi_amount=round(
                random.uniform(500, 10_000),
                2,
            ),
            total_interest=round(
                random.uniform(100, 10_000),
                2,
            ),
            total_payable=round(
                random.uniform(1_100, 110_000),
                2,
            ),
            status=status_pool[i],
            repayment_schedule={},
            created_at=(
                datetime.utcnow()
                - timedelta(days=random.randint(1, 365))
            ),
        )

        db.add(loan)
        bnpl_loans.append(loan)

        if (i + 1) % PROGRESS_INTERVAL == 0:
            print(f"Created {i + 1} BNPL loans...")

    await db.commit()

    for loan in bnpl_loans:
        await db.refresh(loan)

    print(
        f"BNPL seeding complete. "
        f"Created {len(bnpl_loans)} new loans."
    )

    return bnpl_loans


async def main():
    async with async_session() as db:
        counts = await get_existing_counts(db)

        print("=" * 80)
        print("PayOS demo data seeding")
        print("=" * 80)
        print(f"Existing counts: {counts}")
        print()

        # 1. Payment routes
        await get_or_create_payment_routes(db)

        # 2. Demo user
        user = await get_or_create_demo_user(db)

        # 3. Merchants
        merchants = await create_merchants(
            db,
            user,
            counts["merchants"],
        )

        # 4. Transactions
        transactions = await create_transactions(
            db,
            merchants,
            counts["transactions"],
        )

        # 5. Disputes
        disputes = await create_disputes(
            db,
            transactions,
            counts["disputes"],
        )

        # 6. BNPL loans
        result = await db.execute(select(User))
        users = result.scalars().all()

        await create_bnpl_loans(
            db,
            users,
            transactions,
            counts["bnpl_loans"],
        )

        print()
        print("=" * 80)
        print("PayOS demo data seeding completed.")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())