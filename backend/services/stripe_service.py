import stripe
import os
from typing import Dict, Any, Optional
from fastapi import HTTPException
from models.payment import Payment, Refund, PaymentStatus, RefundStatus
from schemas.payment import PaymentIntentCreate, PaymentIntentResponse
import logging

logger = logging.getLogger(__name__)

class StripeService:
    def __init__(self):
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        
        if not self.api_key:
            logger.warning("STRIPE_SECRET_KEY not set. Stripe payments will not work.")
        else:
            stripe.api_key = self.api_key

    def create_payment_intent(
        self, 
        amount: float, 
        currency: str = "usd",
        payment_method_types: list = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a Stripe PaymentIntent"""
        if not self.api_key:
            raise HTTPException(status_code=503, detail="Stripe not configured")
        
        if payment_method_types is None:
            payment_method_types = ["card"]
        
        try:
            # Convert amount to cents (Stripe expects amounts in smallest currency unit)
            amount_cents = int(amount * 100)
            
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                payment_method_types=payment_method_types,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True}
            )
            
            return {
                "id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status,
                "amount": amount,
                "currency": currency
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

    def confirm_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm a payment intent (usually done by frontend)"""
        if not self.api_key:
            raise HTTPException(status_code=503, detail="Stripe not configured")
        
        try:
            intent = stripe.PaymentIntent.confirm(payment_intent_id)
            return {
                "id": intent.id,
                "status": intent.status,
                "amount": intent.amount / 100,  # Convert back from cents
                "currency": intent.currency,
                "charges": intent.charges.data if intent.charges else []
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment: {e}")
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

    def retrieve_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """Get payment intent details"""
        if not self.api_key:
            raise HTTPException(status_code=503, detail="Stripe not configured")
        
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                "id": intent.id,
                "status": intent.status,
                "amount": intent.amount / 100,
                "currency": intent.currency,
                "payment_method": intent.payment_method,
                "charges": intent.charges.data if intent.charges else []
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving payment: {e}")
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

    def create_refund(
        self, 
        payment_intent_id: str, 
        amount: Optional[float] = None,
        reason: str = "requested_by_customer",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a refund for a payment"""
        if not self.api_key:
            raise HTTPException(status_code=503, detail="Stripe not configured")
        
        try:
            # Get the payment intent to find the charge
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if not intent.charges.data:
                raise HTTPException(status_code=400, detail="No charges found for this payment")
            
            charge_id = intent.charges.data[0].id
            refund_data = {
                "charge": charge_id,
                "reason": reason,
                "metadata": metadata or {}
            }
            
            if amount:
                # Convert to cents
                refund_data["amount"] = int(amount * 100)
            
            refund = stripe.Refund.create(**refund_data)
            
            return {
                "id": refund.id,
                "status": refund.status,
                "amount": refund.amount / 100,
                "currency": refund.currency,
                "reason": refund.reason,
                "charge": refund.charge
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating refund: {e}")
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

    def retrieve_refund(self, refund_id: str) -> Dict[str, Any]:
        """Get refund details"""
        if not self.api_key:
            raise HTTPException(status_code=503, detail="Stripe not configured")
        
        try:
            refund = stripe.Refund.retrieve(refund_id)
            return {
                "id": refund.id,
                "status": refund.status,
                "amount": refund.amount / 100,
                "currency": refund.currency,
                "reason": refund.reason,
                "charge": refund.charge
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving refund: {e}")
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

    def construct_webhook_event(self, payload: bytes, sig_header: str):
        """Construct and verify webhook event"""
        if not self.webhook_secret:
            raise HTTPException(status_code=503, detail="Stripe webhook secret not configured")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")

    def map_stripe_status_to_payment_status(self, stripe_status: str) -> PaymentStatus:
        """Map Stripe payment intent status to internal payment status"""
        status_mapping = {
            "requires_payment_method": PaymentStatus.PENDING,
            "requires_confirmation": PaymentStatus.PENDING,
            "requires_action": PaymentStatus.PENDING,
            "processing": PaymentStatus.PROCESSING,
            "requires_capture": PaymentStatus.PROCESSING,
            "succeeded": PaymentStatus.SUCCEEDED,
            "canceled": PaymentStatus.CANCELLED
        }
        return status_mapping.get(stripe_status, PaymentStatus.FAILED)

    def map_stripe_refund_status_to_refund_status(self, stripe_status: str) -> RefundStatus:
        """Map Stripe refund status to internal refund status"""
        status_mapping = {
            "pending": RefundStatus.PENDING,
            "succeeded": RefundStatus.SUCCEEDED,
            "failed": RefundStatus.FAILED,
            "canceled": RefundStatus.CANCELLED
        }
        return status_mapping.get(stripe_status, RefundStatus.FAILED)

# Global instance
stripe_service = StripeService()