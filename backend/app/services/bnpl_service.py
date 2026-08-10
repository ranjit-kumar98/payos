from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import List, Dict, Any
from dataclasses import dataclass

# Set decimal precision for financial calculations
getcontext().prec = 28

@dataclass
class RepaymentEntry:
    month: int
    emi: Decimal
    interest: Decimal
    principal: Decimal
    remaining_balance: Decimal

@dataclass
class BnplCalculationResult:
    principal: Decimal
    tenure: int
    annual_interest_rate: Decimal
    monthly_emi: Decimal
    total_interest: Decimal
    total_repayment: Decimal
    repayment_schedule: List[RepaymentEntry]

class BnplService:
    MIN_AMOUNT = Decimal('3000.00')
    MAX_AMOUNT = Decimal('200000.00')
    ALLOWED_TENURES = {3, 6, 9, 12}
    INTEREST_RATES = {
        3: Decimal('0.12'),
        6: Decimal('0.14'),
        9: Decimal('0.16'),
        12: Decimal('0.18'),
    }

    @classmethod
    def validate_eligibility(cls, principal: Decimal, tenure: int) -> None:
        if principal < cls.MIN_AMOUNT:
            raise ValueError(f"Amount below minimum allowed: {cls.MIN_AMOUNT}")
        if principal > cls.MAX_AMOUNT:
            raise ValueError(f"Amount above maximum allowed: {cls.MAX_AMOUNT}")
        if principal <= 0:
            raise ValueError("Amount must be positive")
        if tenure not in cls.ALLOWED_TENURES:
            raise ValueError(f"Unsupported tenure: {tenure}. Allowed tenures: {sorted(cls.ALLOWED_TENURES)}")

    @classmethod
    def calculate_reducing_balance_emi(cls, principal: Decimal, tenure: int) -> BnplCalculationResult:
        cls.validate_eligibility(principal, tenure)
        annual_rate = cls.INTEREST_RATES[tenure]
        monthly_rate = annual_rate / Decimal('12')

        # EMI formula: P * r * (1+r)^n / ((1+r)^n - 1)
        one_plus_r_pow_n = (1 + monthly_rate) ** tenure
        emi = (principal * monthly_rate * one_plus_r_pow_n) / (one_plus_r_pow_n - 1)
        emi = emi.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        remaining_balance = principal
        total_interest = Decimal('0.00')
        repayment_schedule: List[RepaymentEntry] = []

        for month in range(1, tenure + 1):
            interest = (remaining_balance * monthly_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            principal_payment = (emi - interest).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            # Adjust final payment to ensure remaining balance is zero
            if month == tenure:
                principal_payment = remaining_balance
                final_emi = (principal_payment + interest).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                final_emi = emi
            remaining_balance = (remaining_balance - principal_payment).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total_interest += interest

            repayment_schedule.append(
                RepaymentEntry(
                    month=month,
                    emi=final_emi,
                    interest=interest,
                    principal=principal_payment,
                    remaining_balance=remaining_balance
                )
            )

        total_repayment = (principal + total_interest).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return BnplCalculationResult(
            principal=principal,
            tenure=tenure,
            annual_interest_rate=annual_rate,
            monthly_emi=emi,
            total_interest=total_interest,
            total_repayment=total_repayment,
            repayment_schedule=repayment_schedule
        )
