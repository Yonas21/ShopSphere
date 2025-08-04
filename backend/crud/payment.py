from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from models.payment import Payment, Refund, PaymentStatus, PaymentProvider, RefundStatus
from models.item import Purchase
from schemas.payment import PaymentCreate, PaymentUpdate, RefundCreate, RefundUpdate
import logging

logger = logging.getLogger(__name__)

class PaymentCRUD:
    def create_payment(self, db: Session, payment: PaymentCreate, user_id: int) -> Payment:
        """Create a new payment record"""
        db_payment = Payment(
            purchase_id=payment.purchase_id,
            user_id=user_id,
            amount=payment.amount,
            currency=payment.currency,
            provider=payment.provider,
            payment_method=payment.payment_method,
            metadata=payment.metadata
        )
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        return db_payment

    def get_payment_by_id(self, db: Session, payment_id: int) -> Optional[Payment]:
        """Get payment by ID"""
        return db.query(Payment).filter(Payment.id == payment_id).first()

    def get_payment_by_provider_id(self, db: Session, provider_payment_id: str) -> Optional[Payment]:
        """Get payment by provider payment ID"""
        return db.query(Payment).filter(
            Payment.provider_payment_id == provider_payment_id
        ).first()

    def get_payments_by_user(
        self, 
        db: Session, 
        user_id: int, 
        status: Optional[PaymentStatus] = None,
        provider: Optional[PaymentProvider] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Payment]:
        """Get payments by user with optional filtering"""
        query = db.query(Payment).filter(Payment.user_id == user_id)
        
        if status:
            query = query.filter(Payment.status == status)
        if provider:
            query = query.filter(Payment.provider == provider)
        
        return query.order_by(desc(Payment.created_at)).offset(skip).limit(limit).all()

    def get_payments_by_purchase(self, db: Session, purchase_id: int) -> List[Payment]:
        """Get all payments for a specific purchase"""
        return db.query(Payment).filter(Payment.purchase_id == purchase_id).all()

    def update_payment(self, db: Session, payment_id: int, payment_update: PaymentUpdate) -> Optional[Payment]:
        """Update payment record"""
        db_payment = self.get_payment_by_id(db, payment_id)
        if not db_payment:
            return None
        
        update_data = payment_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_payment, field, value)
        
        db.commit()
        db.refresh(db_payment)
        return db_payment

    def update_payment_status(
        self, 
        db: Session, 
        payment_id: int, 
        status: PaymentStatus,
        provider_payment_id: Optional[str] = None,
        provider_charge_id: Optional[str] = None,
        failure_code: Optional[str] = None,
        failure_message: Optional[str] = None
    ) -> Optional[Payment]:
        """Update payment status with related fields"""
        db_payment = self.get_payment_by_id(db, payment_id)
        if not db_payment:
            return None
        
        db_payment.status = status
        if provider_payment_id:
            db_payment.provider_payment_id = provider_payment_id
        if provider_charge_id:
            db_payment.provider_charge_id = provider_charge_id
        if failure_code:
            db_payment.failure_code = failure_code
        if failure_message:
            db_payment.failure_message = failure_message
        
        # Set timestamp based on status
        now = datetime.utcnow()
        if status == PaymentStatus.SUCCEEDED:
            db_payment.succeeded_at = now
        elif status in [PaymentStatus.FAILED, PaymentStatus.CANCELLED]:
            db_payment.failed_at = now
        
        db.commit()
        db.refresh(db_payment)
        return db_payment

    def get_all_payments(
        self, 
        db: Session, 
        status: Optional[PaymentStatus] = None,
        provider: Optional[PaymentProvider] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Payment]:
        """Get all payments with filtering (admin only)"""
        query = db.query(Payment)
        
        if status:
            query = query.filter(Payment.status == status)
        if provider:
            query = query.filter(Payment.provider == provider)
        if start_date:
            query = query.filter(Payment.created_at >= start_date)
        if end_date:
            query = query.filter(Payment.created_at <= end_date)
        
        return query.order_by(desc(Payment.created_at)).offset(skip).limit(limit).all()

    # Refund operations
    def create_refund(self, db: Session, refund: RefundCreate, initiated_by: int) -> Refund:
        """Create a new refund record"""
        db_refund = Refund(
            payment_id=refund.payment_id,
            amount=refund.amount,
            currency=refund.currency,
            reason=refund.reason,
            admin_notes=refund.admin_notes,
            initiated_by=initiated_by
        )
        db.add(db_refund)
        db.commit()
        db.refresh(db_refund)
        return db_refund

    def get_refund_by_id(self, db: Session, refund_id: int) -> Optional[Refund]:
        """Get refund by ID"""
        return db.query(Refund).filter(Refund.id == refund_id).first()

    def get_refund_by_provider_id(self, db: Session, provider_refund_id: str) -> Optional[Refund]:
        """Get refund by provider refund ID"""
        return db.query(Refund).filter(
            Refund.provider_refund_id == provider_refund_id
        ).first()

    def get_refunds_by_payment(self, db: Session, payment_id: int) -> List[Refund]:
        """Get all refunds for a specific payment"""
        return db.query(Refund).filter(Refund.payment_id == payment_id).all()

    def update_refund(self, db: Session, refund_id: int, refund_update: RefundUpdate) -> Optional[Refund]:
        """Update refund record"""
        db_refund = self.get_refund_by_id(db, refund_id)
        if not db_refund:
            return None
        
        update_data = refund_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_refund, field, value)
        
        db.commit()
        db.refresh(db_refund)
        return db_refund

    def update_refund_status(
        self, 
        db: Session, 
        refund_id: int, 
        status: RefundStatus,
        provider_refund_id: Optional[str] = None,
        failure_code: Optional[str] = None,
        failure_message: Optional[str] = None
    ) -> Optional[Refund]:
        """Update refund status with related fields"""
        db_refund = self.get_refund_by_id(db, refund_id)
        if not db_refund:
            return None
        
        db_refund.status = status
        if provider_refund_id:
            db_refund.provider_refund_id = provider_refund_id
        if failure_code:
            db_refund.failure_code = failure_code
        if failure_message:
            db_refund.failure_message = failure_message
        
        # Set timestamp based on status
        now = datetime.utcnow()
        if status == RefundStatus.SUCCEEDED:
            db_refund.succeeded_at = now
        elif status in [RefundStatus.FAILED, RefundStatus.CANCELLED]:
            db_refund.failed_at = now
        
        db.commit()
        db.refresh(db_refund)
        return db_refund

    def get_all_refunds(
        self, 
        db: Session, 
        status: Optional[RefundStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Refund]:
        """Get all refunds with filtering (admin only)"""
        query = db.query(Refund)
        
        if status:
            query = query.filter(Refund.status == status)
        if start_date:
            query = query.filter(Refund.created_at >= start_date)
        if end_date:
            query = query.filter(Refund.created_at <= end_date)
        
        return query.order_by(desc(Refund.created_at)).offset(skip).limit(limit).all()

    # Analytics and reporting
    def get_payment_summary(
        self, 
        db: Session, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get payment summary statistics"""
        query = db.query(Payment)
        refund_query = db.query(Refund)
        
        if start_date:
            query = query.filter(Payment.created_at >= start_date)
            refund_query = refund_query.filter(Refund.created_at >= start_date)
        if end_date:
            query = query.filter(Payment.created_at <= end_date)
            refund_query = refund_query.filter(Refund.created_at <= end_date)
        
        # Payment statistics
        total_payments = query.count()
        successful_payments = query.filter(Payment.status == PaymentStatus.SUCCEEDED).count()
        failed_payments = query.filter(Payment.status == PaymentStatus.FAILED).count()
        pending_payments = query.filter(Payment.status == PaymentStatus.PENDING).count()
        
        # Calculate total amount
        total_amount_result = query.filter(Payment.status == PaymentStatus.SUCCEEDED).with_entities(
            func.sum(Payment.amount)
        ).scalar()
        total_amount = float(total_amount_result) if total_amount_result else 0.0
        
        # Refund statistics
        total_refunds = refund_query.count()
        total_refund_amount_result = refund_query.filter(Refund.status == RefundStatus.SUCCEEDED).with_entities(
            func.sum(Refund.amount)
        ).scalar()
        total_refund_amount = float(total_refund_amount_result) if total_refund_amount_result else 0.0
        
        return {
            "total_payments": total_payments,
            "total_amount": total_amount,
            "successful_payments": successful_payments,
            "failed_payments": failed_payments,
            "pending_payments": pending_payments,
            "total_refunds": total_refunds,
            "total_refund_amount": total_refund_amount
        }

    def get_payment_with_refunds(self, db: Session, payment_id: int) -> Optional[Payment]:
        """Get payment with all its refunds"""
        return db.query(Payment).filter(Payment.id == payment_id).first()

    def calculate_refundable_amount(self, db: Session, payment_id: int) -> float:
        """Calculate how much can still be refunded for a payment"""
        payment = self.get_payment_by_id(db, payment_id)
        if not payment or payment.status != PaymentStatus.SUCCEEDED:
            return 0.0
        
        # Calculate total successful refunds
        successful_refunds = db.query(func.sum(Refund.amount)).filter(
            and_(Refund.payment_id == payment_id, Refund.status == RefundStatus.SUCCEEDED)
        ).scalar()
        
        refunded_amount = float(successful_refunds) if successful_refunds else 0.0
        return max(0.0, payment.amount - refunded_amount)

# Global instance
payment_crud = PaymentCRUD()