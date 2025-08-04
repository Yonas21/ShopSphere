import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Login from './components/Login';
import PublicShop from './components/PublicShop';
import AdminPanel from './components/AdminPanel';
import CustomerPanel from './components/CustomerPanel';
import UserProfile from './components/UserProfile';
import './App.css';

interface User {
  id: number;
  email: string;
  username: string;
  role: 'customer' | 'admin';
  is_active: boolean;
}

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
  purchase_date: string;
  item_name?: string;
  customer_username?: string;
}

function App() {
  const [message, setMessage] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const API_BASE_URL = 'http://localhost:8000';

  useEffect(() => {
    fetchMessage();
    checkAuthStatus();
  }, []);

  const checkAuthStatus = () => {
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (savedToken && savedUser) {
      setToken(savedToken);
      setCurrentUser(JSON.parse(savedUser));
      setIsAuthenticated(true);
    }
  };

  const fetchMessage = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/`);
      setMessage(response.data.message);
    } catch (error) {
      console.error('Error fetching message:', error);
    }
  };

  const handleLogin = (accessToken: string, user: User) => {
    setToken(accessToken);
    setCurrentUser(user);
    setIsAuthenticated(true);
    localStorage.setItem('token', accessToken);
    localStorage.setItem('user', JSON.stringify(user));
  };

  const handleLogout = () => {
    setToken(null);
    setCurrentUser(null);
    setIsAuthenticated(false);
    setIsProfileOpen(false);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  const handleUserUpdate = (updatedUser: User) => {
    setCurrentUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
  };

  if (!isAuthenticated) {
    return <PublicShop onLogin={handleLogin} />;
  }

  return (
    <div className="App" style={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
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
                {currentUser?.role === 'admin' ? 'Admin Dashboard' : 'Your Shopping Destination'}
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ textAlign: 'right' }}>
              <p style={{ 
                margin: 0, 
                color: 'white', 
                fontSize: '1rem',
                fontWeight: '500'
              }}>
                {currentUser?.username}
              </p>
              <p style={{ 
                margin: 0, 
                color: 'rgba(255, 255, 255, 0.7)', 
                fontSize: '0.8rem',
                textTransform: 'capitalize'
              }}>
                {currentUser?.role}
              </p>
            </div>
            <button 
              onClick={() => setIsProfileOpen(true)}
              style={{ 
                padding: '0.5rem 1rem',
                background: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: '500',
                transition: 'all 0.2s ease',
                backdropFilter: 'blur(10px)',
                marginRight: '0.5rem'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
              }}
            >
              👤 Profile
            </button>
            <button 
              onClick={handleLogout}
              style={{ 
                padding: '0.5rem 1rem',
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
              Logout
            </button>
          </div>
        </div>
      </header>
      
      <main>
        {currentUser?.role === 'admin' ? (
          <AdminPanel token={token!} />
        ) : (
          <CustomerPanel token={token!} currentUser={currentUser} />
        )}
      </main>
      
      {/* User Profile Modal */}
      <UserProfile 
        token={token!}
        currentUser={currentUser!}
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
        onUserUpdate={handleUserUpdate}
      />
    </div>
  );
}

export default App;
