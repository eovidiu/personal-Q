import { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

/**
 * AuthCallbackPage handles OAuth redirect from Google
 *
 * HIGH-003 fix: Now supports two authentication methods:
 * 1. HttpOnly cookie (OAuth flow) - verifySession checks auth via /me endpoint
 * 2. URL token (test auth) - setToken stores token for API calls
 *
 * Flow:
 * 1. Check for token in URL (test auth flow)
 * 2. If no token, verify session via HttpOnly cookie (OAuth flow)
 * 3. Redirect to dashboard on success
 * 4. Show error and redirect to login on failure
 *
 * SECURITY NOTES:
 * - Uses ref to prevent race conditions from multiple effect runs
 * - Cleans up timeouts to prevent memory leaks
 * - OAuth tokens are now in HttpOnly cookies (not exposed to JavaScript)
 */
export function AuthCallbackPage() {
  const { setToken, verifySession } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  // Prevent double processing due to React StrictMode or effect re-runs
  const hasProcessedRef = useRef(false);
  const redirectTimeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // Guard against multiple executions
    if (hasProcessedRef.current) {
      return;
    }

    const processAuthCallback = async () => {
      try {
        // Mark as processing to prevent race conditions
        hasProcessedRef.current = true;

        // Check for token in URL (test auth flow)
        const token = searchParams.get('token');

        if (token) {
          // Test auth flow: token passed in URL
          await setToken(token);
          navigate('/', { replace: true });
          return;
        }

        // HIGH-003 fix: OAuth flow - verify session via HttpOnly cookie
        const isAuthenticated = await verifySession();

        if (isAuthenticated) {
          // OAuth successful, redirect to dashboard
          navigate('/', { replace: true });
        } else {
          setError('Authentication failed. Please try again.');
          // Redirect to login after showing error briefly
          redirectTimeoutRef.current = setTimeout(() => {
            navigate('/login', { replace: true });
          }, 2000);
        }

      } catch (err) {
        console.error('Authentication callback error:', err);
        setError('Authentication failed. Please try again.');

        // Allow retry on error by resetting the flag
        hasProcessedRef.current = false;

        // Redirect to login after showing error briefly
        redirectTimeoutRef.current = setTimeout(() => {
          navigate('/login', { replace: true });
        }, 2000);
      }
    };

    processAuthCallback();

    // Cleanup timeout on unmount
    return () => {
      if (redirectTimeoutRef.current) {
        clearTimeout(redirectTimeoutRef.current);
      }
    };
  }, [searchParams, navigate, setToken, verifySession]);

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <div className="w-full max-w-md">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="ml-2">
              {error}
            </AlertDescription>
          </Alert>
          <p className="text-sm text-muted-foreground text-center mt-4">
            Redirecting to login...
          </p>
        </div>
      </div>
    );
  }

  // Show loading state during token processing
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
        <p className="text-muted-foreground">Completing authentication...</p>
      </div>
    </div>
  );
}
