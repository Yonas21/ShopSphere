import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface PaymentCheckoutProps {
  purchaseId: number;
  amount: number;
  onPaymentSuccess: () => void;
  onPaymentCancel: () => void;
}

interface PaymentIntent {
  payment_id: number;
  client_secret?: string;
  approval_url?: string;
  provider_payment_id: string;
  amount: number;
  currency: string;
  status: string;
}

export const PaymentCheckout: React.FC<PaymentCheckoutProps> = ({
  purchaseId,
  amount,
  onPaymentSuccess,
  onPaymentCancel
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<'stripe' | 'paypal'>('stripe');
  const [paymentIntent, setPaymentIntent] = useState<PaymentIntent | null>(null);
  const [stripeLoaded, setStripeLoaded] = useState(false);

  // Load Stripe script
  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://js.stripe.com/v3/';
    script.onload = () => setStripeLoaded(true);
    document.head.appendChild(script);

    return () => {
      const existingScript = document.querySelector('script[src=\"https://js.stripe.com/v3/\"]');
      if (existingScript) {
        document.head.removeChild(existingScript);
      }
    };
  }, []);

  const createPaymentIntent = async (provider: 'stripe' | 'paypal') => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        'http://localhost:8000/api/payments/intent',
        {
          purchase_id: purchaseId,
          provider: provider,
          payment_method_type: 'card',
          return_url: `${window.location.origin}/payment/success/paypal`,
          metadata: {
            purchase_id: purchaseId.toString()
          }
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      setPaymentIntent(response.data);
      return response.data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to create payment intent';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleStripePayment = async () => {
    if (!stripeLoaded) {
      setError('Stripe is not loaded yet. Please try again.');
      return;
    }

    try {
      const intent = await createPaymentIntent('stripe');
      
      // Initialize Stripe
      const stripe = (window as any).Stripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);
      
      // Create card element or use Stripe's hosted checkout
      const { error } = await stripe.confirmPayment({
        clientSecret: intent.client_secret,
        confirmParams: {
          return_url: `${window.location.origin}/payment/success/stripe`,
        },
      });

      if (error) {
        setError(error.message || 'Payment failed');
      } else {
        onPaymentSuccess();
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handlePayPalPayment = async () => {
    try {
      const intent = await createPaymentIntent('paypal');
      
      if (intent.approval_url) {
        // Redirect to PayPal for approval
        window.location.href = intent.approval_url;
      } else {
        setError('Failed to get PayPal approval URL');
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handlePayment = () => {
    if (paymentMethod === 'stripe') {
      handleStripePayment();
    } else {
      handlePayPalPayment();
    }
  };

  return (
    <div style={{
      maxWidth: '400px',
      margin: '0 auto',
      padding: '20px',
      border: '1px solid #ddd',
      borderRadius: '8px',
      backgroundColor: '#fff'
    }}>
      <h3 style={{ textAlign: 'center', marginBottom: '20px' }}>
        Complete Payment
      </h3>
      
      <div style={{ marginBottom: '20px', textAlign: 'center' }}>
        <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#333' }}>
          ${amount.toFixed(2)}
        </p>
      </div>

      {error && (
        <div style={{
          backgroundColor: '#fee',
          color: '#c00',
          padding: '10px',
          borderRadius: '4px',
          marginBottom: '20px',
          textAlign: 'center'
        }}>
          {error}
        </div>
      )}

      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold' }}>
          Payment Method:
        </label>
        
        <div style={{ marginBottom: '10px' }}>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
            <input
              type="radio"
              value="stripe"
              checked={paymentMethod === 'stripe'}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPaymentMethod(e.target.value as 'stripe')}
              style={{ marginRight: '8px' }}
            />
            <span>Credit Card (Stripe)</span>
          </label>
        </div>
        
        <div>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
            <input
              type="radio"
              value="paypal"
              checked={paymentMethod === 'paypal'}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPaymentMethod(e.target.value as 'paypal')}
              style={{ marginRight: '8px' }}
            />
            <span>PayPal</span>
          </label>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '10px' }}>
        <button
          onClick={onPaymentCancel}
          disabled={loading}
          style={{
            flex: 1,
            padding: '12px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            backgroundColor: '#f5f5f5',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1
          }}
        >
          Cancel
        </button>
        
        <button
          onClick={handlePayment}
          disabled={loading || (paymentMethod === 'stripe' && !stripeLoaded)}
          style={{
            flex: 2,
            padding: '12px',
            border: 'none',
            borderRadius: '4px',
            backgroundColor: paymentMethod === 'stripe' ? '#5469d4' : '#ffc439',
            color: paymentMethod === 'stripe' ? 'white' : '#000',
            fontWeight: 'bold',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading || (paymentMethod === 'stripe' && !stripeLoaded) ? 0.6 : 1
          }}
        >
          {loading ? 'Processing...' : 
           paymentMethod === 'stripe' ? 'Pay with Stripe' : 'Pay with PayPal'}
        </button>
      </div>

      {paymentMethod === 'stripe' && !stripeLoaded && (
        <p style={{ textAlign: 'center', color: '#666', fontSize: '12px', marginTop: '10px' }}>
          Loading Stripe...
        </p>
      )}
    </div>
  );
};