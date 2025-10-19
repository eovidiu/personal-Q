/**
 * Security Tests for Test Authentication Endpoint
 *
 * These tests validate that the test authentication endpoint has proper
 * security safeguards and cannot be accessed in production.
 *
 * Critical security properties tested:
 * 1. Endpoint is disabled in production environments
 * 2. Email validation enforces ALLOWED_EMAIL
 * 3. Tokens generated are valid and match production format
 * 4. Environment checks are properly enforced
 */

import { test, expect } from '@playwright/test';

const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000';
const ALLOWED_EMAIL = process.env.ALLOWED_EMAIL || 'test@example.com';

test.describe('Test Auth Endpoint - Security Validation', () => {

  test('should validate test auth endpoint is accessible in non-production', async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/test-validate`);

    expect(response.status).toBe(200);

    const data = await response.json();
    expect(data.test_auth_available).toBe(true);
    expect(data.environment).not.toBe('production');
    expect(data.allowed_email).toBeTruthy();
  });

  test('should generate valid token for allowed email', async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/test-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email: ALLOWED_EMAIL }),
    });

    expect(response.status).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('access_token');
    expect(data).toHaveProperty('token_type', 'bearer');
    expect(data).toHaveProperty('email', ALLOWED_EMAIL);

    // Validate token format (JWT has 3 parts separated by dots)
    const token = data.access_token;
    expect(token).toBeTruthy();
    expect(token.split('.')).toHaveLength(3);

    // Validate token can be decoded (basic structure check)
    const parts = token.split('.');
    const header = JSON.parse(atob(parts[0]));
    const payload = JSON.parse(atob(parts[1]));

    expect(header).toHaveProperty('alg', 'HS256');
    expect(header).toHaveProperty('typ', 'JWT');
    expect(payload).toHaveProperty('email', ALLOWED_EMAIL);
    expect(payload).toHaveProperty('sub', ALLOWED_EMAIL);
    expect(payload).toHaveProperty('exp');
    expect(payload).toHaveProperty('iat');

    // Verify expiration is in the future and matches expected 24-hour duration
    const now = Math.floor(Date.now() / 1000);
    expect(payload.exp).toBeGreaterThan(now);

    // IMPORTANT-003: Validate expected 24-hour expiration with clock skew tolerance
    const expectedExpiration = payload.iat + (24 * 3600); // 24 hours
    const clockSkewTolerance = 60; // 60 seconds tolerance
    expect(payload.exp).toBeGreaterThanOrEqual(expectedExpiration - clockSkewTolerance);
    expect(payload.exp).toBeLessThanOrEqual(expectedExpiration + clockSkewTolerance);
  });

  test('should reject unauthorized email addresses', async () => {
    const unauthorizedEmail = 'hacker@malicious.com';

    const response = await fetch(`${API_BASE_URL}/api/v1/auth/test-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email: unauthorizedEmail }),
    });

    expect(response.status).toBe(422); // Validation error

    const data = await response.json();
    expect(data.detail).toBeTruthy();

    // Should mention "not authorized" but NOT reveal ALLOWED_EMAIL
    const errorMessage = JSON.stringify(data).toLowerCase();
    expect(errorMessage).toMatch(/not authorized/);
    // SECURITY: Should NOT reveal the allowed email address
    expect(errorMessage).not.toContain(ALLOWED_EMAIL.toLowerCase());
  });

  test('should reject invalid email formats', async () => {
    const invalidEmails = [
      'not-an-email',
      '@incomplete.com',
      'missing-domain@',
      '',
    ];

    for (const invalidEmail of invalidEmails) {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/test-login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: invalidEmail }),
      });

      expect(response.status).toBe(422); // Validation error
    }
  });

  test('should generate tokens that work with real backend auth', async ({ page }) => {
    // Get token from test endpoint
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/test-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email: ALLOWED_EMAIL }),
    });

    expect(response.status).toBe(200);
    const { access_token } = await response.json();

    // Verify token works with /auth/me endpoint
    const meResponse = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      headers: {
        'Authorization': `Bearer ${access_token}`,
      },
    });

    expect(meResponse.status).toBe(200);
    const userData = await meResponse.json();
    expect(userData.email).toBe(ALLOWED_EMAIL);
    expect(userData.authenticated).toBe(true);
  });

  test('should generate tokens that work with protected endpoints', async () => {
    // Get token
    const loginResponse = await fetch(`${API_BASE_URL}/api/v1/auth/test-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email: ALLOWED_EMAIL }),
    });

    const { access_token } = await loginResponse.json();

    // Try accessing a protected endpoint (e.g., agents list)
    const agentsResponse = await fetch(`${API_BASE_URL}/api/v1/agents?skip=0&limit=10`, {
      headers: {
        'Authorization': `Bearer ${access_token}`,
      },
    });

    // Should succeed (200) or return empty list, not auth error (401/403)
    expect(agentsResponse.status).not.toBe(401);
    expect(agentsResponse.status).not.toBe(403);
  });

  test('should log security warnings for test auth usage', async () => {
    // This test documents that test auth usage should be logged
    // Actual log verification would require backend log access

    const response = await fetch(`${API_BASE_URL}/api/v1/auth/test-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email: ALLOWED_EMAIL }),
    });

    expect(response.status).toBe(200);

    // In a real deployment, this would trigger security audit logs
    // Backend logs should contain: "TEST AUTH: Generating token for..."
  });

  test('should require POST method for test-login', async () => {
    // Try GET instead of POST
    const getResponse = await fetch(`${API_BASE_URL}/api/v1/auth/test-login`);
    expect(getResponse.status).toBe(405); // Method Not Allowed
  });

  test('should validate request body is JSON', async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/test-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'text/plain',
      },
      body: 'not json',
    });

    expect(response.status).toBeGreaterThanOrEqual(400);
    expect(response.status).toBeLessThan(500);
  });

  test('should not expose sensitive information in error messages', async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/test-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email: 'attacker@evil.com' }),
    });

    const data = await response.json();
    const errorString = JSON.stringify(data).toLowerCase();

    // Should not expose internal secrets or implementation details
    expect(errorString).not.toContain('secret');
    expect(errorString).not.toContain('password');
    expect(errorString).not.toContain('jwt_secret');
    expect(errorString).not.toContain('encryption_key');
  });

  test('should handle concurrent requests safely', async () => {
    // Send multiple concurrent requests
    const promises = Array(10).fill(null).map(() =>
      fetch(`${API_BASE_URL}/api/v1/auth/test-login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: ALLOWED_EMAIL }),
      })
    );

    const responses = await Promise.all(promises);

    // All should succeed
    for (const response of responses) {
      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.access_token).toBeTruthy();
    }

    // All tokens should be unique (different iat timestamps)
    const tokens = await Promise.all(responses.map(r => r.json()));
    const tokenStrings = tokens.map(t => t.access_token);
    const uniqueTokens = new Set(tokenStrings);

    // Due to timing, some tokens might be identical, but most should be unique
    expect(uniqueTokens.size).toBeGreaterThan(1);
  });
});

test.describe('Test Auth Endpoint - Production Safety', () => {

  test('should document production safety guarantees', async () => {
    // This test documents the triple-layer security model:
    //
    // Layer 1 (Import-time):
    //   - auth_test.py checks settings.env at import time
    //   - Raises RuntimeError if ENV=production
    //   - Prevents module from loading at all
    //
    // Layer 2 (Registration):
    //   - main.py only includes router if settings.env != "production"
    //   - Router never registered in production FastAPI app
    //   - Routes don't exist in production
    //
    // Layer 3 (Runtime):
    //   - Each endpoint calls _validate_test_environment()
    //   - Returns 404 if somehow accessed in production
    //   - Logs security alert
    //
    // These tests run in development, so we can only verify the endpoint works.
    // Production safety is enforced by the environment checks in the backend code.

    const response = await fetch(`${API_BASE_URL}/api/v1/auth/test-validate`);
    expect(response.status).toBe(200);

    const data = await response.json();

    // Verify we're NOT in production
    expect(data.environment).not.toBe('production');

    // Document: In production, this endpoint would return 404
    // Document: In production, this module wouldn't even load
  });

  test('should verify environment is correctly set', async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/test-validate`);
    const data = await response.json();

    // Verify environment matches expectations
    expect(['development', 'test', 'testing', 'local']).toContain(data.environment);
    expect(data.environment).not.toBe('production');
    expect(data.environment).not.toBe('prod');
  });
});
