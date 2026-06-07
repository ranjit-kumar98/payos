import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Enum, Float, Integer, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class BusinessType(enum.Enum):
    ECOMMERCE = "ECOMMERCE"
    FOOD = "FOOD"
    TRAVEL = "TRAVEL"
    GAMING = "GAMING"
    RETAIL = "RETAIL"
    FINTECH = "FINTECH"

class RiskTier(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class PaymentMethod(enum.Enum):
    UPI = "UPI"
    CARD = "CARD"
    WALLET = "WALLET"
    NETBANKING = "NETBANKING"

class TransactionStatus(enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    REFUNDED = "REFUNDED"

class DisputeReason(enum.Enum):
    FRAUD = "FRAUD"
    DUPLICATE = "DUPLICATE"
    NOT_RECEIVED = "NOT_RECEIVED"
    WRONG_AMOUNT = "WRONG_AMOUNT"

class DisputeStatus(enum.Enum):
    RAISED = "RAISED"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"

class BnplStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    DEFAULTED = "DEFAULTED"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    merchants = relationship("Merchant", back_populates="owner")

class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    business_type = Column(Enum(BusinessType), nullable=False)
    risk_tier = Column(Enum(RiskTier), nullable=False)
    email = Column(String)
    phone = Column(String)
    gstin = Column(String)
    website = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    owner = relationship("User", back_populates="merchants")
    transactions = relationship("Transaction", back_populates="merchant")
    disputes = relationship("Dispute", back_populates="merchant")

class PaymentRoute(Base):
    __tablename__ = "payment_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gateway_name = Column(String, nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    success_rate = Column(Float)
    avg_latency_ms = Column(Float)
    is_active = Column(Boolean, default=True)
    daily_limit = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    razorpay_order_id = Column(String)
    razorpay_payment_id = Column(String)
    amount = Column(Float)
    currency = Column(String, default="INR")
    payment_method = Column(Enum(PaymentMethod))
    status = Column(Enum(TransactionStatus))
    risk_score = Column(Float)
    risk_tier = Column(Enum(RiskTier))
    triggered_rules = Column(JSON)
    decline_reason = Column(String)
    gateway_used = Column(String)
    gateway_fee = Column(Float)
    customer_email = Column(String)
    customer_phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    merchant = relationship("Merchant", back_populates="transactions")
    disputes = relationship("Dispute", back_populates="transaction")
    bnpl_loans = relationship("BnplLoan", back_populates="transaction")

class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchants.id"))
    reason = Column(Enum(DisputeReason))
    description = Column(String)
    status = Column(Enum(DisputeStatus))
    resolution_notes = Column(String)
    raised_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    is_sla_breached = Column(Boolean, default=False)
    sla_deadline = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="disputes")
    merchant = relationship("Merchant", back_populates="disputes")

class BnplLoan(Base):
    __tablename__ = "bnpl_loans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    principal = Column(Float)
    tenure_months = Column(Integer)
    interest_rate_pa = Column(Float)
    emi_amount = Column(Float)
    total_interest = Column(Float)
    total_payable = Column(Float)
    status = Column(Enum(BnplStatus))
    repayment_schedule = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="bnpl_loans")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String)
    entity_id = Column(String)
    action = Column(String)
    performed_by = Column(String)
    old_value = Column(JSON)
    new_value = Column(JSON)
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)