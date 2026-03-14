"""
Custom middleware for CourseTracker.
Sustainability improvements: cache-control headers, security headers.
[Day 12 - Sustainability]
"""


class CacheControlMiddleware:
    """
    Adds Cache-Control headers to responses to reduce unnecessary
    network requests and improve Lighthouse performance score.

    - Static-like pages (login, register) get short cache with revalidation.
    - Dynamic pages get no-cache to ensure fresh data.
    - All pages get ETag support via Django's ConditionalGetMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Don't override if Cache-Control is already set
        if 'Cache-Control' in response:
            return response

        # Static-like auth pages: cache briefly with revalidation
        path = request.path
        if path in ('/accounts/login/', '/accounts/register/'):
            response['Cache-Control'] = 'public, max-age=300, must-revalidate'
        else:
            # Dynamic pages: no cache to ensure fresh data
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'

        return response


class SecurityHeadersMiddleware:
    """
    Adds additional security headers recommended by Lighthouse.
    These supplement Django's built-in security middleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Prevent MIME-type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        # Referrer policy for privacy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Permissions Policy - disable unused browser features
        response['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), '
            'payment=(), usb=(), magnetometer=()'
        )
        return response
