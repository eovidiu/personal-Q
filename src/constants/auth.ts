/**
 * Authentication constants shared across the application
 */

/**
 * LocalStorage key for storing JWT authentication token
 */
export const TOKEN_STORAGE_KEY = 'personal_q_token';

/**
 * API base URL - configurable via environment variable
 * Falls back to localhost for development
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Check if a JWT token is expired
 * @param token - JWT token string
 * @returns true if token is expired or invalid
 */
export function isTokenExpired(token: string): boolean {
  try {
    // Decode JWT payload (middle part)
    const payload = JSON.parse(atob(token.split('.')[1]));

    // Check expiration (exp is in seconds, Date.now() is in milliseconds)
    const isExpired = payload.exp * 1000 < Date.now();

    return isExpired;
  } catch (error) {
    // If token can't be decoded, consider it expired
    return true;
  }
}
