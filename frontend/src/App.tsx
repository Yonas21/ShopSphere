import React from 'react';
import { AppProvider, useApp } from './contexts/AppContext';
import { CartProvider } from './contexts/CartContext';
import { PaymentProvider } from './contexts/PaymentContext';
import PublicShop from './components/PublicShop';
import AdminPanel from './components/AdminPanel';
import CustomerPanel from './components/CustomerPanel';
import UserProfile from './components/UserProfile';
import NotificationSystem from './components/NotificationSystem';
import './App.css';

// Main App Component with Context Integration
const AppContent: React.FC = () => {
  const { state: appState, logout } = useApp();
  const [isProfileOpen, setIsProfileOpen] = React.useState(false);

  if (!appState.isAuthenticated) {
    return <PublicShop />;
  }

  if (appState.isLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '50px',
            height: '50px',
            border: '4px solid rgba(255, 255, 255, 0.3)',
            borderTop: '4px solid white',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px'
          }}></div>
          <p style={{ fontSize: '18px', fontWeight: '500' }}>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <CartProvider>
      <PaymentProvider>
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
                    {appState.user?.role === 'admin' ? 'Admin Dashboard' : 'Your Shopping Destination'}
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
                    {appState.user?.username}
                  </p>
                  <p style={{ 
                    margin: 0, 
                    color: 'rgba(255, 255, 255, 0.7)', 
                    fontSize: '0.8rem',
                    textTransform: 'capitalize'
                  }}>
                    {appState.user?.role}
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
                  onClick={logout}
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
            {appState.user?.role === 'admin' ? (
              <AdminPanel token={appState.token!} />
            ) : (
              <CustomerPanel token={appState.token!} currentUser={appState.user} />
            )}
          </main>
          
          {/* User Profile Modal */}
          <UserProfile 
            token={appState.token!}
            currentUser={appState.user!}
            isOpen={isProfileOpen}
            onClose={() => setIsProfileOpen(false)}
            onUserUpdate={(user) => {
              // User update is now handled by the context
            }}
          />
          
          {/* Notification System */}
          <NotificationSystem />
        </div>
      </PaymentProvider>
    </CartProvider>
  );
};

// Root App Component with Providers
function App() {
  return (
    <AppProvider>
      <AppContent />
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </AppProvider>
  );
}

export default App;
