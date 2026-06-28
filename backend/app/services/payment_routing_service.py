import asyncio
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models import PaymentRoute, Merchant, User
from enum import Enum

class PaymentRoutingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Percentage fee for estimated fee calculation
        self.estimated_fee_pct = 0.02  # 2% fee

    async def seed_demo_data(self):
        # Seed payment_routes if empty
        count_query = await self.db.execute(select(func.count()).select_from(PaymentRoute))
        count = count_query.scalar_one()
        if count == 0:
            # Prepare demo data
            demo_data = [
                # Razorpay
                {"gateway_name": "Razorpay", "payment_method": "UPI", "success_rate": 0.98, "avg_latency_ms": 150, "daily_limit": 1000000, "is_active": True},
                {"gateway_name": "Razorpay", "payment_method": "CARD", "success_rate": 0.95, "avg_latency_ms": 200, "daily_limit": 500000, "is_active": True},
                {"gateway_name": "Razorpay", "payment_method": "WALLET", "success_rate": 0.92, "avg_latency_ms": 180, "daily_limit": 300000, "is_active": True},
                {"gateway_name": "Razorpay", "payment_method": "NETBANKING", "success_rate": 0.90, "avg_latency_ms": 250, "daily_limit": 200000, "is_active": True},
                # Cashfree
                {"gateway_name": "Cashfree", "payment_method": "UPI", "success_rate": 0.96, "avg_latency_ms": 160, "daily_limit": 1200000, "is_active": True},
                {"gateway_name": "Cashfree", "payment_method": "CARD", "success_rate": 0.94, "avg_latency_ms": 210, "daily_limit": 450000, "is_active": True},
                {"gateway_name": "Cashfree", "payment_method": "WALLET", "success_rate": 0.91, "avg_latency_ms": 190, "daily_limit": 350000, "is_active": True},
                {"gateway_name": "Cashfree", "payment_method": "NETBANKING", "success_rate": 0.89, "avg_latency_ms": 260, "daily_limit": 250000, "is_active": True},
                # PhonePe
                {"gateway_name": "PhonePe", "payment_method": "UPI", "success_rate": 0.97, "avg_latency_ms": 140, "daily_limit": 900000, "is_active": True},
                {"gateway_name": "PhonePe", "payment_method": "CARD", "success_rate": 0.93, "avg_latency_ms": 220, "daily_limit": 400000, "is_active": True},
                {"gateway_name": "PhonePe", "payment_method": "WALLET", "success_rate": 0.90, "avg_latency_ms": 200, "daily_limit": 320000, "is_active": True},
                {"gateway_name": "PhonePe", "payment_method": "NETBANKING", "success_rate": 0.88, "avg_latency_ms": 270, "daily_limit": 210000, "is_active": True}
            ]
            # Insert demo payment routes
            for entry in demo_data:
                pr = PaymentRoute(
                    gateway_name=entry["gateway_name"],
                    payment_method=entry["payment_method"],
                    success_rate=entry["success_rate"],
                    avg_latency_ms=entry["avg_latency_ms"],
                    daily_limit=entry["daily_limit"],
                    is_active=entry["is_active"],
                    last_updated=datetime.utcnow()
                )
                self.db.add(pr)
            await self.db.commit()

        # Seed merchant if empty
        merchant_count_query = await self.db.execute(select(func.count()).select_from(Merchant))
        merchant_count = merchant_count_query.scalar_one()
        if merchant_count == 0:
            # Pick any one user from users
            user_query = await self.db.execute(select(User).limit(1))
            user = user_query.scalars().first()
            if user is None:
                # No user available, do nothing
                return
            merchant = Merchant(
                name="Demo Merchant",
                business_type="RETAIL",
                risk_tier="LOW",
                email="demo@merchant.com",
                phone="9999999999",
                gstin="1234GSTIN",
                website="https://demo-merchant.com",
                is_active=True,
                owner_id=user.id,
                created_at=datetime.utcnow()
            )
            self.db.add(merchant)
            await self.db.commit()

    async def route_payment(self, amount: float, currency: str, payment_method: str) -> Dict[str, Any]:
        # Query active gateways matching payment method
        result = await self.db.execute(
            select(PaymentRoute).where(
                PaymentRoute.is_active == True,
                PaymentRoute.payment_method == payment_method
            )
        )
        gateways = result.scalars().all()
        if len(gateways) == 0:
            raise ValueError(f"No active payment gateways support payment method {payment_method}")

        # Sort by success_rate descending
        gateways.sort(key=lambda x: x.success_rate, reverse=True)
        selected = gateways[0]
        backup = gateways[1] if len(gateways) > 1 else None

        estimated_fee = round(amount * self.estimated_fee_pct, 2)
        reason = f"Selected {selected.gateway_name} for highest success rate {selected.success_rate * 100:.2f}%"

        return {
            "selected_gateway": selected.gateway_name,
            "backup_gateway": backup.gateway_name if backup else None,
            "estimated_fee": estimated_fee,
            "selection_reason": reason
        }