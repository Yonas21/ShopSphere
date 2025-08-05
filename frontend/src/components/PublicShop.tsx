import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Login from './Login';

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

interface PublicShopProps {
  // No longer needs onLogin prop - handled by context
}

const PublicShop: React.FC<PublicShopProps> = () => {
  const [items, setItems] = useState<Item[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [minPrice, setMinPrice] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('created_at');
  const [sortOrder, setSortOrder] = useState<string>('desc');
  const [inStockOnly, setInStockOnly] = useState<boolean>(true);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [purchaseQuantities, setPurchaseQuantities] = useState<{[key: number]: number}>({});

  const API_BASE_URL = 'http://localhost:8001';

  useEffect(() => {
    fetchItems();
    fetchCategories();
  }, [selectedCategory, searchTerm, minPrice, maxPrice, sortBy, sortOrder, inStockOnly]);

  const fetchItems = async () => {
    try {
      const params: any = {
        sort_by: sortBy,
        sort_order: sortOrder,
        in_stock_only: inStockOnly
      };
      
      if (selectedCategory) params.category = selectedCategory;
      if (searchTerm) params.search = searchTerm;
      if (minPrice) params.min_price = parseFloat(minPrice);
      if (maxPrice) params.max_price = parseFloat(maxPrice);
      
      const response = await axios.get(`${API_BASE_URL}/api/items/`, { params });
      setItems(response.data);
    } catch (error) {
      console.error('Error fetching items:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/items/categories/list`);
      setCategories(response.data.categories);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const handlePurchaseClick = (itemId: number) => {
    setSelectedItemForPurchase(itemId);
    setShowLoginModal(true);
  };

  const handleAddToCartClick = () => {
    setShowLoginModal(true);
  };

  const updateQuantity = (itemId: number, quantity: number) => {
    const item = items.find(i => i.id === itemId);
    const maxQuantity = item ? item.stock_quantity : 1;
    const validQuantity = Math.max(1, Math.min(quantity, maxQuantity));
    setPurchaseQuantities({ ...purchaseQuantities, [itemId]: validQuantity });
  };


  const filteredItems = items;

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
      {/* Header */}
      <header style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        position: 'sticky',
        top: 0,
        zIndex: 1000
      }}>
        <div style={{ 
          maxWidth: '1200px', 
          margin: '0 auto', 
          padding: '1rem 2rem',
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              width: '40px',
              height: '40px',
              background: 'white',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '24px',
              fontWeight: 'bold',
              color: '#667eea'
            }}>
              🛍️
            </div>
            <div>
              <h1 style={{ 
                margin: 0, 
                color: 'white', 
                fontSize: '1.8rem',
                fontWeight: '700',
                letterSpacing: '-0.025em'
              }}>
                ShopSphere
              </h1>
              <p style={{ 
                margin: 0, 
                color: 'rgba(255, 255, 255, 0.8)', 
                fontSize: '0.9rem',
                fontWeight: '400'
              }}>
                Your Shopping Destination
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button 
              onClick={() => setShowLoginModal(true)}
              style={{ 
                padding: '0.5rem 1.5rem',
                background: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: '500',
                transition: 'all 0.2s ease',
                backdropFilter: 'blur(10px)'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
              }}
            >
              👤 Login / Sign Up
            </button>
          </div>
        </div>
      </header>

      <main style={{ 
        maxWidth: '1400px', 
        margin: '0 auto', 
        padding: '2rem',
        minHeight: 'calc(100vh - 80px)'
      }}>
        {/* Welcome Section */}
        <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: '20px',
          padding: '2rem',
          marginBottom: '2rem',
          color: 'white',
          boxShadow: '0 10px 30px rgba(102, 126, 234, 0.3)',
          textAlign: 'center'
        }}>
          <h1 style={{ 
            margin: '0 0 0.5rem 0', 
            fontSize: '2.5rem', 
            fontWeight: '700',
            textShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            Welcome to ShopSphere! 🌟
          </h1>
          <p style={{ 
            margin: '0 0 1rem 0', 
            fontSize: '1.2rem', 
            opacity: 0.9,
            fontWeight: '400'
          }}>
            Browse our amazing collection of products. Login to start shopping!
          </p>
          <div style={{
            background: 'rgba(255, 255, 255, 0.2)',
            padding: '1rem 1.5rem',
            borderRadius: '12px',
            backdropFilter: 'blur(10px)',
            display: 'inline-block',
            marginTop: '1rem'
          }}>
            <p style={{ margin: 0, fontSize: '1rem', opacity: 0.9 }}>
              🔍 Explore {filteredItems.length} products available
            </p>
          </div>
        </div>

        {/* Search and Filters */}
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '1.5rem',
          marginBottom: '2rem',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
        }}>
          {/* Search and Basic Filters */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '0.5rem', 
                fontWeight: '600', 
                color: '#374151',
                fontSize: '0.95rem'
              }}>
                🔍 Search Products
              </label>
              <input
                type="text"
                placeholder="Search by name, description, or category..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ 
                  width: '100%', 
                  padding: '0.75rem 1rem', 
                  border: '2px solid #e5e7eb', 
                  borderRadius: '12px',
                  fontSize: '1rem',
                  transition: 'all 0.2s ease'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#667eea';
                  e.target.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.1)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = '#e5e7eb';
                  e.target.style.boxShadow = 'none';
                }}
              />
            </div>
            
            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '0.5rem', 
                fontWeight: '600', 
                color: '#374151',
                fontSize: '0.95rem'
              }}>
                🏷️ Category
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                style={{ 
                  width: '100%', 
                  padding: '0.75rem 1rem', 
                  border: '2px solid #e5e7eb', 
                  borderRadius: '12px',
                  fontSize: '1rem',
                  backgroundColor: 'white',
                  cursor: 'pointer'
                }}
              >
                <option value="">All Categories</option>
                {categories.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '0.5rem', 
                fontWeight: '600', 
                color: '#374151',
                fontSize: '0.95rem'
              }}>
                📊 Sort By
              </label>
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [field, order] = e.target.value.split('-');
                  setSortBy(field);
                  setSortOrder(order);
                }}
                style={{ 
                  width: '100%', 
                  padding: '0.75rem 1rem', 
                  border: '2px solid #e5e7eb', 
                  borderRadius: '12px',
                  fontSize: '1rem',
                  backgroundColor: 'white',
                  cursor: 'pointer'
                }}
              >
                <option value="created_at-desc">Newest First</option>
                <option value="created_at-asc">Oldest First</option>
                <option value="name-asc">Name A-Z</option>
                <option value="name-desc">Name Z-A</option>
                <option value="price-asc">Price Low-High</option>
                <option value="price-desc">Price High-Low</option>
                <option value="stock_quantity-desc">Most Stock</option>
                <option value="stock_quantity-asc">Least Stock</option>
              </select>
            </div>
          </div>

          {/* Price Range and Advanced Filters */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', alignItems: 'end' }}>
            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '0.5rem', 
                fontWeight: '600', 
                color: '#374151',
                fontSize: '0.95rem'
              }}>
                💰 Min Price
              </label>
              <input
                type="number"
                placeholder="0.00"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
                min="0"
                step="0.01"
                style={{ 
                  width: '100%', 
                  padding: '0.75rem 1rem', 
                  border: '2px solid #e5e7eb', 
                  borderRadius: '12px',
                  fontSize: '1rem'
                }}
              />
            </div>

            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '0.5rem', 
                fontWeight: '600', 
                color: '#374151',
                fontSize: '0.95rem'
              }}>
                💰 Max Price
              </label>
              <input
                type="number"
                placeholder="999.99"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                min="0"
                step="0.01"
                style={{ 
                  width: '100%', 
                  padding: '0.75rem 1rem', 
                  border: '2px solid #e5e7eb', 
                  borderRadius: '12px',
                  fontSize: '1rem'
                }}
              />
            </div>

            <div>
              <label style={{ 
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontWeight: '600', 
                color: '#374151',
                fontSize: '0.95rem',
                cursor: 'pointer'
              }}>
                <input
                  type="checkbox"
                  checked={inStockOnly}
                  onChange={(e) => setInStockOnly(e.target.checked)}
                  style={{ 
                    width: '18px',
                    height: '18px',
                    cursor: 'pointer'
                  }}
                />
                📦 In Stock Only
              </label>
            </div>
          </div>
          
          {/* Active Filters Summary */}
          {(searchTerm || selectedCategory || minPrice || maxPrice || !inStockOnly) && (
            <div style={{ 
              marginTop: '1rem', 
              padding: '0.75rem 1rem',
              background: '#f0f9ff',
              borderRadius: '8px',
              border: '1px solid #bae6fd',
              color: '#0369a1',
              fontSize: '0.95rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                Showing {filteredItems.length} result{filteredItems.length !== 1 ? 's' : ''} 
                {selectedCategory && ` in "${selectedCategory}"`}
                {searchTerm && ` matching "${searchTerm}"`}
                {(minPrice || maxPrice) && ` ($${minPrice || '0'} - $${maxPrice || '∞'})`}
                {!inStockOnly && ' (including out of stock)'}
              </div>
              <button
                onClick={() => {
                  setSearchTerm('');
                  setSelectedCategory('');
                  setMinPrice('');
                  setMaxPrice('');
                  setInStockOnly(true);
                  setSortBy('created_at');
                  setSortOrder('desc');
                }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#0369a1',
                  textDecoration: 'underline',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: '600'
                }}
              >
                Clear All Filters
              </button>
            </div>
          )}
        </div>

        {/* Products Grid */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', 
          gap: '1.5rem' 
        }}>
          {filteredItems.length === 0 ? (
            <div style={{
              gridColumn: '1 / -1',
              textAlign: 'center',
              padding: '4rem 2rem',
              background: 'white',
              borderRadius: '16px',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)'
            }}>
              <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🔍</div>
              <h3 style={{ color: '#64748b', fontWeight: '500', marginBottom: '0.5rem' }}>
                No products found
              </h3>
              <p style={{ color: '#9ca3af', margin: 0 }}>
                Try adjusting your search or filter criteria
              </p>
            </div>
          ) : (
            filteredItems.map((item) => (
              <div key={item.id} style={{ 
                background: 'white',
                borderRadius: '20px',
                overflow: 'hidden',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.05)',
                transition: 'all 0.3s ease',
                border: '1px solid #f1f5f9'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)';
                e.currentTarget.style.boxShadow = '0 20px 40px rgba(0, 0, 0, 0.1)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.05)';
              }}
              >
                {/* Product Image */}
                <div style={{ 
                  height: '200px', 
                  background: item.image_url ? `url(${item.image_url})` : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  backgroundSize: 'cover',
                  backgroundPosition: 'center',
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  {!item.image_url && (
                    <div style={{ 
                      fontSize: '3rem',
                      filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))'
                    }}>
                      📦
                    </div>
                  )}
                  <div style={{
                    position: 'absolute',
                    top: '1rem',
                    right: '1rem',
                    background: 'rgba(255, 255, 255, 0.95)',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '20px',
                    fontSize: '0.8rem',
                    fontWeight: '600',
                    color: '#667eea',
                    backdropFilter: 'blur(10px)'
                  }}>
                    {item.category}
                  </div>
                </div>

                <div style={{ padding: '1.5rem' }}>
                  {/* Product Info */}
                  <h3 style={{ 
                    margin: '0 0 0.5rem 0', 
                    fontSize: '1.3rem', 
                    fontWeight: '700', 
                    color: '#1e293b',
                    lineHeight: '1.3'
                  }}>
                    {item.name}
                  </h3>
                  
                  <p style={{ 
                    margin: '0 0 1rem 0', 
                    color: '#64748b', 
                    fontSize: '0.95rem',
                    lineHeight: '1.5',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden'
                  }}>
                    {item.description || 'No description available'}
                  </p>
                  
                  {/* Price and Stock */}
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center', 
                    marginBottom: '1.5rem'
                  }}>
                    <div style={{ fontSize: '1.8rem', fontWeight: '700', color: '#059669' }}>
                      ${item.price.toFixed(2)}
                    </div>
                    <div style={{ 
                      fontSize: '0.9rem', 
                      color: item.stock_quantity <= 10 ? '#dc2626' : '#64748b',
                      fontWeight: '500'
                    }}>
                      {item.stock_quantity} in stock
                    </div>
                  </div>

                  <div style={{ fontSize: '0.85rem', color: '#9ca3af', marginBottom: '1rem' }}>
                    Sold by {item.creator_username}
                  </div>
                  
                  {/* Purchase Controls */}
                  <div style={{ 
                    padding: '1rem',
                    background: '#f8fafc',
                    borderRadius: '12px',
                    margin: '-0.5rem -0.5rem 0 -0.5rem'
                  }}>
                    {/* Quantity Selector */}
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '0.5rem',
                      marginBottom: '0.75rem'
                    }}>
                      <label style={{ fontSize: '0.9rem', fontWeight: '500', color: '#374151' }}>
                        Qty:
                      </label>
                      <input
                        type="number"
                        min="1"
                        max={item.stock_quantity}
                        value={purchaseQuantities[item.id] || 1}
                        onChange={(e) => updateQuantity(item.id, parseInt(e.target.value))}
                        style={{ 
                          width: '70px', 
                          padding: '0.5rem', 
                          border: '2px solid #e5e7eb', 
                          borderRadius: '8px',
                          textAlign: 'center',
                          fontSize: '0.9rem',
                          fontWeight: '600'
                        }}
                      />
                      <span style={{ fontSize: '0.9rem', color: '#64748b', marginLeft: '0.5rem' }}>
                        Total: ${((purchaseQuantities[item.id] || 1) * item.price).toFixed(2)}
                      </span>
                    </div>
                    
                    {/* Action Buttons */}
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        onClick={handleAddToCartClick}
                        style={{
                          flex: 1,
                          padding: '0.75rem 1rem',
                          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          color: 'white',
                          border: 'none',
                          borderRadius: '10px',
                          cursor: 'pointer',
                          fontWeight: '600',
                          fontSize: '0.9rem',
                          transition: 'all 0.2s ease',
                          boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '0.5rem'
                        }}
                        onMouseOver={(e) => {
                          e.currentTarget.style.transform = 'translateY(-1px)';
                          e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.4)';
                        }}
                        onMouseOut={(e) => {
                          e.currentTarget.style.transform = 'translateY(0)';
                          e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.3)';
                        }}
                      >
                        🛒 Add to Cart
                      </button>
                      
                      <button
                        onClick={() => handlePurchaseClick(item.id)}
                        style={{
                          flex: 1,
                          padding: '0.75rem 1rem',
                          background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                          color: 'white',
                          border: 'none',
                          borderRadius: '10px',
                          cursor: 'pointer',
                          fontWeight: '600',
                          fontSize: '0.9rem',
                          transition: 'all 0.2s ease',
                          boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '0.5rem'
                        }}
                        onMouseOver={(e) => {
                          e.currentTarget.style.transform = 'translateY(-1px)';
                          e.currentTarget.style.boxShadow = '0 6px 20px rgba(16, 185, 129, 0.4)';
                        }}
                        onMouseOut={(e) => {
                          e.currentTarget.style.transform = 'translateY(0)';
                          e.currentTarget.style.boxShadow = '0 4px 12px rgba(16, 185, 129, 0.3)';
                        }}
                      >
                        ⚡ Buy Now
                      </button>
                    </div>

                    {/* Login Prompt */}
                    <div style={{
                      marginTop: '0.75rem',
                      padding: '0.5rem',
                      background: '#fef3c7',
                      borderRadius: '8px',
                      textAlign: 'center',
                      fontSize: '0.8rem',
                      color: '#92400e'
                    }}>
                      💡 Login required to purchase items
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </main>

      {/* Login Modal */}
      {showLoginModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          zIndex: 10000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{
            background: 'white',
            borderRadius: '20px',
            padding: '0',
            maxWidth: '500px',
            width: '90%',
            maxHeight: '90%',
            overflow: 'auto',
            position: 'relative'
          }}>
            <button
              onClick={() => {
                setShowLoginModal(false);
                setSelectedItemForPurchase(null);
              }}
              style={{
                position: 'absolute',
                top: '1rem',
                right: '1rem',
                background: 'transparent',
                border: 'none',
                fontSize: '1.5rem',
                cursor: 'pointer',
                color: '#64748b',
                zIndex: 1
              }}
            >
              ✕
            </button>
            <Login />
          </div>
        </div>
      )}
    </div>
  );
};

export default PublicShop;