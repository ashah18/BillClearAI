class ContentSecurityPolicyMiddleware:
    """
    Adds Content-Security-Policy headers to every response.

    Django admin gets a permissive policy (needs inline scripts/styles).
    All other paths (REST API, OAuth redirects) get a strict no-content policy.
    """

    # Permissive CSP for the Django admin UI
    ADMIN_CSP = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self';"
    )

    # Strict CSP for API responses — no renderable content expected
    API_CSP = "default-src 'none'; frame-ancestors 'none';"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/admin"):
            response["Content-Security-Policy"] = self.ADMIN_CSP
        else:
            response["Content-Security-Policy"] = self.API_CSP
        return response
