import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ImageUpload from './ImageUpload';
import { RefundManagement } from './RefundManagement';

interface Item {
  id: number;
  name: string;
  description?: string;
  price: number;
  category: string;
  stock_quantity: number;
  image_url?: string;
  is_active: boolean;
  created_by: number;
  created_at: string;
  updated_at?: string;
  creator_username?: string;
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

interface AdminPanelProps {
  token: string;
}

const AdminPanel: React.FC<AdminPanelProps> = ({ token }) => {
  const [items, setItems] = useState<Item[]>([]);
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [newItem, setNewItem] = useState({
    name: '',
    description: '',
    price: 0,
    category: '',
    stock_quantity: 0,
    image_url: ''
  });
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'items' | 'create' | 'orders' | 'refunds'>('overview');
  const [orderStats, setOrderStats] = useState<any>(null);
  const [selectedOrder, setSelectedOrder] = useState<Purchase | null>(null);
  const [orderUpdateForm, setOrderUpdateForm] = useState({
    status: '',
    tracking_number: '',
    notes: ''
  });

  const API_BASE_URL = 'http://localhost:8001';

  useEffect(() => {
    fetchItems();
    fetchPurchases();
    fetchOrderStats();
  }, []);

  const fetchItems = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/items/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setItems(response.data);
    } catch (error) {
      console.error('Error fetching items:', error);
    }
  };

  const fetchPurchases = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/items/purchases/all`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPurchases(response.data);
    } catch (error) {
      console.error('Error fetching purchases:', error);
    }
  };

  const fetchOrderStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/items/orders/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOrderStats(response.data);
    } catch (error) {
      console.error('Error fetching order stats:', error);
    }
  };

  const updateOrderStatus = async (orderId: number) => {
    try {
      const response = await axios.put(
        `${API_BASE_URL}/api/items/purchases/${orderId}/status`,
        {
          status: orderUpdateForm.status,
          tracking_number: orderUpdateForm.tracking_number || null,
          notes: orderUpdateForm.notes || null
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Update the orders list
      setPurchases(purchases.map(purchase => 
        purchase.id === orderId ? response.data : purchase
      ));
      
      // Close modal and refresh stats
      setSelectedOrder(null);
      fetchOrderStats();
      
      alert('✅ Order status updated successfully!');
    } catch (error: any) {
      alert(`❌ Error: ${error.response?.data?.detail || 'Failed to update order status'}`);
    }
  };

  const openOrderModal = (order: Purchase) => {
    setSelectedOrder(order);
    setOrderUpdateForm({
      status: order.status,
      tracking_number: order.tracking_number || '',
      notes: order.notes || ''
    });
  };

  const createItem = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/items/`, newItem, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setItems([...items, response.data]);
      setNewItem({
        name: '',
        description: '',
        price: 0,
        category: '',
        stock_quantity: 0,
        image_url: ''
      });
      alert('✅ Item created successfully!');
      setActiveTab('items');
    } catch (error: any) {
      console.error('Error creating item:', error);
      alert(`❌ Error: ${error.response?.data?.detail || 'Failed to create item'}`);
    } finally {
      setLoading(false);
    }
  };

  const deleteItem = async (itemId: number) => {
    if (!window.confirm('Are you sure you want to delete this item?')) return;
    
    try {
      await axios.delete(`${API_BASE_URL}/api/items/${itemId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setItems(items.map(item => 
        item.id === itemId ? { ...item, is_active: false } : item
      ));
      alert('✅ Item deleted successfully!');
    } catch (error: any) {
      console.error('Error deleting item:', error);
      alert(`❌ Error: ${error.response?.data?.detail || 'Failed to delete item'}`);
    }
  };

  const totalRevenue = purchases.reduce((sum, purchase) => sum + purchase.total_price, 0);
  const activeItems = items.filter(item => item.is_active);
  const lowStockItems = activeItems.filter(item => item.stock_quantity <= 5);

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
      maxWidth: '1400px', 
      margin: '0 auto', 
      padding: '2rem',
      minHeight: 'calc(100vh - 80px)'
    }}>
      {/* Navigation Tabs */}
      <div style={{ 
        background: 'white',
        borderRadius: '12px',
        padding: '1rem',
        marginBottom: '2rem',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
      }}>
        <button style={tabButtonStyle('overview')} onClick={() => setActiveTab('overview')}>
          📊 Overview
        </button>
        <button style={tabButtonStyle('items')} onClick={() => setActiveTab('items')}>
          📦 Products ({activeItems.length})
        </button>
        <button style={tabButtonStyle('create')} onClick={() => setActiveTab('create')}>
          ➕ Add Product
        </button>
        <button style={tabButtonStyle('orders')} onClick={() => setActiveTab('orders')}>
          🛒 Orders ({purchases.length})
        </button>
        <button style={tabButtonStyle('refunds')} onClick={() => setActiveTab('refunds')}>
          💰 Refunds
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div>
          <h2 style={{ 
            fontSize: '2rem', 
            fontWeight: '700', 
            color: '#1e293b', 
            marginBottom: '2rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            📈 Dashboard Overview
          </h2>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
            gap: '1.5rem',
            marginBottom: '2rem'
          }}>
            {/* Stats Cards */}
            <div style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              padding: '2rem',
              borderRadius: '16px',
              boxShadow: '0 10px 25px rgba(102, 126, 234, 0.3)'
            }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>💰</div>
              <h3 style={{ margin: 0, fontSize: '2rem', fontWeight: '700' }}>
                ${totalRevenue.toFixed(2)}
              </h3>
              <p style={{ margin: 0, opacity: 0.9 }}>Total Revenue</p>
            </div>

            <div style={{
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              color: 'white',
              padding: '2rem',
              borderRadius: '16px',
              boxShadow: '0 10px 25px rgba(245, 87, 108, 0.3)'
            }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🛍️</div>
              <h3 style={{ margin: 0, fontSize: '2rem', fontWeight: '700' }}>
                {purchases.length}
              </h3>
              <p style={{ margin: 0, opacity: 0.9 }}>Total Orders</p>
            </div>

            <div style={{
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              color: 'white',
              padding: '2rem',
              borderRadius: '16px',
              boxShadow: '0 10px 25px rgba(79, 172, 254, 0.3)'
            }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📦</div>
              <h3 style={{ margin: 0, fontSize: '2rem', fontWeight: '700' }}>
                {activeItems.length}
              </h3>
              <p style={{ margin: 0, opacity: 0.9 }}>Active Products</p>
            </div>

            <div style={{
              background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
              color: 'white',
              padding: '2rem',
              borderRadius: '16px',
              boxShadow: '0 10px 25px rgba(250, 112, 154, 0.3)'
            }}>
              <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>⚠️</div>
              <h3 style={{ margin: 0, fontSize: '2rem', fontWeight: '700' }}>
                {lowStockItems.length}
              </h3>
              <p style={{ margin: 0, opacity: 0.9 }}>Low Stock Items</p>
            </div>
          </div>

          {/* Low Stock Alert */}
          {lowStockItems.length > 0 && (
            <div style={{
              background: '#fef3c7',
              border: '1px solid #fcd34d',
              borderRadius: '12px',
              padding: '1.5rem',
              marginBottom: '2rem'
            }}>
              <h3 style={{ color: '#92400e', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                ⚠️ Low Stock Alert
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                {lowStockItems.map(item => (
                  <div key={item.id} style={{ 
                    background: 'white', 
                    padding: '1rem', 
                    borderRadius: '8px',
                    border: '1px solid #fcd34d'
                  }}>
                    <strong style={{ color: '#92400e' }}>{item.name}</strong>
                    <br />
                    <span style={{ color: '#92400e', fontSize: '0.9rem' }}>
                      Only {item.stock_quantity} left
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Create Item Tab */}
      {activeTab === 'create' && (
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '2rem',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
        }}>
          <h2 style={{ 
            fontSize: '1.8rem', 
            fontWeight: '600', 
            color: '#1e293b', 
            marginBottom: '2rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            ➕ Add New Product
          </h2>
          
          <form onSubmit={createItem}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#374151' }}>
                  Product Name *
                </label>
                <input
                  type="text"
                  placeholder="Enter product name"
                  value={newItem.name}
                  onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
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
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#374151' }}>
                  Category *
                </label>
                <input
                  type="text"
                  placeholder="e.g., Electronics, Books"
                  value={newItem.category}
                  onChange={(e) => setNewItem({ ...newItem, category: e.target.value })}
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
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#374151' }}>
                  Price ($) *
                </label>
                <input
                  type="number"
                  placeholder="0.00"
                  value={newItem.price}
                  onChange={(e) => setNewItem({ ...newItem, price: parseFloat(e.target.value) || 0 })}
                  required
                  step="0.01"
                  min="0"
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
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#374151' }}>
                  Stock Quantity *
                </label>
                <input
                  type="number"
                  placeholder="0"
                  value={newItem.stock_quantity}
                  onChange={(e) => setNewItem({ ...newItem, stock_quantity: parseInt(e.target.value) || 0 })}
                  required
                  min="0"
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

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#374151' }}>
                Description
              </label>
              <textarea
                placeholder="Describe your product..."
                value={newItem.description}
                onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
                rows={4}
                style={{ 
                  width: '100%', 
                  padding: '0.75rem', 
                  border: '2px solid #e5e7eb', 
                  borderRadius: '8px',
                  fontSize: '1rem',
                  resize: 'vertical',
                  transition: 'border-color 0.2s ease'
                }}
                onFocus={(e) => e.target.style.borderColor = '#667eea'}
                onBlur={(e) => e.target.style.borderColor = '#e5e7eb'}
              />
            </div>

            <div style={{ marginBottom: '2rem' }}>
              <ImageUpload
                token={token}
                currentImageUrl={newItem.image_url}
                onImageUploaded={(imageUrl) => setNewItem({ ...newItem, image_url: imageUrl })}
                disabled={loading}
              />
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
              {loading ? '⏳ Creating...' : '✨ Create Product'}
            </button>
          </form>
        </div>
      )}

      {/* Items Tab */}
      {activeTab === 'items' && (
        <div>
          <h2 style={{ 
            fontSize: '1.8rem', 
            fontWeight: '600', 
            color: '#1e293b', 
            marginBottom: '2rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            📦 Product Inventory
          </h2>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', 
            gap: '1.5rem' 
          }}>
            {items.map((item) => (
              <div key={item.id} style={{ 
                background: 'white',
                borderRadius: '16px',
                padding: '1.5rem',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)',
                border: item.is_active ? '1px solid #e5e7eb' : '1px solid #fca5a5',
                opacity: item.is_active ? 1 : 0.7,
                transition: 'transform 0.2s ease, box-shadow 0.2s ease'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.1)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.05)';
              }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                  <h4 style={{ 
                    margin: 0, 
                    fontSize: '1.2rem', 
                    fontWeight: '600', 
                    color: '#1e293b',
                    lineHeight: '1.3'
                  }}>
                    {item.name}
                  </h4>
                  <span style={{
                    background: item.is_active ? '#dcfce7' : '#fee2e2',
                    color: item.is_active ? '#166534' : '#991b1b',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '9999px',
                    fontSize: '0.8rem',
                    fontWeight: '500'
                  }}>
                    {item.is_active ? '✅ Active' : '❌ Inactive'}
                  </span>
                </div>
                
                <p style={{ 
                  margin: '0 0 1rem 0', 
                  color: '#64748b', 
                  fontSize: '0.9rem',
                  lineHeight: '1.5'
                }}>
                  {item.description || 'No description available'}
                </p>
                
                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: '600', fontSize: '1.4rem', color: '#059669' }}>
                      ${item.price.toFixed(2)}
                    </span>
                    <span style={{ 
                      background: '#f1f5f9', 
                      color: '#475569', 
                      padding: '0.25rem 0.5rem', 
                      borderRadius: '6px',
                      fontSize: '0.8rem',
                      fontWeight: '500'
                    }}>
                      {item.category}
                    </span>
                  </div>
                  
                  <div style={{ fontSize: '0.9rem', color: '#64748b' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span>Stock:</span>
                      <span style={{ 
                        fontWeight: '600',
                        color: item.stock_quantity <= 5 ? '#dc2626' : '#059669'
                      }}>
                        {item.stock_quantity} units
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Created by:</span>
                      <span style={{ fontWeight: '500' }}>{item.creator_username}</span>
                    </div>
                  </div>
                </div>
                
                {item.is_active && (
                  <button
                    onClick={() => deleteItem(item.id)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                      color: 'white',
                      border: 'none',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontSize: '0.9rem',
                      fontWeight: '500',
                      transition: 'transform 0.1s ease'
                    }}
                    onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.98)'}
                    onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
                  >
                    🗑️ Delete Product
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Orders Tab */}
      {activeTab === 'orders' && (
        <div>
          <h2 style={{ 
            fontSize: '1.8rem', 
            fontWeight: '600', 
            color: '#1e293b', 
            marginBottom: '2rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            🛒 Order Management
          </h2>
          
          <div style={{
            background: 'white',
            borderRadius: '16px',
            padding: '1.5rem',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)',
            overflowX: 'auto'
          }}>
            {purchases.length === 0 ? (
              <div style={{ 
                textAlign: 'center', 
                padding: '3rem',
                color: '#64748b'
              }}>
                <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>📦</div>
                <h3 style={{ color: '#64748b', fontWeight: '500' }}>No orders yet</h3>
                <p>Orders will appear here once customers start purchasing.</p>
              </div>
            ) : (
              <table style={{ 
                width: '100%', 
                borderCollapse: 'separate',
                borderSpacing: '0'
              }}>
                <thead>
                  <tr style={{ background: '#f8fafc' }}>
                    <th style={{ 
                      padding: '1rem', 
                      textAlign: 'left',
                      fontWeight: '600',
                      color: '#374151',
                      borderRadius: '8px 0 0 0'
                    }}>
                      Order #
                    </th>
                    <th style={{ 
                      padding: '1rem', 
                      textAlign: 'left',
                      fontWeight: '600',
                      color: '#374151'
                    }}>
                      Customer
                    </th>
                    <th style={{ 
                      padding: '1rem', 
                      textAlign: 'left',
                      fontWeight: '600',
                      color: '#374151'
                    }}>
                      Product
                    </th>
                    <th style={{ 
                      padding: '1rem', 
                      textAlign: 'center',
                      fontWeight: '600',
                      color: '#374151'
                    }}>
                      Status
                    </th>
                    <th style={{ 
                      padding: '1rem', 
                      textAlign: 'right',
                      fontWeight: '600',
                      color: '#374151'
                    }}>
                      Total
                    </th>
                    <th style={{ 
                      padding: '1rem', 
                      textAlign: 'center',
                      fontWeight: '600',
                      color: '#374151',
                      borderRadius: '0 8px 0 0'
                    }}>
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {purchases.map((purchase, index) => {
                    const statusColor = getStatusColor(purchase.status);
                    return (
                      <tr key={purchase.id} style={{
                        borderBottom: index < purchases.length - 1 ? '1px solid #f1f5f9' : 'none',
                        cursor: 'pointer'
                      }}
                      onClick={() => openOrderModal(purchase)}>
                        <td style={{ 
                          padding: '1rem',
                          fontWeight: '600',
                          color: '#374151',
                          fontFamily: 'monospace'
                        }}>
                          #{purchase.id.toString().padStart(6, '0')}
                        </td>
                        <td style={{ 
                          padding: '1rem',
                          fontWeight: '500',
                          color: '#374151'
                        }}>
                          {purchase.customer_username}
                        </td>
                        <td style={{ 
                          padding: '1rem',
                          color: '#64748b'
                        }}>
                          <div>{purchase.item_name}</div>
                          <div style={{ fontSize: '0.8rem', color: '#9ca3af' }}>
                            Qty: {purchase.quantity}
                          </div>
                        </td>
                        <td style={{ 
                          padding: '1rem', 
                          textAlign: 'center'
                        }}>
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
                        </td>
                        <td style={{ 
                          padding: '1rem', 
                          textAlign: 'right',
                          fontWeight: '600',
                          color: '#059669',
                          fontSize: '1.1rem'
                        }}>
                          ${purchase.total_price.toFixed(2)}
                        </td>
                        <td style={{ 
                          padding: '1rem',
                          textAlign: 'center'
                        }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              openOrderModal(purchase);
                            }}
                            style={{
                              padding: '0.5rem 1rem',
                              background: '#667eea',
                              color: 'white',
                              border: 'none',
                              borderRadius: '8px',
                              cursor: 'pointer',
                              fontSize: '0.9rem',
                              fontWeight: '500'
                            }}
                          >
                            Manage
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* Order Management Modal */}
      {selectedOrder && (
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
            maxWidth: '600px',
            backgroundColor: 'white',
            borderRadius: '20px',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.15)',
            maxHeight: '90%',
            overflow: 'auto'
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '2rem',
              borderBottom: '1px solid #e5e7eb',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              borderRadius: '20px 20px 0 0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: '600' }}>
                  Order #{selectedOrder.id.toString().padStart(6, '0')}
                </h2>
                <p style={{ margin: '0.5rem 0 0 0', opacity: 0.9, fontSize: '1rem' }}>
                  Manage order status and tracking
                </p>
              </div>
              <button
                onClick={() => setSelectedOrder(null)}
                style={{
                  background: 'rgba(255, 255, 255, 0.2)',
                  border: 'none',
                  color: 'white',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  padding: '0.5rem',
                  borderRadius: '8px',
                  width: '40px',
                  height: '40px'
                }}
              >
                ✕
              </button>
            </div>

            {/* Modal Content */}
            <div style={{ padding: '2rem' }}>
              {/* Order Details */}
              <div style={{ 
                background: '#f8fafc',
                borderRadius: '12px',
                padding: '1.5rem',
                marginBottom: '2rem'
              }}>
                <h3 style={{ margin: '0 0 1rem 0', color: '#374151' }}>Order Details</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <span style={{ color: '#64748b', fontSize: '0.9rem' }}>Customer:</span>
                    <p style={{ margin: '0.25rem 0', fontWeight: '600', color: '#374151' }}>
                      {selectedOrder.customer_username}
                    </p>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', fontSize: '0.9rem' }}>Product:</span>
                    <p style={{ margin: '0.25rem 0', fontWeight: '600', color: '#374151' }}>
                      {selectedOrder.item_name}
                    </p>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', fontSize: '0.9rem' }}>Quantity:</span>
                    <p style={{ margin: '0.25rem 0', fontWeight: '600', color: '#374151' }}>
                      {selectedOrder.quantity}
                    </p>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', fontSize: '0.9rem' }}>Total:</span>
                    <p style={{ margin: '0.25rem 0', fontWeight: '600', color: '#059669', fontSize: '1.1rem' }}>
                      ${selectedOrder.total_price.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', fontSize: '0.9rem' }}>Order Date:</span>
                    <p style={{ margin: '0.25rem 0', fontWeight: '500', color: '#374151' }}>
                      {new Date(selectedOrder.purchase_date).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', fontSize: '0.9rem' }}>Current Status:</span>
                    <div style={{ margin: '0.25rem 0' }}>
                      <span style={{
                        background: getStatusColor(selectedOrder.status).bg,
                        color: getStatusColor(selectedOrder.status).text,
                        padding: '0.5rem 0.75rem',
                        borderRadius: '20px',
                        fontSize: '0.8rem',
                        fontWeight: '600',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem'
                      }}>
                        {getStatusIcon(selectedOrder.status)} {selectedOrder.status.charAt(0).toUpperCase() + selectedOrder.status.slice(1)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Update Form */}
              <form onSubmit={(e) => {
                e.preventDefault();
                updateOrderStatus(selectedOrder.id);
              }}>
                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ 
                    display: 'block', 
                    marginBottom: '0.5rem', 
                    fontWeight: '600', 
                    color: '#374151' 
                  }}>
                    Update Status
                  </label>
                  <select
                    value={orderUpdateForm.status}
                    onChange={(e) => setOrderUpdateForm({ ...orderUpdateForm, status: e.target.value })}
                    required
                    style={{ 
                      width: '100%', 
                      padding: '0.75rem', 
                      border: '2px solid #e5e7eb', 
                      borderRadius: '8px',
                      fontSize: '1rem',
                      backgroundColor: 'white'
                    }}
                  >
                    <option value="pending">⏳ Pending</option>
                    <option value="confirmed">✅ Confirmed</option>
                    <option value="processing">🔄 Processing</option>
                    <option value="shipped">🚚 Shipped</option>
                    <option value="delivered">📦 Delivered</option>
                    <option value="cancelled">❌ Cancelled</option>
                  </select>
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                  <label style={{ 
                    display: 'block', 
                    marginBottom: '0.5rem', 
                    fontWeight: '600', 
                    color: '#374151' 
                  }}>
                    Tracking Number (optional)
                  </label>
                  <input
                    type="text"
                    placeholder="Enter tracking number"
                    value={orderUpdateForm.tracking_number}
                    onChange={(e) => setOrderUpdateForm({ ...orderUpdateForm, tracking_number: e.target.value })}
                    style={{ 
                      width: '100%', 
                      padding: '0.75rem', 
                      border: '2px solid #e5e7eb', 
                      borderRadius: '8px',
                      fontSize: '1rem'
                    }}
                  />
                </div>

                <div style={{ marginBottom: '2rem' }}>
                  <label style={{ 
                    display: 'block', 
                    marginBottom: '0.5rem', 
                    fontWeight: '600', 
                    color: '#374151' 
                  }}>
                    Notes (optional)
                  </label>
                  <textarea
                    placeholder="Add notes about this order..."
                    value={orderUpdateForm.notes}
                    onChange={(e) => setOrderUpdateForm({ ...orderUpdateForm, notes: e.target.value })}
                    rows={3}
                    style={{ 
                      width: '100%', 
                      padding: '0.75rem', 
                      border: '2px solid #e5e7eb', 
                      borderRadius: '8px',
                      fontSize: '1rem',
                      resize: 'vertical'
                    }}
                  />
                </div>

                <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                  <button
                    type="button"
                    onClick={() => setSelectedOrder(null)}
                    style={{
                      padding: '0.875rem 2rem',
                      border: '1px solid #d1d5db',
                      background: 'white',
                      color: '#374151',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontSize: '1rem',
                      fontWeight: '500'
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    style={{
                      padding: '0.875rem 2rem',
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      color: 'white',
                      border: 'none',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      fontSize: '1rem',
                      fontWeight: '600',
                      boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)'
                    }}
                  >
                    Update Order
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Refunds Tab */}
      {activeTab === 'refunds' && (
        <div>
          <RefundManagement />
        </div>
      )}
    </div>
  );
};

export default AdminPanel;