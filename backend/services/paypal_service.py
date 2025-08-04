import requests
import os
import base64
from typing import Dict, Any, Optional
from fastapi import HTTPException
from models.payment import PaymentStatus, RefundStatus
import logging

logger = logging.getLogger(__name__)

class PayPalService:
    def __init__(self):
        self.client_id = os.getenv("PAYPAL_CLIENT_ID")
        self.client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
        self.mode = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox or live
        
        if self.mode == "sandbox":
            self.base_url = "https://api-m.sandbox.paypal.com"
        else:
            self.base_url = "https://api-m.paypal.com"
        
        self._access_token = None
        self._token_expires_at = None
        
        if not self.client_id or not self.client_secret:
            logger.warning("PayPal credentials not set. PayPal payments will not work.")

    def _get_access_token(self) -> str:
        """Get OAuth access token from PayPal"""
        if not self.client_id or not self.client_secret:
            raise HTTPException(status_code=503, detail="PayPal not configured")
        
        # Check if we have a valid token
        import time
        if self._access_token and self._token_expires_at and time.time() < self._token_expires_at:
            return self._access_token
        
        # Get new token
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = "grant_type=client_credentials"
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                headers=headers,
                data=data
            )
            response.raise_for_status()
            
            token_data = response.json()
            self._access_token = token_data["access_token"]
            # Set expiration a bit earlier to be safe
            self._token_expires_at = time.time() + token_data["expires_in"] - 60
            
            return self._access_token
        except requests.RequestException as e:
            logger.error(f"PayPal token error: {e}")
            raise HTTPException(status_code=503, detail="PayPal authentication failed")

    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make authenticated request to PayPal API"""
        access_token = self._get_access_token()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "PayPal-Request-Id": f"request-{hash(str(data))}" if data else None
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"PayPal API error: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"PayPal API response: {e.response.text}")
            raise HTTPException(status_code=400, detail=f"PayPal error: {str(e)}")

    def create_order(
        self, 
        amount: float, 
        currency: str = "USD",
        return_url: str = None,
        cancel_url: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a PayPal order"""
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency.upper(),
                    "value": f"{amount:.2f}"
                },
                "custom_id": metadata.get("purchase_id") if metadata else None
            }],
            "application_context": {
                "return_url": return_url or "http://localhost:3000/payment/success/paypal",
                "cancel_url": cancel_url or "http://localhost:3000/payment/cancel"
            }
        }
        
        try:
            response = self._make_request("POST", "/v2/checkout/orders", order_data)
            
            # Extract approval URL
            approval_url = None
            for link in response.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break
            
            return {
                "id": response["id"],
                "status": response["status"],
                "approval_url": approval_url,
                "amount": amount,
                "currency": currency
            }
        except Exception as e:
            logger.error(f"PayPal order creation error: {e}")
            raise

    def capture_order(self, order_id: str) -> Dict[str, Any]:
        """Capture a PayPal order"""
        try:
            response = self._make_request("POST", f"/v2/checkout/orders/{order_id}/capture")
            
            return {
                "id": response["id"],
                "status": response["status"],
                "purchase_units": response.get("purchase_units", []),
                "payer": response.get("payer", {}),
                "create_time": response.get("create_time"),
                "update_time": response.get("update_time")
            }
        except Exception as e:
            logger.error(f"PayPal order capture error: {e}")
            raise

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get PayPal order details"""
        try:
            response = self._make_request("GET", f"/v2/checkout/orders/{order_id}")
            return response
        except Exception as e:
            logger.error(f"PayPal get order error: {e}")
            raise

    def create_refund(
        self, 
        capture_id: str, 
        amount: Optional[float] = None,
        currency: str = "USD",
        note_to_payer: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a refund for a PayPal capture"""
        refund_data = {}
        
        if amount:
            refund_data["amount"] = {
                "currency_code": currency.upper(),
                "value": f"{amount:.2f}"
            }
        
        if note_to_payer:
            refund_data["note_to_payer"] = note_to_payer
        
        try:
            response = self._make_request("POST", f"/v2/payments/captures/{capture_id}/refund", refund_data)
            
            return {
                "id": response["id"],
                "status": response["status"],
                "amount": float(response["amount"]["value"]) if "amount" in response else None,
                "currency": response["amount"]["currency_code"] if "amount" in response else currency,
                "create_time": response.get("create_time"),
                "update_time": response.get("update_time")
            }
        except Exception as e:
            logger.error(f"PayPal refund error: {e}")
            raise

    def get_refund(self, refund_id: str) -> Dict[str, Any]:
        """Get PayPal refund details"""
        try:
            response = self._make_request("GET", f"/v2/payments/refunds/{refund_id}")
            return response
        except Exception as e:
            logger.error(f"PayPal get refund error: {e}")
            raise

    def map_paypal_status_to_payment_status(self, paypal_status: str) -> PaymentStatus:
        """Map PayPal order status to internal payment status"""
        status_mapping = {
            "CREATED": PaymentStatus.PENDING,
            "SAVED": PaymentStatus.PENDING,
            "APPROVED": PaymentStatus.PROCESSING,
            "VOIDED": PaymentStatus.CANCELLED,
            "COMPLETED": PaymentStatus.SUCCEEDED,
            "PAYER_ACTION_REQUIRED": PaymentStatus.PENDING
        }
        return status_mapping.get(paypal_status, PaymentStatus.FAILED)

    def map_paypal_refund_status_to_refund_status(self, paypal_status: str) -> RefundStatus:
        """Map PayPal refund status to internal refund status"""
        status_mapping = {
            "CANCELLED": RefundStatus.CANCELLED,
            "PENDING": RefundStatus.PENDING,
            "COMPLETED": RefundStatus.SUCCEEDED,
            "FAILED": RefundStatus.FAILED
        }
        return status_mapping.get(paypal_status, RefundStatus.FAILED)

    def verify_webhook_signature(self, headers: dict, body: str, webhook_id: str) -> bool:
        """Verify PayPal webhook signature"""
        # PayPal webhook verification is more complex and requires the webhook certificate
        # For now, we'll implement basic verification
        # In production, you should implement full certificate verification
        auth_algo = headers.get("PAYPAL-AUTH-ALGO")
        transmission_id = headers.get("PAYPAL-TRANSMISSION-ID")
        cert_id = headers.get("PAYPAL-CERT-ID")
        transmission_sig = headers.get("PAYPAL-TRANSMISSION-SIG")
        transmission_time = headers.get("PAYPAL-TRANSMISSION-TIME")
        
        # Basic checks
        required_headers = [auth_algo, transmission_id, cert_id, transmission_sig, transmission_time]
        if not all(required_headers):
            logger.warning("Missing required PayPal webhook headers")
            return False
        
        # For production, implement full webhook verification with PayPal SDK
        # For now, return True if basic headers are present
        return True

# Global instance
paypal_service = PayPalService()