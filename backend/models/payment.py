from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.sql_database import Base
import enum

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class PaymentProvider(str, enum.Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"

class RefundStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Payment details
    amount = Column(Float, nullable=False)  # Total amount
    currency = Column(String, default="usd", nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    provider = Column(Enum(PaymentProvider), nullable=False)
    
    # Provider-specific IDs
    provider_payment_id = Column(String, nullable=True, index=True)  # Stripe payment_intent_id or PayPal order_id
    provider_charge_id = Column(String, nullable=True)  # Stripe charge_id
    
    # Payment metadata
    payment_method = Column(String, nullable=True)  # card, paypal, etc.
    payment_metadata = Column(JSON, nullable=True)  # Store provider-specific data
    
    # Failure information
    failure_code = Column(String, nullable=True)
    failure_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    succeeded_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    purchase = relationship("Purchase", back_populates="payment")
    user = relationship("User", back_populates="payments")
    refunds = relationship("Refund", back_populates="payment", cascade="all, delete-orphan")

class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    
    # Refund details
    amount = Column(Float, nullable=False)
    currency = Column(String, default="usd", nullable=False)
    status = Column(Enum(RefundStatus), default=RefundStatus.PENDING, nullable=False)
    reason = Column(String, nullable=True)  # duplicate, fraudulent, requested_by_customer
    
    # Provider-specific ID
    provider_refund_id = Column(String, nullable=True, index=True)
    
    # Refund metadata
    refund_metadata = Column(JSON, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Failure information
    failure_code = Column(String, nullable=True)
    failure_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    succeeded_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Admin who initiated the refund
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    payment = relationship("Payment", back_populates="refunds")
    admin = relationship("User", foreign_keys=[initiated_by])