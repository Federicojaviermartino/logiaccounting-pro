import { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

// Use sessionStorage instead of localStorage to limit token exposure.
// sessionStorage is cleared when the browser tab closes, reducing the
// window for XSS-based token exfiltration.
const tokenStorage = sessionStorage;

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setTokenState] = useState(null);
  const [loading, setLoading] = useState(true);

  const isAuthenticated = !!user && !!token;

  useEffect(() => {
    // Migration: move tokens from localStorage to sessionStorage
    const legacyToken = localStorage.getItem('token');
    if (legacyToken) {
      tokenStorage.setItem('token', legacyToken);
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }

    const savedToken = tokenStorage.getItem('token');
    const savedUser = tokenStorage.getItem('user');

    if (savedToken && savedUser) {
      try {
        const userData = JSON.parse(savedUser);
        setUser(userData);
        setTokenState(savedToken);
        api.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`;
      } catch (e) {
        tokenStorage.removeItem('token');
        tokenStorage.removeItem('user');
      }
    }
    setLoading(false);
  }, []);

  const setToken = (newToken) => {
    setTokenState(newToken);
    if (newToken) {
      tokenStorage.setItem('token', newToken);
      api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
    } else {
      tokenStorage.removeItem('token');
      delete api.defaults.headers.common['Authorization'];
    }
  };

  const login = async (email, password) => {
    const response = await api.post('/api/v1/auth/login', { email, password });
    const { token: newToken, user: userData } = response.data;

    setToken(newToken);
    tokenStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const logout = async () => {
    try {
      await api.post('/api/v1/auth/logout');
    } catch (e) {
      // Ignore logout errors
    }
    tokenStorage.removeItem('token');
    tokenStorage.removeItem('user');
    delete api.defaults.headers.common['Authorization'];
    setTokenState(null);
    setUser(null);
  };

  const updateUser = (userData) => {
    setUser(userData);
    tokenStorage.setItem('user', JSON.stringify(userData));
  };

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated, loading, login, logout, updateUser, setUser, setToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
