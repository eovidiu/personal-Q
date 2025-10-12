import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { TOKEN_STORAGE_KEY, API_BASE_URL, isTokenExpired } from '@/constants/auth';

interface User {
  email: string;
  authenticated: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  login: () => void;
  logout: () => void;
  setToken: (token: string) => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(() => {
    // Initialize from localStorage
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Verify token on mount
  useEffect(() => {
    const verifyToken = async () => {
      const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY);

      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      // Check if token is expired before making API call
      if (isTokenExpired(storedToken)) {
        console.info('Token expired, clearing...');
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        setTokenState(null);
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
          headers: {
            'Authorization': `Bearer ${storedToken}`,
          },
        });

        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
          setTokenState(storedToken);
        } else {
          // Token invalid, clear it
          localStorage.removeItem(TOKEN_STORAGE_KEY);
          setTokenState(null);
          if (response.status === 401) {
            setError('Session expired. Please log in again.');
          }
        }
      } catch (error) {
        console.error('Token verification failed:', error);
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        setTokenState(null);
        setError('Authentication failed. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    verifyToken();
  }, []);

  const setToken = async (newToken: string): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      // Check token expiration before storing
      if (isTokenExpired(newToken)) {
        throw new Error('Token is expired');
      }

      localStorage.setItem(TOKEN_STORAGE_KEY, newToken);
      setTokenState(newToken);

      // Fetch user info with new token
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
        headers: {
          'Authorization': `Bearer ${newToken}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch user info');
      }

      const userData = await response.json();
      setUser(userData);
    } catch (error) {
      console.error('Failed to set token:', error);
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      setTokenState(null);
      setError('Authentication failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const login = () => {
    // Clear any existing errors
    setError(null);
    // Redirect to backend OAuth endpoint
    window.location.href = `${API_BASE_URL}/api/v1/auth/login`;
  };

  const logout = async () => {
    try {
      setError(null);
      // Call backend logout
      await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
        },
      });
    } catch (error) {
      console.error('Logout error:', error);
      // Don't show error to user for logout failures
    } finally {
      // Clear local state regardless
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      setTokenState(null);
      setUser(null);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: !!token && !!user,
    error,
    login,
    logout,
    setToken,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
