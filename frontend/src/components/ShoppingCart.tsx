import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface CartItem {
  id: number;
  user_id: number;
  item_id: number;
  quantity: number;
  added_at: string;
  item_name: string;
  item_price: number;
  item_image_url?: string;
  item_stock_quantity: number;
  subtotal: number;
}

interface CartSummary {
  items: CartItem[];
  total_items: number;
  total_price: number;
}

interface ShoppingCartProps {
  token: string;
  isOpen: boolean;
  onClose: () => void;
  onCartUpdate?: () => void;
}

const ShoppingCart: React.FC<ShoppingCartProps> = ({ token, isOpen, onClose, onCartUpdate }) => {
  const [cart, setCart] = useState<CartSummary>({ items: [], total_items: 0, total_price: 0 });
  const [loading, setLoading] = useState(false);
  const [checkingOut, setCheckingOut] = useState(false);

  const API_BASE_URL = 'http://localhost:8000';

  useEffect(() => {
    if (isOpen) {
      fetchCart();
    }
  }, [isOpen]);

  const fetchCart = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/api/cart/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCart(response.data);
    } catch (error) {
      console.error('Error fetching cart:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateQuantity = async (cartItemId: number, quantity: number) => {
    if (quantity <= 0) return;
    
    try {
      await axios.put(`${API_BASE_URL}/api/cart/${cartItemId}`, 
        { quantity },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchCart();
      onCartUpdate?.();
    } catch (error: any) {
      alert(`Error: ${error.response?.data?.detail || 'Failed to update quantity'}`);
    }
  };

  const removeItem = async (cartItemId: number) => {
    try {
      await axios.delete(`${API_BASE_URL}/api/cart/${cartItemId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchCart();
      onCartUpdate?.();
    } catch (error: any) {
      alert(`Error: ${error.response?.data?.detail || 'Failed to remove item'}`);
    }
  };

  const clearCart = async () => {
    if (!window.confirm('Are you sure you want to clear your cart?')) return;
    
    try {
      await axios.delete(`${API_BASE_URL}/api/cart/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchCart();
      onCartUpdate?.();
    } catch (error: any) {
      alert(`Error: ${error.response?.data?.detail || 'Failed to clear cart'}`);
    }
  };

  const checkout = async () => {
    if (cart.items.length === 0) return;
    
    setCheckingOut(true);
    try {
      // First create purchases (orders) from cart
      const response = await axios.post(`${API_BASE_URL}/api/cart/checkout`, 
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Get the created purchases
      const purchases = response.data;
      
      if (purchases.length === 0) {
        alert('No purchases created');
        return;
      }

      // For simplicity, we'll handle payment for the first purchase
      // In a real app, you might want to combine all purchases into one payment
      const firstPurchase = purchases[0];
      
      // Show payment modal or redirect to payment page
      // For now, let's create a simple payment intent
      try {
        const paymentResponse = await axios.post(
          `${API_BASE_URL}/api/payments/intent`,
          {
            purchase_id: firstPurchase.id,
            provider: 'stripe', // Default to Stripe
            payment_method_type: 'card'
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        
        alert(`✅ Orders created! Please complete payment. Payment ID: ${paymentResponse.data.payment_id}`);
        // In a real app, you would redirect to a payment page or show payment modal
        // For now, we'll just show the purchase was created
        
      } catch (paymentError: any) {
        console.error('Payment creation failed:', paymentError);
        alert(`✅ Orders created but payment setup failed: ${paymentError.response?.data?.detail || 'Please contact support'}`);
      }
      
      fetchCart();
      onCartUpdate?.();
      onClose();
    } catch (error: any) {
      alert(`❌ Checkout failed: ${error.response?.data?.detail || 'Please try again'}`);
    } finally {
      setCheckingOut(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      width: '100%',
      height: '100%',
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      zIndex: 2000,
      display: 'flex',
      justifyContent: 'flex-end'
    }}>
      <div style={{
        width: '500px',
        height: '100%',
        backgroundColor: 'white',
        boxShadow: '-4px 0 20px rgba(0, 0, 0, 0.15)',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{
          padding: '1.5rem',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white'
        }}>
          <h2 style={{ 
            margin: 0, 
            fontSize: '1.5rem', 
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            🛒 Shopping Cart ({cart.total_items})
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'white',
              fontSize: '1.5rem',
              cursor: 'pointer',
              padding: '0.5rem',
              borderRadius: '4px'
            }}
          >
            ✕
          </button>
        </div>

        {/* Cart Items */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: loading ? '2rem' : '0'
        }}>
          {loading ? (
            <div style={{ textAlign: 'center', color: '#64748b' }}>
              <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⏳</div>
              Loading cart...
            </div>
          ) : cart.items.length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              padding: '3rem 2rem',
              color: '#64748b'
            }}>
              <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🛒</div>
              <h3 style={{ color: '#64748b', fontWeight: '500', margin: '0 0 0.5rem 0' }}>
                Your cart is empty
              </h3>
              <p style={{ margin: 0 }}>Add some items to get started!</p>
            </div>
          ) : (
            <div>
              {cart.items.map((item) => (
                <div key={item.id} style={{
                  padding: '1.5rem',
                  borderBottom: '1px solid #f1f5f9',
                  display: 'flex',
                  gap: '1rem'
                }}>
                  {/* Item Image */}
                  <div style={{
                    width: '80px',
                    height: '80px',
                    backgroundColor: '#f8fafc',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    backgroundImage: item.item_image_url ? `url(${item.item_image_url})` : 'none',
                    backgroundSize: 'cover',
                    backgroundPosition: 'center'
                  }}>
                    {!item.item_image_url && (
                      <span style={{ fontSize: '2rem' }}>📦</span>
                    )}
                  </div>

                  {/* Item Details */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h4 style={{
                      margin: '0 0 0.5rem 0',
                      fontSize: '1.1rem',
                      fontWeight: '600',
                      color: '#1e293b',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {item.item_name}
                    </h4>
                    
                    <p style={{
                      margin: '0 0 0.75rem 0',
                      fontSize: '1.1rem',
                      fontWeight: '600',
                      color: '#059669'
                    }}>
                      ${item.item_price.toFixed(2)}
                    </p>

                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}>
                      {/* Quantity Controls */}
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                      }}>
                        <button
                          onClick={() => updateQuantity(item.id, item.quantity - 1)}
                          disabled={item.quantity <= 1}
                          style={{
                            width: '32px',
                            height: '32px',
                            border: '1px solid #d1d5db',
                            background: item.quantity <= 1 ? '#f9fafb' : 'white',
                            borderRadius: '4px',
                            cursor: item.quantity <= 1 ? 'not-allowed' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '1.2rem',
                            color: item.quantity <= 1 ? '#9ca3af' : '#374151'
                          }}
                        >
                          −
                        </button>
                        
                        <span style={{
                          minWidth: '2rem',
                          textAlign: 'center',
                          fontWeight: '600',
                          color: '#374151'
                        }}>
                          {item.quantity}
                        </span>
                        
                        <button
                          onClick={() => updateQuantity(item.id, item.quantity + 1)}
                          disabled={item.quantity >= item.item_stock_quantity}
                          style={{
                            width: '32px',
                            height: '32px',
                            border: '1px solid #d1d5db',
                            background: item.quantity >= item.item_stock_quantity ? '#f9fafb' : 'white',
                            borderRadius: '4px',
                            cursor: item.quantity >= item.item_stock_quantity ? 'not-allowed' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '1.2rem',
                            color: item.quantity >= item.item_stock_quantity ? '#9ca3af' : '#374151'
                          }}
                        >
                          +
                        </button>
                      </div>

                      {/* Remove Button */}
                      <button
                        onClick={() => removeItem(item.id)}
                        style={{
                          padding: '0.5rem',
                          background: 'none',
                          border: 'none',
                          color: '#dc2626',
                          cursor: 'pointer',
                          borderRadius: '4px',
                          fontSize: '1.2rem'
                        }}
                        title="Remove item"
                      >
                        🗑️
                      </button>
                    </div>

                    {/* Subtotal */}
                    <div style={{
                      marginTop: '0.75rem',
                      fontSize: '1rem',
                      fontWeight: '600',
                      color: '#374151',
                      textAlign: 'right'
                    }}>
                      Subtotal: ${item.subtotal.toFixed(2)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {cart.items.length > 0 && (
          <div style={{
            padding: '1.5rem',
            borderTop: '1px solid #e5e7eb',
            backgroundColor: '#f8fafc'
          }}>
            {/* Total */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem',
              fontSize: '1.2rem',
              fontWeight: '700'
            }}>
              <span>Total:</span>
              <span style={{ color: '#059669' }}>
                ${cart.total_price.toFixed(2)}
              </span>
            </div>

            {/* Action Buttons */}
            <div style={{
              display: 'flex',
              gap: '0.75rem'
            }}>
              <button
                onClick={clearCart}
                style={{
                  flex: 1,
                  padding: '0.75rem',
                  border: '1px solid #d1d5db',
                  background: 'white',
                  color: '#374151',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: '500'
                }}
              >
                Clear Cart
              </button>
              
              <button
                onClick={checkout}
                disabled={checkingOut}
                style={{
                  flex: 2,
                  padding: '0.75rem',
                  border: 'none',
                  background: checkingOut ? '#9ca3af' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  borderRadius: '8px',
                  cursor: checkingOut ? 'not-allowed' : 'pointer',
                  fontSize: '1rem',
                  fontWeight: '600',
                  boxShadow: checkingOut ? 'none' : '0 4px 12px rgba(102, 126, 234, 0.4)'
                }}
              >
                {checkingOut ? '⏳ Processing...' : '💳 Checkout'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShoppingCart;