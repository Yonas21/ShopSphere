from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from database.sql_database import get_db
from auth import get_current_user, require_admin
from models.user import User
from models.payment import PaymentStatus, PaymentProvider, RefundStatus
from schemas.payment import (
    PaymentCreate, PaymentUpdate, PaymentResponse, PaymentWithRefunds,
    RefundCreate, RefundUpdate, RefundResponse,
    PaymentIntentCreate, PaymentIntentResponse,
    PaymentSummary, StripeWebhookEvent, PayPalWebhookEvent
)
from crud.payment import payment_crud
from crud.item import get_purchase
from services.stripe_service import stripe_service
from services.paypal_service import paypal_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["payments"])

# Payment Intent Endpoints
@router.post("/intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    intent_data: PaymentIntentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a payment intent for a purchase"""
    # Verify purchase exists and belongs to current user
    purchase = get_purchase(db, intent_data.purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    if purchase.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to pay for this purchase")
    
    # Check if payment already exists
    existing_payments = payment_crud.get_payments_by_purchase(db, intent_data.purchase_id)
    if any(p.status == PaymentStatus.SUCCEEDED for p in existing_payments):
        raise HTTPException(status_code=400, detail="Purchase already paid")
    
    # Create payment record
    payment_create = PaymentCreate(
        purchase_id=intent_data.purchase_id,
        amount=purchase.total_price,
        provider=intent_data.provider,
        payment_method=intent_data.payment_method_type,
        metadata=intent_data.metadata or {}
    )
    
    payment = payment_crud.create_payment(db, payment_create, current_user.id)
    
    try:
        if intent_data.provider == PaymentProvider.STRIPE:
            # Create Stripe payment intent
            stripe_intent = stripe_service.create_payment_intent(
                amount=purchase.total_price,
                metadata={
                    "payment_id": str(payment.id),
                    "purchase_id": str(intent_data.purchase_id),
                    "user_id": str(current_user.id)
                }
            )
            
            # Update payment with Stripe intent ID
            payment_crud.update_payment_status(
                db, payment.id, PaymentStatus.PENDING,
                provider_payment_id=stripe_intent["id"]
            )
            
            return PaymentIntentResponse(
                payment_id=payment.id,
                client_secret=stripe_intent["client_secret"],
                provider_payment_id=stripe_intent["id"],
                amount=purchase.total_price,
                currency=stripe_intent["currency"],
                status=PaymentStatus.PENDING
            )
            
        elif intent_data.provider == PaymentProvider.PAYPAL:
            # Create PayPal order
            paypal_order = paypal_service.create_order(
                amount=purchase.total_price,
                return_url=intent_data.return_url,
                metadata={
                    "payment_id": str(payment.id),
                    "purchase_id": str(intent_data.purchase_id)
                }
            )
            
            # Update payment with PayPal order ID
            payment_crud.update_payment_status(
                db, payment.id, PaymentStatus.PENDING,
                provider_payment_id=paypal_order["id"]
            )
            
            return PaymentIntentResponse(
                payment_id=payment.id,
                approval_url=paypal_order["approval_url"],
                provider_payment_id=paypal_order["id"],
                amount=purchase.total_price,
                currency=paypal_order["currency"],
                status=PaymentStatus.PENDING
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported payment provider")
            
    except Exception as e:
        logger.error(f"Error creating payment intent: {e}")
        # Update payment status to failed
        payment_crud.update_payment_status(
            db, payment.id, PaymentStatus.FAILED,
            failure_message=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/confirm/{payment_id}")
async def confirm_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Confirm a payment (used for PayPal after user approval)"""
    payment = payment_crud.get_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        if payment.provider == PaymentProvider.PAYPAL:
            # Capture PayPal order
            capture_result = paypal_service.capture_order(payment.provider_payment_id)
            
            if capture_result["status"] == "COMPLETED":
                payment_crud.update_payment_status(
                    db, payment.id, PaymentStatus.SUCCEEDED
                )
                return {"status": "success", "message": "Payment confirmed"}
            else:
                payment_crud.update_payment_status(
                    db, payment.id, PaymentStatus.FAILED,
                    failure_message=f"PayPal capture failed: {capture_result['status']}"
                )
                raise HTTPException(status_code=400, detail="Payment confirmation failed")
        
        else:
            raise HTTPException(status_code=400, detail="Payment confirmation not supported for this provider")
            
    except Exception as e:
        logger.error(f"Error confirming payment: {e}")
        payment_crud.update_payment_status(
            db, payment.id, PaymentStatus.FAILED,
            failure_message=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

# Payment Management Endpoints
@router.get("/", response_model=List[PaymentResponse])
async def get_user_payments(
    status: Optional[PaymentStatus] = None,
    provider: Optional[PaymentProvider] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's payments"""
    payments = payment_crud.get_payments_by_user(
        db, current_user.id, status, provider, skip, limit
    )
    return payments

@router.get("/{payment_id}", response_model=PaymentWithRefunds)
async def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment details with refunds"""
    payment = payment_crud.get_payment_with_refunds(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return payment

@router.get("/purchase/{purchase_id}", response_model=List[PaymentResponse])
async def get_payments_by_purchase(
    purchase_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all payments for a specific purchase"""
    # Verify purchase belongs to user
    purchase = get_purchase(db, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    if purchase.customer_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    payments = payment_crud.get_payments_by_purchase(db, purchase_id)
    return payments

# Admin Payment Management
@router.get("/admin/all", response_model=List[PaymentResponse])
async def get_all_payments(
    status: Optional[PaymentStatus] = None,
    provider: Optional[PaymentProvider] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all payments (admin only)"""
    payments = payment_crud.get_all_payments(
        db, status, provider, start_date, end_date, skip, limit
    )
    return payments

@router.get("/admin/summary", response_model=PaymentSummary)
async def get_payment_summary(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get payment summary statistics (admin only)"""
    summary = payment_crud.get_payment_summary(db, start_date, end_date)
    return summary

# Refund Management
@router.post("/refunds", response_model=RefundResponse)
async def create_refund(
    refund_data: RefundCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a refund (admin only)"""
    # Verify payment exists
    payment = payment_crud.get_payment_by_id(db, refund_data.payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status != PaymentStatus.SUCCEEDED:
        raise HTTPException(status_code=400, detail="Cannot refund unsuccessful payment")
    
    # Check refundable amount
    refundable_amount = payment_crud.calculate_refundable_amount(db, refund_data.payment_id)
    if refund_data.amount > refundable_amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Refund amount exceeds refundable amount: {refundable_amount}"
        )
    
    # Create refund record
    refund = payment_crud.create_refund(db, refund_data, current_user.id)
    
    try:
        if payment.provider == PaymentProvider.STRIPE:
            # Create Stripe refund
            stripe_refund = stripe_service.create_refund(
                payment.provider_payment_id,
                amount=refund_data.amount,
                reason=refund_data.reason or "requested_by_customer",
                metadata={"refund_id": str(refund.id)}
            )
            
            # Update refund with Stripe refund ID
            payment_crud.update_refund_status(
                db, refund.id, RefundStatus.PENDING,
                provider_refund_id=stripe_refund["id"]
            )
            
        elif payment.provider == PaymentProvider.PAYPAL:
            # Find capture ID from payment metadata or charges
            capture_id = payment.provider_charge_id
            if not capture_id:
                raise HTTPException(status_code=400, detail="Cannot find PayPal capture ID for refund")
            
            # Create PayPal refund
            paypal_refund = paypal_service.create_refund(
                capture_id,
                amount=refund_data.amount,
                note_to_payer=refund_data.admin_notes,
                metadata={"refund_id": str(refund.id)}
            )
            
            # Update refund with PayPal refund ID
            payment_crud.update_refund_status(
                db, refund.id, RefundStatus.PENDING,
                provider_refund_id=paypal_refund["id"]
            )
        
        # Update payment status if fully refunded
        if refund_data.amount == refundable_amount:
            payment_crud.update_payment_status(
                db, payment.id, PaymentStatus.REFUNDED
            )
        elif refundable_amount - refund_data.amount < payment.amount:
            payment_crud.update_payment_status(
                db, payment.id, PaymentStatus.PARTIALLY_REFUNDED
            )
        
        return refund
        
    except Exception as e:
        logger.error(f"Error creating refund: {e}")
        # Update refund status to failed
        payment_crud.update_refund_status(
            db, refund.id, RefundStatus.FAILED,
            failure_message=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/refunds/{refund_id}", response_model=RefundResponse)
async def get_refund(
    refund_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get refund details"""
    refund = payment_crud.get_refund_by_id(db, refund_id)
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")
    
    # Check authorization
    payment = payment_crud.get_payment_by_id(db, refund.payment_id)
    if payment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return refund

@router.get("/admin/refunds", response_model=List[RefundResponse])
async def get_all_refunds(
    status: Optional[RefundStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all refunds (admin only)"""
    refunds = payment_crud.get_all_refunds(db, status, start_date, end_date, skip, limit)
    return refunds

# Webhook Endpoints
@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """Handle Stripe webhooks"""
    try:
        payload = await request.body()
        event = stripe_service.construct_webhook_event(payload, stripe_signature)
        
        logger.info(f"Received Stripe webhook: {event['type']}")
        
        if event['type'] == 'payment_intent.succeeded':
            # Update payment status
            payment_intent = event['data']['object']
            payment = payment_crud.get_payment_by_provider_id(db, payment_intent['id'])
            
            if payment:
                payment_crud.update_payment_status(
                    db, payment.id, PaymentStatus.SUCCEEDED,
                    provider_charge_id=payment_intent.get('charges', {}).get('data', [{}])[0].get('id')
                )
                
        elif event['type'] == 'payment_intent.payment_failed':
            # Update payment status
            payment_intent = event['data']['object']
            payment = payment_crud.get_payment_by_provider_id(db, payment_intent['id'])
            
            if payment:
                payment_crud.update_payment_status(
                    db, payment.id, PaymentStatus.FAILED,
                    failure_code=payment_intent.get('last_payment_error', {}).get('code'),
                    failure_message=payment_intent.get('last_payment_error', {}).get('message')
                )
                
        elif event['type'] == 'charge.dispute.created':
            # Handle disputes/chargebacks
            logger.warning(f"Dispute created for charge: {event['data']['object']['charge']}")
            
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhooks/paypal")
async def paypal_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle PayPal webhooks"""
    try:
        payload = await request.body()
        headers = dict(request.headers)
        
        # Verify webhook signature (basic implementation)
        if not paypal_service.verify_webhook_signature(headers, payload.decode(), "webhook_id"):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        event_data = json.loads(payload.decode())
        event_type = event_data.get('event_type')
        
        logger.info(f"Received PayPal webhook: {event_type}")
        
        if event_type == 'PAYMENT.CAPTURE.COMPLETED':
            # Update payment status
            resource = event_data['resource']
            custom_id = resource.get('custom_id')
            
            if custom_id:
                try:
                    purchase_id = int(custom_id)
                    payments = payment_crud.get_payments_by_purchase(db, purchase_id)
                    for payment in payments:
                        if payment.provider == PaymentProvider.PAYPAL and payment.status == PaymentStatus.PENDING:
                            payment_crud.update_payment_status(
                                db, payment.id, PaymentStatus.SUCCEEDED,
                                provider_charge_id=resource.get('id')
                            )
                            break
                except ValueError:
                    logger.warning(f"Invalid custom_id in PayPal webhook: {custom_id}")
                    
        elif event_type == 'PAYMENT.CAPTURE.DENIED':
            # Handle failed payment
            resource = event_data['resource']
            custom_id = resource.get('custom_id')
            
            if custom_id:
                try:
                    purchase_id = int(custom_id)
                    payments = payment_crud.get_payments_by_purchase(db, purchase_id)
                    for payment in payments:
                        if payment.provider == PaymentProvider.PAYPAL and payment.status == PaymentStatus.PENDING:
                            payment_crud.update_payment_status(
                                db, payment.id, PaymentStatus.FAILED,
                                failure_message="Payment denied by PayPal"
                            )
                            break
                except ValueError:
                    logger.warning(f"Invalid custom_id in PayPal webhook: {custom_id}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"PayPal webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))