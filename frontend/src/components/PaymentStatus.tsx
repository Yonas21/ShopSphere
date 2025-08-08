import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Payment {
  id: number;
  purchase_id: number;
  amount: number;
  currency: string;
  status: string;
  provider: string;
  provider_payment_id: string;
  created_at: string;
  updated_at?: string;
  succeeded_at?: string;
  failed_at?: string;
  failure_message?: string;
  refunds?: Refund[];
}

interface Refund {
  id: number;
  payment_id: number;
  amount: number;
  currency: string;
  status: string;
  reason?: string;
  admin_notes?: string;
  created_at: string;
  succeeded_at?: string;
  failed_at?: string;
}

interface PaymentStatusProps {
  paymentId?: number;
  purchaseId?: number;
  showRefunds?: boolean;
}

export const PaymentStatus: React.FC<PaymentStatusProps> = ({
  paymentId,
  purchaseId,
  showRefunds = true
}) => {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPayments();
  }, [paymentId, purchaseId]);

  const fetchPayments = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      let url = '';

      if (paymentId) {
        url = `http://localhost:8000/api/payments/${paymentId}`;
      } else if (purchaseId) {
        url = `http://localhost:8000/api/payments/purchase/${purchaseId}`;
      } else {
        url = 'http://localhost:8000/api/payments/';
      }

      const response = await axios.get(url, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      const data = Array.isArray(response.data) ? response.data : [response.data];
      setPayments(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch payment status');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'succeeded': return '#28a745';
      case 'processing': return '#ffc107';
      case 'pending': return '#17a2b8';
      case 'failed': return '#dc3545';
      case 'cancelled': return '#6c757d';
      case 'refunded': return '#fd7e14';
      case 'partially_refunded': return '#e83e8c';
      default: return '#6c757d';
    }
  };

  const getProviderLogo = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'stripe':
        return '💳';
      case 'paypal':
        return '🅿️';
      default:
        return '💰';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '20px' }}>
        <p>Loading payment status...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        backgroundColor: '#fee',
        color: '#c00',
        padding: '15px',
        borderRadius: '4px',
        textAlign: 'center'
      }}>
        {error}
      </div>
    );
  }

  if (!payments.length) {
    return (
      <div style={{ textAlign: 'center', padding: '20px' }}>
        <p>No payments found.</p>
      </div>
    );
  }

  return (
    <div>
      <h3 style={{ marginBottom: '20px' }}>Payment Status</h3>
      
      {payments.map((payment) => (
        <div
          key={payment.id}
          style={{
            border: '1px solid #ddd',
            borderRadius: '8px',
            padding: '15px',
            marginBottom: '15px',
            backgroundColor: '#fff'
          }}
        >
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '10px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '20px' }}>
                {getProviderLogo(payment.provider)}
              </span>
              <div>
                <strong>${payment.amount.toFixed(2)} {payment.currency.toUpperCase()}</strong>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  Payment #{payment.id}
                </div>
              </div>
            </div>
            
            <div style={{
              padding: '4px 12px',
              borderRadius: '20px',
              backgroundColor: getStatusColor(payment.status),
              color: 'white',
              fontSize: '12px',
              fontWeight: 'bold',
              textTransform: 'uppercase'
            }}>
              {payment.status.replace('_', ' ')}
            </div>
          </div>

          <div style={{ fontSize: '14px', color: '#666', marginBottom: '10px' }}>
            <div>Provider: {payment.provider.charAt(0).toUpperCase() + payment.provider.slice(1)}</div>
            <div>Created: {formatDate(payment.created_at)}</div>
            {payment.succeeded_at && (
              <div>Succeeded: {formatDate(payment.succeeded_at)}</div>
            )}
            {payment.failed_at && (
              <div>Failed: {formatDate(payment.failed_at)}</div>
            )}
          </div>

          {payment.failure_message && (
            <div style={{
              backgroundColor: '#fee',
              color: '#c00',
              padding: '8px',
              borderRadius: '4px',
              fontSize: '14px',
              marginBottom: '10px'
            }}>
              <strong>Error:</strong> {payment.failure_message}
            </div>
          )}

          {showRefunds && payment.refunds && payment.refunds.length > 0 && (
            <div style={{ marginTop: '15px' }}>
              <h4 style={{ marginBottom: '10px', fontSize: '16px' }}>Refunds</h4>
              {payment.refunds.map((refund) => (
                <div
                  key={refund.id}
                  style={{
                    backgroundColor: '#f8f9fa',
                    padding: '10px',
                    borderRadius: '4px',
                    marginBottom: '5px',
                    fontSize: '14px'
                  }}
                >
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <strong>-${refund.amount.toFixed(2)} {refund.currency.toUpperCase()}</strong>
                      {refund.reason && (
                        <span style={{ color: '#666', marginLeft: '10px' }}>
                          ({refund.reason.replace('_', ' ')})
                        </span>
                      )}
                    </div>
                    <div style={{
                      padding: '2px 8px',
                      borderRadius: '12px',
                      backgroundColor: getStatusColor(refund.status),
                      color: 'white',
                      fontSize: '10px',
                      fontWeight: 'bold',
                      textTransform: 'uppercase'
                    }}>
                      {refund.status}
                    </div>
                  </div>
                  
                  <div style={{ color: '#666', fontSize: '12px', marginTop: '5px' }}>
                    Created: {formatDate(refund.created_at)}
                    {refund.succeeded_at && (
                      <span> • Processed: {formatDate(refund.succeeded_at)}</span>
                    )}
                  </div>
                  
                  {refund.admin_notes && (
                    <div style={{
                      marginTop: '5px',
                      fontStyle: 'italic',
                      color: '#666'
                    }}>
                      Note: {refund.admin_notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          <div style={{
            marginTop: '10px',
            paddingTop: '10px',
            borderTop: '1px solid #eee',
            fontSize: '12px',
            color: '#666'
          }}>
            Transaction ID: {payment.provider_payment_id}
          </div>
        </div>
      ))}
    </div>
  );
};