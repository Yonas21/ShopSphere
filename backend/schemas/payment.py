from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from models.payment import PaymentStatus, PaymentProvider, RefundStatus

# Base payment schemas
class PaymentBase(BaseModel):
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="usd", description="Payment currency")
    provider: PaymentProvider = Field(..., description="Payment provider")
    payment_method: Optional[str] = Field(None, description="Payment method type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class PaymentCreate(PaymentBase):
    purchase_id: int = Field(..., description="Associated purchase ID")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        # Round to 2 decimal places to avoid floating point issues
        return round(v, 2)

class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    provider_payment_id: Optional[str] = None
    provider_charge_id: Optional[str] = None
    payment_method: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None
    succeeded_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

class PaymentResponse(PaymentBase):
    id: int
    purchase_id: int
    user_id: int
    status: PaymentStatus
    provider_payment_id: Optional[str] = None
    provider_charge_id: Optional[str] = None
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    succeeded_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Refund schemas
class RefundBase(BaseModel):
    amount: float = Field(..., gt=0, description="Refund amount")
    currency: str = Field(default="usd", description="Refund currency")
    reason: Optional[str] = Field(None, description="Refund reason")
    admin_notes: Optional[str] = Field(None, description="Admin notes")

class RefundCreate(RefundBase):
    payment_id: int = Field(..., description="Associated payment ID")
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Refund amount must be greater than 0')
        return round(v, 2)

class RefundUpdate(BaseModel):
    status: Optional[RefundStatus] = None
    provider_refund_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    admin_notes: Optional[str] = None
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None
    succeeded_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

class RefundResponse(RefundBase):
    id: int
    payment_id: int
    status: RefundStatus
    provider_refund_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    failure_code: Optional[str] = None
    failure_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    succeeded_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    initiated_by: Optional[int] = None
    
    class Config:
        from_attributes = True

# Payment intent schemas (for frontend integration)
class PaymentIntentCreate(BaseModel):
    purchase_id: int = Field(..., description="Purchase ID to create payment for")
    provider: PaymentProvider = Field(..., description="Payment provider")
    payment_method_type: Optional[str] = Field("card", description="Payment method type")
    return_url: Optional[str] = Field(None, description="Return URL for redirects")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class PaymentIntentResponse(BaseModel):
    payment_id: int
    client_secret: Optional[str] = None  # For Stripe
    approval_url: Optional[str] = None   # For PayPal
    provider_payment_id: str
    amount: float
    currency: str
    status: PaymentStatus

# Webhook schemas
class StripeWebhookEvent(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]
    created: int

class PayPalWebhookEvent(BaseModel):
    id: str
    event_type: str
    resource: Dict[str, Any]
    create_time: str

# Payment summary schemas
class PaymentSummary(BaseModel):
    total_payments: int
    total_amount: float
    successful_payments: int
    failed_payments: int
    pending_payments: int
    total_refunds: int
    total_refund_amount: float
    
class PaymentWithRefunds(PaymentResponse):
    refunds: List[RefundResponse] = []