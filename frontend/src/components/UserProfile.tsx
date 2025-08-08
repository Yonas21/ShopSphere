import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PaymentStatus } from './PaymentStatus';

interface User {
  id: number;
  email: string;
  username: string;
  role: 'customer' | 'admin';
  is_active: boolean;
}

interface Purchase {
  id: number;
  item_id: number;
  quantity: number;
  total_price: number;
  status: string;
  status_updated_at: string;
  tracking_number?: string;
  notes?: string;
  purchase_date: string;
  item_name?: string;
  customer_username?: string;
}

interface UserProfileProps {
  token: string;
  currentUser: User;
  isOpen: boolean;
  onClose: () => void;
  onUserUpdate: (user: User) => void;
}

const UserProfile: React.FC<UserProfileProps> = ({ 
  token, 
  currentUser, 
  isOpen, 
  onClose, 
  onUserUpdate 
}) => {
  const [activeTab, setActiveTab] = useState<'profile' | 'password' | 'orders' | 'payments'>('profile');
  const [loading, setLoading] = useState(false);
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  
  // Profile form state
  const [profileForm, setProfileForm] = useState({
    email: currentUser.email || '',
    username: currentUser.username || ''
  });
  
  // Password form state
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });

  const API_BASE_URL = 'http://localhost:8000';

  const getStatusColor = (status: string) => {
    const colors: { [key: string]: { bg: string; text: string } } = {
      pending: { bg: '#fef3c7', text: '#92400e' },
      confirmed: { bg: '#dbeafe', text: '#1e40af' },
      processing: { bg: '#f3e8ff', text: '#7c3aed' },
      shipped: { bg: '#dcfce7', text: '#166534' },
      delivered: { bg: '#d1fae5', text: '#065f46' },
      cancelled: { bg: '#fee2e2', text: '#991b1b' }
    };
    return colors[status] || { bg: '#f3f4f6', text: '#374151' };
  };

  const getStatusIcon = (status: string) => {
    const icons: { [key: string]: string } = {
      pending: '⏳',
      confirmed: '✅',
      processing: '🔄',
      shipped: '🚚',
      delivered: '📦',
      cancelled: '❌'
    };
    return icons[status] || '❓';
  };

  useEffect(() => {
    if (isOpen) {
      setProfileForm({
        email: currentUser.email || '',
        username: currentUser.username || ''
      });
      if (activeTab === 'orders') {
        fetchPurchases();
      }
    }
  }, [isOpen, currentUser, activeTab]);

  const fetchPurchases = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/items/purchases/my`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPurchases(response.data);
    } catch (error) {
      console.error('Error fetching purchases:', error);
    }
  };

  const updateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.put(
        `${API_BASE_URL}/api/users/profile`,
        {
          email: profileForm.email !== currentUser.email ? profileForm.email : undefined,
          username: profileForm.username !== currentUser.username ? profileForm.username : undefined
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      onUserUpdate(response.data);
      alert('✅ Profile updated successfully!');
    } catch (error: any) {
      alert(`❌ Error: ${error.response?.data?.detail || 'Failed to update profile'}`);
    } finally {
      setLoading(false);
    }
  };

  const changePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      alert('❌ New passwords do not match');
      return;
    }
    
    if (passwordForm.new_password.length < 6) {
      alert('❌ New password must be at least 6 characters long');
      return;
    }
    
    setLoading(true);
    
    try {
      await axios.post(
        `${API_BASE_URL}/api/users/change-password`,
        {
          current_password: passwordForm.current_password,
          new_password: passwordForm.new_password
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setPasswordForm({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
      
      alert('✅ Password changed successfully!');
    } catch (error: any) {
      alert(`❌ Error: ${error.response?.data?.detail || 'Failed to change password'}`);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const tabButtonStyle = (tabName: string) => ({
    padding: '0.75rem 1.5rem',
    border: 'none',
    background: activeTab === tabName ? '#667eea' : 'transparent',
    color: activeTab === tabName ? 'white' : '#64748b',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: '500',
    fontSize: '0.95rem',
    transition: 'all 0.2s ease',
    marginRight: '0.5rem'
  });

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      zIndex: 2000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{
        width: '90%',
        maxWidth: '800px',
        maxHeight: '90%',
        backgroundColor: 'white',
        borderRadius: '20px',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.15)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: '2rem',
          borderBottom: '1px solid #e5e7eb',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h2 style={{ 
              margin: 0, 
              fontSize: '1.8rem', 
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              👤 My Profile
            </h2>
            <p style={{ 
              margin: '0.5rem 0 0 0', 
              opacity: 0.9,
              fontSize: '1rem'
            }}>
              Manage your account settings and preferences
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.2)',
              border: 'none',
              color: 'white',
              fontSize: '1.5rem',
              cursor: 'pointer',
              padding: '0.5rem',
              borderRadius: '8px',
              width: '40px',
              height: '40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            ✕
          </button>
        </div>

        {/* Navigation Tabs */}
        <div style={{
          padding: '1.5rem 2rem 0 2rem',
          borderBottom: '1px solid #f1f5f9'
        }}>
          <button style={tabButtonStyle('profile')} onClick={() => setActiveTab('profile')}>
            ✏️ Edit Profile
          </button>
          <button style={tabButtonStyle('password')} onClick={() => setActiveTab('password')}>
            🔒 Change Password
          </button>
          <button style={tabButtonStyle('orders')} onClick={() => setActiveTab('orders')}>
            📦 Order History ({purchases.length})
          </button>
          <button style={tabButtonStyle('payments')} onClick={() => setActiveTab('payments')}>
            💳 Payments
          </button>
        </div>

        {/* Content */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '2rem'
        }}>
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div>
              <h3 style={{ 
                margin: '0 0 1.5rem 0', 
                fontSize: '1.3rem', 
                fontWeight: '600', 
                color: '#1e293b' 
              }}>
                Profile Information
              </h3>
              
              <form onSubmit={updateProfile}>
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: '1fr 1fr', 
                  gap: '1.5rem', 
                  marginBottom: '2rem' 
                }}>
                  <div>
                    <label style={{ 
                      display: 'block', 
                      marginBottom: '0.5rem', 
                      fontWeight: '500', 
                      color: '#374151' 
                    }}>
                      Username
                    </label>
                    <input
                      type="text"
                      value={profileForm.username}
                      onChange={(e) => setProfileForm({ ...profileForm, username: e.target.value })}
                      required
                      style={{ 
                        width: '100%', 
                        padding: '0.75rem', 
                        border: '2px solid #e5e7eb', 
                        borderRadius: '8px',
                        fontSize: '1rem',
                        transition: 'border-color 0.2s ease'
                      }}
                      onFocus={(e) => e.target.style.borderColor = '#667eea'}
                      onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                    />
                  </div>
                  
                  <div>
                    <label style={{ 
                      display: 'block', 
                      marginBottom: '0.5rem', 
                      fontWeight: '500', 
                      color: '#374151' 
                    }}>
                      Email
                    </label>
                    <input
                      type="email"
                      value={profileForm.email}
                      onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                      required
                      style={{ 
                        width: '100%', 
                        padding: '0.75rem', 
                        border: '2px solid #e5e7eb', 
                        borderRadius: '8px',
                        fontSize: '1rem',
                        transition: 'border-color 0.2s ease'
                      }}
                      onFocus={(e) => e.target.style.borderColor = '#667eea'}
                      onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                    />
                  </div>
                </div>

                <div style={{
                  background: '#f8fafc',
                  padding: '1.5rem',
                  borderRadius: '12px',
                  marginBottom: '2rem'
                }}>
                  <h4 style={{ margin: '0 0 1rem 0', color: '#374151' }}>Account Details</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div>
                      <span style={{ color: '#64748b', fontSize: '0.9rem' }}>Role:</span>
                      <p style={{ margin: '0.25rem 0 0 0', fontWeight: '600', color: '#374151', textTransform: 'capitalize' }}>
                        {currentUser.role}
                      </p>
                    </div>
                    <div>
                      <span style={{ color: '#64748b', fontSize: '0.9rem' }}>Status:</span>
                      <p style={{ margin: '0.25rem 0 0 0', fontWeight: '600', color: currentUser.is_active ? '#059669' : '#dc2626' }}>
                        {currentUser.is_active ? 'Active' : 'Inactive'}
                      </p>
                    </div>
                  </div>
                </div>

                <button 
                  type="submit"
                  disabled={loading}
                  style={{ 
                    background: loading ? '#9ca3af' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '0.875rem 2rem',
                    fontSize: '1rem',
                    fontWeight: '600',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s ease',
                    boxShadow: loading ? 'none' : '0 4px 12px rgba(102, 126, 234, 0.4)'
                  }}
                >
                  {loading ? '⏳ Updating...' : '✨ Update Profile'}
                </button>
              </form>
            </div>
          )}

          {/* Password Tab */}
          {activeTab === 'password' && (
            <div>
              <h3 style={{ 
                margin: '0 0 1.5rem 0', 
                fontSize: '1.3rem', 
                fontWeight: '600', 
                color: '#1e293b' 
              }}>
                Change Password
              </h3>
              
              <form onSubmit={changePassword}>
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ 
                    display: 'block', 
                    marginBottom: '0.5rem', 
                    fontWeight: '500', 
                    color: '#374151' 
                  }}>
                    Current Password
                  </label>
                  <input
                    type="password"
                    value={passwordForm.current_password}
                    onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                    required
                    style={{ 
                      width: '100%', 
                      padding: '0.75rem', 
                      border: '2px solid #e5e7eb', 
                      borderRadius: '8px',
                      fontSize: '1rem',
                      transition: 'border-color 0.2s ease'
                    }}
                    onFocus={(e) => e.target.style.borderColor = '#667eea'}
                    onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                  />
                </div>

                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: '1fr 1fr', 
                  gap: '1rem', 
                  marginBottom: '2rem' 
                }}>
                  <div>
                    <label style={{ 
                      display: 'block', 
                      marginBottom: '0.5rem', 
                      fontWeight: '500', 
                      color: '#374151' 
                    }}>
                      New Password
                    </label>
                    <input
                      type="password"
                      value={passwordForm.new_password}
                      onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                      required
                      minLength={6}
                      style={{ 
                        width: '90%', 
                        padding: '0.75rem', 
                        border: '2px solid #e5e7eb', 
                        borderRadius: '8px',
                        fontSize: '1rem',
                        transition: 'border-color 0.2s ease'
                      }}
                      onFocus={(e) => e.target.style.borderColor = '#667eea'}
                      onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
                    />
                  </div>
                  <div>
                    <label style={{ 
                      display: 'block', 
                      marginBottom: '0.5rem', 
                      fontWeight: '500', 
                      color: '#374151' 
                    }}>
                      Confirm New Password
                    </label>
                    <input
                      type="password"
                      value={passwordForm.confirm_password}
                      onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                      required
                      minLength={6}
                      style={{ 
                        width: '90%', 
                        padding: '0.75rem', 
                        border: `2px solid ${passwordForm.new_password && passwordForm.confirm_password && passwordForm.new_password !== passwordForm.confirm_password ? '#ef4444' : '#e5e7eb'}`, 
                        borderRadius: '8px',
                        fontSize: '1rem',
                        transition: 'border-color 0.2s ease'
                      }}
                      onFocus={(e) => e.target.style.borderColor = '#667eea'}
                      onBlur={(e) => e.target.style.borderColor = passwordForm.new_password && passwordForm.confirm_password && passwordForm.new_password !== passwordForm.confirm_password ? '#ef4444' : '#e5e7eb'}
                    />
                    {passwordForm.new_password && passwordForm.confirm_password && passwordForm.new_password !== passwordForm.confirm_password && (
                      <span style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '0.25rem', display: 'block' }}>
                        Passwords do not match
                      </span>
                    )}
                  </div>
                </div>

                <div style={{
                  background: '#fef3c7',
                  border: '1px solid #fcd34d',
                  borderRadius: '8px',
                  padding: '1rem',
                  marginBottom: '2rem'
                }}>
                  <p style={{ margin: 0, color: '#92400e', fontSize: '0.9rem' }}>
                    💡 Password must be at least 6 characters long
                  </p>
                </div>

                <button 
                  type="submit"
                  disabled={loading || !!(passwordForm.new_password && passwordForm.confirm_password && passwordForm.new_password !== passwordForm.confirm_password)}
                  style={{ 
                    background: loading ? '#9ca3af' : 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '0.875rem 2rem',
                    fontSize: '1rem',
                    fontWeight: '600',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s ease',
                    boxShadow: loading ? 'none' : '0 4px 12px rgba(220, 38, 38, 0.4)'
                  }}
                >
                  {loading ? '⏳ Changing...' : '🔒 Change Password'}
                </button>
              </form>
            </div>
          )}

          {/* Orders Tab */}
          {activeTab === 'orders' && (
            <div>
              <h3 style={{ 
                margin: '0 0 1.5rem 0', 
                fontSize: '1.3rem', 
                fontWeight: '600', 
                color: '#1e293b' 
              }}>
                Order History
              </h3>
              
              {purchases.length === 0 ? (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '3rem',
                  color: '#64748b'
                }}>
                  <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>📦</div>
                  <h4 style={{ color: '#64748b', fontWeight: '500' }}>No orders yet</h4>
                  <p>Your purchase history will appear here.</p>
                </div>
              ) : (
                <div style={{ 
                  display: 'grid', 
                  gap: '1rem' 
                }}>
                  {purchases.map((purchase) => {
                    const statusColor = getStatusColor(purchase.status);
                    return (
                      <div key={purchase.id} style={{
                        background: '#f8fafc',
                        borderRadius: '12px',
                        padding: '1.5rem',
                        border: '1px solid #e2e8f0'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                          <div style={{ flex: 1 }}>
                            <h4 style={{ 
                              margin: '0 0 0.5rem 0', 
                              fontSize: '1.1rem', 
                              fontWeight: '600', 
                              color: '#1e293b'
                            }}>
                              {purchase.item_name}
                            </h4>
                            <p style={{ 
                              margin: '0 0 0.5rem 0', 
                              color: '#64748b',
                              fontSize: '0.9rem'
                            }}>
                              Order #{purchase.id.toString().padStart(6, '0')} • Quantity: {purchase.quantity}
                            </p>
                            <p style={{ 
                              margin: 0, 
                              color: '#64748b',
                              fontSize: '0.85rem'
                            }}>
                              Ordered: {new Date(purchase.purchase_date).toLocaleDateString('en-US', {
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric'
                              })}
                            </p>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <div style={{ 
                              fontSize: '1.3rem', 
                              fontWeight: '700', 
                              color: '#059669',
                              marginBottom: '0.5rem'
                            }}>
                              ${purchase.total_price.toFixed(2)}
                            </div>
                            <span style={{
                              background: statusColor.bg,
                              color: statusColor.text,
                              padding: '0.5rem 0.75rem',
                              borderRadius: '20px',
                              fontSize: '0.8rem',
                              fontWeight: '600',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.25rem'
                            }}>
                              {getStatusIcon(purchase.status)} {purchase.status.charAt(0).toUpperCase() + purchase.status.slice(1)}
                            </span>
                          </div>
                        </div>
                        
                        {/* Tracking Information */}
                        {(purchase.tracking_number || purchase.notes) && (
                          <div style={{
                            background: '#ffffff',
                            borderRadius: '8px',
                            padding: '1rem',
                            border: '1px solid #e5e7eb',
                            marginTop: '0.5rem'
                          }}>
                            {purchase.tracking_number && (
                              <div style={{ marginBottom: purchase.notes ? '0.5rem' : 0 }}>
                                <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: '600' }}>
                                  Tracking: 
                                </span>
                                <span style={{ 
                                  fontSize: '0.9rem', 
                                  color: '#374151', 
                                  fontFamily: 'monospace',
                                  marginLeft: '0.5rem',
                                  background: '#f3f4f6',
                                  padding: '0.25rem 0.5rem',
                                  borderRadius: '4px'
                                }}>
                                  {purchase.tracking_number}
                                </span>
                              </div>
                            )}
                            {purchase.notes && (
                              <div>
                                <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: '600' }}>
                                  Notes: 
                                </span>
                                <span style={{ fontSize: '0.9rem', color: '#374151', marginLeft: '0.5rem' }}>
                                  {purchase.notes}
                                </span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
          
          {/* Payments Tab */}
          {activeTab === 'payments' && (
            <div>
              <h3 style={{ 
                margin: '0 0 1.5rem 0', 
                fontSize: '1.3rem', 
                fontWeight: '600', 
                color: '#1e293b' 
              }}>
                Payment History
              </h3>
              <PaymentStatus />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserProfile;