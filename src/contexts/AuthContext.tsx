import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
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
  verifySession: () => Promise<boolean>;  // HIGH-003: Cookie-based auth verification
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(() => {
    // LOW-003 fix: Use sessionStorage instead of localStorage for auth state
    // The actual JWT is in HttpOnly cookie (HIGH-003), this is just a UI state marker
    // sessionStorage clears on tab close, reducing XSS attack window
    return sessionStorage.getItem(TOKEN_STORAGE_KEY);
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Verify session on mount via HttpOnly cookie
  // LOW-003 fix: Primary auth is via cookie, sessionStorage is just UI state
  useEffect(() => {
    const verifySession = async () => {
      try {
        // Try to verify via HttpOnly cookie first (primary auth method)
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
          credentials: 'include',  // Include HttpOnly cookie
        });

        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
          setTokenState('cookie-auth');
          sessionStorage.setItem(TOKEN_STORAGE_KEY, 'cookie-auth');
        } else {
          // No valid session
          sessionStorage.removeItem(TOKEN_STORAGE_KEY);
          setTokenState(null);
          setUser(null);
          if (response.status === 401) {
            // Only show error if user was previously logged in
            const hadSession = sessionStorage.getItem(TOKEN_STORAGE_KEY);
            if (hadSession) {
              setError('Session expired. Please log in again.');
            }
          }
        }
      } catch (error) {
        console.error('Session verification failed:', error);
        sessionStorage.removeItem(TOKEN_STORAGE_KEY);
        setTokenState(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    verifySession();
  }, []);

  /**
   * LOW-003 fix: setToken is kept for backwards compatibility with test flows.
   * In production OAuth flow, JWT is set in HttpOnly cookie by the backend.
   * This function is primarily for development/testing scenarios.
   */
  const setToken = useCallback(async (newToken: string): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      // For cookie-auth marker or actual tokens in test mode
      if (newToken === 'cookie-auth') {
        sessionStorage.setItem(TOKEN_STORAGE_KEY, newToken);
        setTokenState(newToken);
        // Verify via cookie
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
          credentials: 'include',
        });
        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        } else {
          throw new Error('Failed to verify session');
        }
      } else {
        // Test mode: actual token (only works in development)
        if (isTokenExpired(newToken)) {
          throw new Error('Token is expired');
        }
        sessionStorage.setItem(TOKEN_STORAGE_KEY, newToken);
        setTokenState(newToken);
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
          headers: { 'Authorization': `Bearer ${newToken}` },
        });
        if (!response.ok) {
          throw new Error('Failed to fetch user info');
        }
        const userData = await response.json();
        setUser(userData);
      }
    } catch (error) {
      console.error('Failed to set token:', error);
      sessionStorage.removeItem(TOKEN_STORAGE_KEY);
      setTokenState(null);
      setError('Authentication failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(() => {
    // Clear any existing errors
    setError(null);
    // Redirect to backend OAuth endpoint
    window.location.href = `${API_BASE_URL}/api/v1/auth/login`;
  }, []);

  const logout = useCallback(async () => {
    try {
      setError(null);
      // Issue #111: Get CSRF token from cookie for defense-in-depth protection
      const csrfToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_token='))
        ?.split('=')[1];

      // Call backend logout with credentials to clear HttpOnly cookie
      await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
        method: 'POST',
        credentials: 'include',  // HIGH-003: Include cookies for proper logout
        headers: {
          'X-CSRF-Token': csrfToken || '',  // Issue #111: Send CSRF token
        },
      });
    } catch (error) {
      console.error('Logout error:', error);
      // Don't show error to user for logout failures
    } finally {
      // LOW-003: Clear sessionStorage state
      sessionStorage.removeItem(TOKEN_STORAGE_KEY);
      setTokenState(null);
      setUser(null);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * HIGH-003 fix: Verify session via HttpOnly cookie.
   * LOW-003 fix: Uses sessionStorage for UI state marker.
   * Called after OAuth callback to check if authentication succeeded.
   * Returns true if authenticated, false otherwise.
   */
  const verifySession = useCallback(async (): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);

      // Call /auth/me with credentials to include HttpOnly cookie
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
        credentials: 'include',  // Include cookies in request
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        // Set a marker token for isAuthenticated check (actual token is in HttpOnly cookie)
        setTokenState('cookie-auth');
        sessionStorage.setItem(TOKEN_STORAGE_KEY, 'cookie-auth');
        return true;
      } else {
        setUser(null);
        setTokenState(null);
        sessionStorage.removeItem(TOKEN_STORAGE_KEY);
        return false;
      }
    } catch (error) {
      console.error('Session verification failed:', error);
      setUser(null);
      setTokenState(null);
      sessionStorage.removeItem(TOKEN_STORAGE_KEY);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: !!token && !!user,
    error,
    login,
    logout,
    setToken,
    verifySession,
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
