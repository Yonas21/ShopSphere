import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import axios from 'axios';
import { useApp } from './AppContext';

// Types
export interface CartItem {
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

export interface CartState {
  items: CartItem[];
  totalItems: number;
  totalPrice: number;
  isLoading: boolean;
  error: string | null;
  isOpen: boolean;
  lastUpdated: string | null;
}

// Actions
export type CartAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'LOAD_CART_SUCCESS'; payload: { items: CartItem[]; total_items: number; total_price: number } }
  | { type: 'ADD_ITEM_SUCCESS'; payload: CartItem }
  | { type: 'UPDATE_ITEM_SUCCESS'; payload: { itemId: number; quantity: number } }
  | { type: 'REMOVE_ITEM_SUCCESS'; payload: number }
  | { type: 'CLEAR_CART_SUCCESS' }
  | { type: 'TOGGLE_CART' }
  | { type: 'OPEN_CART' }
  | { type: 'CLOSE_CART' }
  | { type: 'CHECKOUT_SUCCESS' };

// Initial state
const initialState: CartState = {
  items: [],
  totalItems: 0,
  totalPrice: 0,
  isLoading: false,
  error: null,
  isOpen: false,
  lastUpdated: null
};

// Reducer
const cartReducer = (state: CartState, action: CartAction): CartState => {
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

    case 'LOAD_CART_SUCCESS':
      return {
        ...state,
        items: action.payload.items,
        totalItems: action.payload.total_items,
        totalPrice: action.payload.total_price,
        isLoading: false,
        error: null,
        lastUpdated: new Date().toISOString()
      };

    case 'ADD_ITEM_SUCCESS':
      const existingItem = state.items.find(item => item.item_id === action.payload.item_id);
      
      if (existingItem) {
        // Update existing item
        const updatedItems = state.items.map(item =>
          item.item_id === action.payload.item_id
            ? { ...item, quantity: action.payload.quantity, subtotal: action.payload.subtotal }
            : item
        );
        
        return {
          ...state,
          items: updatedItems,
          totalItems: updatedItems.reduce((sum, item) => sum + item.quantity, 0),
          totalPrice: updatedItems.reduce((sum, item) => sum + item.subtotal, 0),
          lastUpdated: new Date().toISOString()
        };
      } else {
        // Add new item
        const newItems = [...state.items, action.payload];
        return {
          ...state,
          items: newItems,
          totalItems: newItems.reduce((sum, item) => sum + item.quantity, 0),
          totalPrice: newItems.reduce((sum, item) => sum + item.subtotal, 0),
          lastUpdated: new Date().toISOString()
        };
      }

    case 'UPDATE_ITEM_SUCCESS':
      const itemsAfterUpdate = state.items.map(item =>
        item.id === action.payload.itemId
          ? { ...item, quantity: action.payload.quantity, subtotal: item.item_price * action.payload.quantity }
          : item
      );
      
      return {
        ...state,
        items: itemsAfterUpdate,
        totalItems: itemsAfterUpdate.reduce((sum, item) => sum + item.quantity, 0),
        totalPrice: itemsAfterUpdate.reduce((sum, item) => sum + item.subtotal, 0),
        lastUpdated: new Date().toISOString()
      };

    case 'REMOVE_ITEM_SUCCESS':
      const itemsAfterRemoval = state.items.filter(item => item.id !== action.payload);
      
      return {
        ...state,
        items: itemsAfterRemoval,
        totalItems: itemsAfterRemoval.reduce((sum, item) => sum + item.quantity, 0),
        totalPrice: itemsAfterRemoval.reduce((sum, item) => sum + item.subtotal, 0),
        lastUpdated: new Date().toISOString()
      };

    case 'CLEAR_CART_SUCCESS':
      return {
        ...state,
        items: [],
        totalItems: 0,
        totalPrice: 0,
        lastUpdated: new Date().toISOString()
      };

    case 'TOGGLE_CART':
      return {
        ...state,
        isOpen: !state.isOpen
      };

    case 'OPEN_CART':
      return {
        ...state,
        isOpen: true
      };

    case 'CLOSE_CART':
      return {
        ...state,
        isOpen: false
      };

    case 'CHECKOUT_SUCCESS':
      return {
        ...state,
        items: [],
        totalItems: 0,
        totalPrice: 0,
        isOpen: false,
        lastUpdated: new Date().toISOString()
      };

    default:
      return state;
  }
};

// Context
interface CartContextType {
  state: CartState;
  dispatch: React.Dispatch<CartAction>;
  loadCart: () => Promise<void>;
  addToCart: (itemId: number, quantity?: number) => Promise<void>;
  updateQuantity: (cartItemId: number, quantity: number) => Promise<void>;
  removeFromCart: (cartItemId: number) => Promise<void>;
  clearCart: () => Promise<void>;
  checkout: () => Promise<any>;
  toggleCart: () => void;
  openCart: () => void;
  closeCart: () => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

// Provider
interface CartProviderProps {
  children: ReactNode;
}

export const CartProvider: React.FC<CartProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(cartReducer, initialState);
  const { state: appState, showNotification } = useApp();

  const API_BASE_URL = 'http://localhost:8001';

  // Load cart from API
  const loadCart = async (): Promise<void> => {
    if (!appState.isAuthenticated) {
      return;
    }

    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const response = await axios.get(`${API_BASE_URL}/api/cart/`);
      
      dispatch({
        type: 'LOAD_CART_SUCCESS',
        payload: response.data
      });

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to load cart';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      
      if (error.response?.status !== 401) {
        showNotification({
          type: 'error',
          message: errorMessage
        });
      }
    }
  };

  // Add item to cart
  const addToCart = async (itemId: number, quantity: number = 1): Promise<void> => {
    if (!appState.isAuthenticated) {
      showNotification({
        type: 'error',
        message: 'Please login to add items to cart'
      });
      return;
    }

    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const response = await axios.post(`${API_BASE_URL}/api/cart/add`, {
        item_id: itemId,
        quantity
      });

      // Reload cart to get updated data
      await loadCart();

      showNotification({
        type: 'success',
        message: 'Item added to cart!'
      });

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to add item to cart';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      
      showNotification({
        type: 'error',
        message: errorMessage
      });
    }
  };

  // Update item quantity
  const updateQuantity = async (cartItemId: number, quantity: number): Promise<void> => {
    if (quantity <= 0) {
      await removeFromCart(cartItemId);
      return;
    }

    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      await axios.put(`${API_BASE_URL}/api/cart/${cartItemId}`, {
        quantity
      });

      dispatch({
        type: 'UPDATE_ITEM_SUCCESS',
        payload: { itemId: cartItemId, quantity }
      });

      dispatch({ type: 'SET_LOADING', payload: false });

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to update quantity';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      
      showNotification({
        type: 'error',
        message: errorMessage
      });
    }
  };

  // Remove item from cart
  const removeFromCart = async (cartItemId: number): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      await axios.delete(`${API_BASE_URL}/api/cart/${cartItemId}`);

      dispatch({
        type: 'REMOVE_ITEM_SUCCESS',
        payload: cartItemId
      });

      dispatch({ type: 'SET_LOADING', payload: false });

      showNotification({
        type: 'success',
        message: 'Item removed from cart'
      });

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to remove item';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      
      showNotification({
        type: 'error',
        message: errorMessage
      });
    }
  };

  // Clear entire cart
  const clearCart = async (): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      await axios.delete(`${API_BASE_URL}/api/cart/`);

      dispatch({ type: 'CLEAR_CART_SUCCESS' });
      dispatch({ type: 'SET_LOADING', payload: false });

      showNotification({
        type: 'success',
        message: 'Cart cleared'
      });

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to clear cart';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      
      showNotification({
        type: 'error',
        message: errorMessage
      });
    }
  };

  // Checkout
  const checkout = async (): Promise<any> => {
    if (state.items.length === 0) {
      showNotification({
        type: 'warning',
        message: 'Your cart is empty'
      });
      return;
    }

    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const response = await axios.post(`${API_BASE_URL}/api/cart/checkout`);
      
      dispatch({ type: 'CHECKOUT_SUCCESS' });

      showNotification({
        type: 'success',
        message: 'Orders created successfully!'
      });

      return response.data;

    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Checkout failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      
      showNotification({
        type: 'error',
        message: errorMessage
      });
      
      throw error;
    }
  };

  // Cart UI controls
  const toggleCart = (): void => {
    dispatch({ type: 'TOGGLE_CART' });
  };

  const openCart = (): void => {
    dispatch({ type: 'OPEN_CART' });
  };

  const closeCart = (): void => {
    dispatch({ type: 'CLOSE_CART' });
  };

  // Load cart when user logs in
  useEffect(() => {
    if (appState.isAuthenticated) {
      loadCart();
    } else {
      // Clear cart when user logs out
      dispatch({ type: 'CLEAR_CART_SUCCESS' });
    }
  }, [appState.isAuthenticated]);

  const contextValue: CartContextType = {
    state,
    dispatch,
    loadCart,
    addToCart,
    updateQuantity,
    removeFromCart,
    clearCart,
    checkout,
    toggleCart,
    openCart,
    closeCart
  };

  return (
    <CartContext.Provider value={contextValue}>
      {children}
    </CartContext.Provider>
  );
};

// Hook
export const useCart = (): CartContextType => {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

export default CartContext;