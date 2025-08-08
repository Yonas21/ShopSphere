import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Payment {
  id: number;
  purchase_id: number;
  user_id: number;
  amount: number;
  currency: string;
  status: string;
  provider: string;
  provider_payment_id: string;
  created_at: string;
  succeeded_at?: string;
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
  failure_message?: string;
}

interface RefundFormData {
  amount: string;
  reason: string;
  admin_notes: string;
}

export const RefundManagement: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [refunds, setRefunds] = useState<Refund[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<'payments' | 'refunds'>('payments');
  const [showRefundModal, setShowRefundModal] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);
  const [refundForm, setRefundForm] = useState<RefundFormData>({
    amount: '',
    reason: 'requested_by_customer',
    admin_notes: ''
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchData();
  }, [selectedTab]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      
      if (selectedTab === 'payments') {
        const response = await axios.get(
          'http://localhost:8000/api/payments/admin/all?status=succeeded',
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        );
        setPayments(response.data);
      } else {
        const response = await axios.get(
          'http://localhost:8000/api/payments/admin/refunds',
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        );
        setRefunds(response.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const calculateRefundableAmount = (payment: Payment): number => {
    if (!payment.refunds) return payment.amount;
    
    const successfulRefunds = payment.refunds.filter(r => r.status === 'succeeded');
    const totalRefunded = successfulRefunds.reduce((sum, refund) => sum + refund.amount, 0);
    return Math.max(0, payment.amount - totalRefunded);
  };

  const handleRefundClick = (payment: Payment) => {
    const refundableAmount = calculateRefundableAmount(payment);
    if (refundableAmount <= 0) {
      alert('This payment has already been fully refunded.');
      return;
    }

    setSelectedPayment(payment);
    setRefundForm({
      amount: refundableAmount.toFixed(2),
      reason: 'requested_by_customer',
      admin_notes: ''
    });
    setShowRefundModal(true);
  };

  const handleRefundSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPayment) return;

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        'http://localhost:8000/api/payments/refunds',
        {
          payment_id: selectedPayment.id,
          amount: parseFloat(refundForm.amount),
          reason: refundForm.reason,
          admin_notes: refundForm.admin_notes || null
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      alert('Refund initiated successfully!');
      setShowRefundModal(false);
      setSelectedPayment(null);
      fetchData(); // Refresh data
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create refund');
    } finally {
      setSubmitting(false);
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '20px' }}>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <h2>Refund Management</h2>

      {/* Tab Navigation */}
      <div style={{ marginBottom: '20px', borderBottom: '1px solid #ddd' }}>
        <button
          onClick={() => setSelectedTab('payments')}
          style={{
            padding: '10px 20px',
            border: 'none',
            borderBottom: selectedTab === 'payments' ? '2px solid #007bff' : 'none',
            backgroundColor: 'transparent',
            cursor: 'pointer',
            fontWeight: selectedTab === 'payments' ? 'bold' : 'normal'
          }}
        >
          Payments ({payments.length})
        </button>
        <button
          onClick={() => setSelectedTab('refunds')}
          style={{
            padding: '10px 20px',
            border: 'none',
            borderBottom: selectedTab === 'refunds' ? '2px solid #007bff' : 'none',
            backgroundColor: 'transparent',
            cursor: 'pointer',
            fontWeight: selectedTab === 'refunds' ? 'bold' : 'normal'
          }}
        >
          Refunds ({refunds.length})
        </button>
      </div>

      {error && (
        <div style={{
          backgroundColor: '#fee',
          color: '#c00',
          padding: '15px',
          borderRadius: '4px',
          marginBottom: '20px'
        }}>
          {error}
        </div>
      )}

      {/* Payments Tab */}
      {selectedTab === 'payments' && (
        <div>
          <h3>Successful Payments</h3>
          {payments.length === 0 ? (
            <p>No successful payments found.</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa' }}>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>ID</th>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Amount</th>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Provider</th>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Date</th>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Status</th>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Refundable</th>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.map((payment) => {
                    const refundableAmount = calculateRefundableAmount(payment);
                    return (
                      <tr key={payment.id}>
                        <td style={{ padding: '12px', border: '1px solid #ddd' }}>#{payment.id}</td>
                        <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                          ${payment.amount.toFixed(2)} {payment.currency.toUpperCase()}
                        </td>
                        <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                          {payment.provider.charAt(0).toUpperCase() + payment.provider.slice(1)}
                        </td>
                        <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                          {formatDate(payment.created_at)}
                        </td>
                        <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                          <span style={{
                            padding: '4px 8px',
                            borderRadius: '12px',
                            backgroundColor: getStatusColor(payment.status),
                            color: 'white',
                            fontSize: '12px',
                            fontWeight: 'bold'
                          }}>
                            {payment.status.replace('_', ' ').toUpperCase()}
                          </span>
                        </td>
                        <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                          ${refundableAmount.toFixed(2)}
                        </td>
                        <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                          <button
                            onClick={() => handleRefundClick(payment)}
                            disabled={refundableAmount <= 0}
                            style={{
                              padding: '6px 12px',
                              border: 'none',
                              borderRadius: '4px',
                              backgroundColor: refundableAmount > 0 ? '#dc3545' : '#6c757d',
                              color: 'white',
                              cursor: refundableAmount > 0 ? 'pointer' : 'not-allowed',
                              fontSize: '12px'
                            }}
                          >
                            {refundableAmount > 0 ? 'Refund' : 'Fully Refunded'}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Refunds Tab */}
      {selectedTab === 'refunds' && (
        <div>
          <h3>All Refunds</h3>
          {refunds.length === 0 ? (
            <p>No refunds found.</p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa' }}>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>ID</th>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Amount</th>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Payment ID</th>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Reason</th>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Status</th>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Date</th>
                    <th style={{ padding: '12px', textAlign: 'left', border: '1px solid #ddd' }}>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {refunds.map((refund) => (
                    <tr key={refund.id}>
                      <td style={{ padding: '12px', border: '1px solid #ddd' }}>#{refund.id}</td>
                      <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                        ${refund.amount.toFixed(2)} {refund.currency.toUpperCase()}
                      </td>
                      <td style={{ padding: '12px', border: '1px solid #ddd' }}>#{refund.payment_id}</td>
                      <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                        {refund.reason?.replace('_', ' ') || 'N/A'}
                      </td>
                      <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                        <span style={{
                          padding: '4px 8px',
                          borderRadius: '12px',
                          backgroundColor: getStatusColor(refund.status),
                          color: 'white',
                          fontSize: '12px',
                          fontWeight: 'bold'
                        }}>
                          {refund.status.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                        {formatDate(refund.created_at)}
                      </td>
                      <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                        {refund.admin_notes || 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Refund Modal */}
      {showRefundModal && selectedPayment && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            width: '90%',
            maxWidth: '500px'
          }}>
            <h3>Create Refund</h3>
            <p>Payment #{selectedPayment.id} - ${selectedPayment.amount.toFixed(2)}</p>
            
            <form onSubmit={handleRefundSubmit}>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>
                  Refund Amount:
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  max={calculateRefundableAmount(selectedPayment)}
                  value={refundForm.amount}
                  onChange={(e) => setRefundForm({ ...refundForm, amount: e.target.value })}
                  required
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px'
                  }}
                />
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>
                  Reason:
                </label>
                <select
                  value={refundForm.reason}
                  onChange={(e) => setRefundForm({ ...refundForm, reason: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px'
                  }}
                >
                  <option value="requested_by_customer">Requested by Customer</option>
                  <option value="duplicate">Duplicate Payment</option>
                  <option value="fraudulent">Fraudulent</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px' }}>
                  Admin Notes:
                </label>
                <textarea
                  value={refundForm.admin_notes}
                  onChange={(e) => setRefundForm({ ...refundForm, admin_notes: e.target.value })}
                  rows={3}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    resize: 'vertical'
                  }}
                  placeholder="Optional notes about this refund..."
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  onClick={() => setShowRefundModal(false)}
                  disabled={submitting}
                  style={{
                    padding: '10px 20px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    backgroundColor: '#f8f9fa',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  style={{
                    padding: '10px 20px',
                    border: 'none',
                    borderRadius: '4px',
                    backgroundColor: '#dc3545',
                    color: 'white',
                    cursor: 'pointer'
                  }}
                >
                  {submitting ? 'Processing...' : 'Create Refund'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};