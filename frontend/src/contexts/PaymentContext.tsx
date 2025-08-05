import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import axios from 'axios';
import { useApp } from './AppContext';

// Types
export interface Payment {
  id: number;
  purchase_id: number;
  user_id: number;
  amount: number;
  currency: string;
  status: 'pending' | 'processing' | 'succeeded' | 'failed' | 'cancelled' | 'refunded' | 'partially_refunded';
  provider: 'stripe' | 'paypal';
  provider_payment_id?: string;
  provider_charge_id?: string;
  payment_method?: string;
  payment_metadata?: any;
  failure_code?: string;
  failure_message?: string;
  created_at: string;
  updated_at?: string;
  succeeded_at?: string;
  failed_at?: string;
}

export interface PaymentIntent {
  payment_id: number;
  client_secret?: string;
  approval_url?: string;
  provider_payment_id: string;
  amount: number;
  currency: string;
  status: string;
}

export interface PaymentState {
  currentPayment: Payment | null;
  paymentIntent: PaymentIntent | null;
  paymentHistory: Payment[];
  isLoading: boolean;
  error: string | null;
  isPaymentModalOpen: boolean;
  selectedProvider: 'stripe' | 'paypal';
  processingPurchaseId: number | null;
}

// Actions
export type PaymentAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_CURRENT_PAYMENT'; payload: Payment | null }
  | { type: 'SET_PAYMENT_INTENT'; payload: PaymentIntent | null }
  | { type: 'SET_PAYMENT_HISTORY'; payload: Payment[] }
  | { type: 'ADD_TO_HISTORY'; payload: Payment }
  | { type: 'UPDATE_PAYMENT_STATUS'; payload: { paymentId: number; status: string } }
  | { type: 'OPEN_PAYMENT_MODAL'; payload: { purchaseId: number; provider?: 'stripe' | 'paypal' } }
  | { type: 'CLOSE_PAYMENT_MODAL' }
  | { type: 'SET_PROVIDER'; payload: 'stripe' | 'paypal' }
  | { type: 'PAYMENT_SUCCESS' }
  | { type: 'PAYMENT_FAILURE'; payload: string }
  | { type: 'RESET_PAYMENT_STATE' };

// Initial state
const initialState: PaymentState = {
  currentPayment: null,
  paymentIntent: null,
  paymentHistory: [],
  isLoading: false,
  error: null,
  isPaymentModalOpen: false,
  selectedProvider: 'stripe',
  processingPurchaseId: null
};

// Reducer
const paymentReducer = (state: PaymentState, action: PaymentAction): PaymentState => {
  switch (action.type) {
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false
      };

    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null
      };

    case 'SET_CURRENT_PAYMENT':
      return {
        ...state,
        currentPayment: action.payload
      };

    case 'SET_PAYMENT_INTENT':
      return {
        ...state,
        paymentIntent: action.payload,
        isLoading: false
      };

    case 'SET_PAYMENT_HISTORY':
      return {
        ...state,
        paymentHistory: action.payload
      };

    case 'ADD_TO_HISTORY':
      return {
        ...state,
        paymentHistory: [action.payload, ...state.paymentHistory]
      };

    case 'UPDATE_PAYMENT_STATUS':
      return {
        ...state,
        paymentHistory: state.paymentHistory.map(payment =>
          payment.id === action.payload.paymentId
            ? { ...payment, status: action.payload.status as any }
            : payment
        ),
        currentPayment: state.currentPayment?.id === action.payload.paymentId
          ? { ...state.currentPayment, status: action.payload.status as any }
          : state.currentPayment
      };

    case 'OPEN_PAYMENT_MODAL':
      return {
        ...state,
        isPaymentModalOpen: true,
        processingPurchaseId: action.payload.purchaseId,
        selectedProvider: action.payload.provider || 'stripe',
        error: null
      };

    case 'CLOSE_PAYMENT_MODAL':
      return {
        ...state,
        isPaymentModalOpen: false,
        processingPurchaseId: null,
        paymentIntent: null,
        error: null
      };

    case 'SET_PROVIDER':
      return {
        ...state,
        selectedProvider: action.payload
      };

    case 'PAYMENT_SUCCESS':
      return {
        ...state,
        isPaymentModalOpen: false,
        processingPurchaseId: null,
        paymentIntent: null,
        error: null,
        isLoading: false
      };

    case 'PAYMENT_FAILURE':
      return {
        ...state,
        error: action.payload,
        isLoading: false
      };

    case 'RESET_PAYMENT_STATE':
      return {
        ...initialState,
        paymentHistory: state.paymentHistory
      };

    default:
      return state;
  }
};

// Context
interface PaymentContextType {
  state: PaymentState;
  dispatch: React.Dispatch<PaymentAction>;
  createPaymentIntent: (purchaseId: number, provider: 'stripe' | 'paypal') => Promise<PaymentIntent>;
  confirmPayment: (paymentId: number) => Promise<void>;
  loadPaymentHistory: () => Promise<void>;
  getPaymentsByPurchase: (purchaseId: number) => Promise<Payment[]>;
  openPaymentModal: (purchaseId: number, provider?: 'stripe' | 'paypal') => void;
  closePaymentModal: () => void;
  setProvider: (provider: 'stripe' | 'paypal') => void;
  processStripePayment: (paymentIntent: PaymentIntent) => Promise<void>;
  processPayPalPayment: (paymentIntent: PaymentIntent) => void;
  resetPaymentState: () => void;
}

const PaymentContext = createContext<PaymentContextType | undefined>(undefined);

// Provider
interface PaymentProviderProps {
  children: ReactNode;
}

export const PaymentProvider: React.FC<PaymentProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(paymentReducer, initialState);
  const { state: appState, showNotification } = useApp();

  const API_BASE_URL = 'http://localhost:8001';

  // Create payment intent
  const createPaymentIntent = async (purchaseId: number, provider: 'stripe' | 'paypal'): Promise<PaymentIntent> => {
    if (!appState.isAuthenticated) {
      throw new Error('User not authenticated');
    }

    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'CLEAR_ERROR' });

      const response = await axios.post(`${API_BASE_URL}/api/payments/intent`, {
        purchase_id: purchaseId,
        provider: provider,
        payment_method_type: 'card',
        return_url: `${window.location.origin}/payment/success/${provider}`,
        payment_metadata: {
          purchase_id: purchaseId.toString()
        }
      });

      const paymentIntent = response.data;
      
      dispatch({
        type: 'SET_PAYMENT_INTENT',
        payload: paymentIntent
      });

      return paymentIntent;

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to create payment intent';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      
      showNotification({
        type: 'error',
        message: errorMessage
      });
      
      throw error;
    }
  };

  // Confirm payment (for PayPal)
  const confirmPayment = async (paymentId: number): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      const response = await axios.post(`${API_BASE_URL}/api/payments/confirm/${paymentId}`);

      if (response.data.status === 'success') {
        dispatch({ type: 'PAYMENT_SUCCESS' });
        
        showNotification({
          type: 'success',
          message: 'Payment confirmed successfully!'
        });

        // Reload payment history
        await loadPaymentHistory();
      }

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Payment confirmation failed';
      dispatch({ type: 'PAYMENT_FAILURE', payload: errorMessage });
      
      showNotification({
        type: 'error',
        message: errorMessage
      });
      
      throw error;
    }
  };

  // Load payment history
  const loadPaymentHistory = async (): Promise<void> => {
    if (!appState.isAuthenticated) {
      return;
    }

    try {
      const response = await axios.get(`${API_BASE_URL}/api/payments/`);
      
      dispatch({
        type: 'SET_PAYMENT_HISTORY',
        payload: response.data
      });

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to load payment history';
      
      if (error.response?.status !== 401) {
        showNotification({
          type: 'error',
          message: errorMessage
        });
      }
    }
  };

  // Get payments by purchase
  const getPaymentsByPurchase = async (purchaseId: number): Promise<Payment[]> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/payments/purchase/${purchaseId}`);
      return response.data;

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to load payments';
      
      showNotification({
        type: 'error',
        message: errorMessage
      });
      
      return [];
    }
  };

  // Payment modal controls
  const openPaymentModal = (purchaseId: number, provider: 'stripe' | 'paypal' = 'stripe'): void => {
    dispatch({
      type: 'OPEN_PAYMENT_MODAL',
      payload: { purchaseId, provider }
    });
  };

  const closePaymentModal = (): void => {
    dispatch({ type: 'CLOSE_PAYMENT_MODAL' });
  };

  const setProvider = (provider: 'stripe' | 'paypal'): void => {
    dispatch({ type: 'SET_PROVIDER', payload: provider });
  };

  // Process Stripe payment
  const processStripePayment = async (paymentIntent: PaymentIntent): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      // Load Stripe.js
      const stripe = (window as any).Stripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);
      
      if (!stripe) {
        throw new Error('Stripe is not loaded');
      }

      const { error } = await stripe.confirmPayment({
        clientSecret: paymentIntent.client_secret,
        confirmParams: {
          return_url: `${window.location.origin}/payment/success/stripe`,
        },
      });

      if (error) {
        dispatch({ type: 'PAYMENT_FAILURE', payload: error.message || 'Payment failed' });
        
        showNotification({
          type: 'error',
          message: error.message || 'Payment failed'
        });
      } else {
        dispatch({ type: 'PAYMENT_SUCCESS' });
        
        showNotification({
          type: 'success',
          message: 'Payment processed successfully!'
        });

        // Reload payment history
        await loadPaymentHistory();
      }

    } catch (error: any) {
      dispatch({ type: 'PAYMENT_FAILURE', payload: error.message });
      
      showNotification({
        type: 'error',
        message: error.message
      });
    }
  };

  // Process PayPal payment
  const processPayPalPayment = (paymentIntent: PaymentIntent): void => {
    if (paymentIntent.approval_url) {
      // Redirect to PayPal for approval
      window.location.href = paymentIntent.approval_url;
    } else {
      dispatch({ type: 'PAYMENT_FAILURE', payload: 'Failed to get PayPal approval URL' });
      
      showNotification({
        type: 'error',
        message: 'Failed to get PayPal approval URL'
      });
    }
  };

  // Reset payment state
  const resetPaymentState = (): void => {
    dispatch({ type: 'RESET_PAYMENT_STATE' });
  };

  const contextValue: PaymentContextType = {
    state,
    dispatch,
    createPaymentIntent,
    confirmPayment,
    loadPaymentHistory,
    getPaymentsByPurchase,
    openPaymentModal,
    closePaymentModal,
    setProvider,
    processStripePayment,
    processPayPalPayment,
    resetPaymentState
  };

  return (
    <PaymentContext.Provider value={contextValue}>
      {children}
    </PaymentContext.Provider>
  );
};

// Hook
export const usePayment = (): PaymentContextType => {
  const context = useContext(PaymentContext);
  if (context === undefined) {
    throw new Error('usePayment must be used within a PaymentProvider');
  }
  return context;
};

export default PaymentContext;