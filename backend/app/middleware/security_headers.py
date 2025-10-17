"""
ABOUTME: Security headers middleware for protecting against common web vulnerabilities.
ABOUTME: Implements CSP, HSTS, clickjacking protection, and other security headers.
"""

import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all HTTP responses."""

    async def dispatch(self, request: Request, call_next):
        """Process request and add security headers to response."""
        response = await call_next(request)

        # Prevent clickjacking - don't allow embedding in iframes
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        # Note: In production, customize based on your actual needs
        csp_parts = [
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",  # 'unsafe-inline' needed for some UI frameworks
            "img-src 'self' data: https:",
            "font-src 'self'",
            "connect-src 'self' https://api.anthropic.com ws: wss:",  # Allow WebSocket and Anthropic API
            "frame-ancestors 'none'",  # Don't allow embedding
            "base-uri 'self'",
            "form-action 'self'",
        ]

        # Only enforce strict CSP in production
        if settings.env == "production":
            response.headers["Content-Security-Policy"] = "; ".join(csp_parts)
        else:
            # Report-only mode for development
            response.headers["Content-Security-Policy-Report-Only"] = "; ".join(csp_parts)

        # HTTPS enforcement (HSTS) - only in production with HTTPS
        if settings.env == "production":
            # max-age=31536000 (1 year)
            # includeSubDomains: Apply to all subdomains
            # preload: Allow inclusion in browser HSTS preload lists
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Referrer Policy - control what referrer information is sent
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy - disable unnecessary browser features
        permissions = [
            "geolocation=()",  # No geolocation
            "microphone=()",  # No microphone
            "camera=()",  # No camera
            "payment=()",  # No payment APIs
            "usb=()",  # No USB access
            "magnetometer=()",  # No magnetometer
            "gyroscope=()",  # No gyroscope
            "accelerometer=()",  # No accelerometer
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)

        # Additional cache control for sensitive endpoints
        if "/api/settings" in str(request.url) or "/api/agents" in str(request.url):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response
