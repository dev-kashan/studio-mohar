from django.http import HttpResponsePermanentRedirect


class RemoveWwwMiddleware:
    """Send www.studiomohar.ca/... to studiomohar.ca/... with a permanent (301) redirect,
    so the site only lives on one address (better for SEO).

    - Must be FIRST in settings.MIDDLEWARE.
    - Both addresses must be in ALLOWED_HOSTS (the www one still has to reach Django
      to be forwarded). get_host() checks that, so no redirect to an unknown host.
    - Do not set PREPEND_WWW = True, or the two settings would loop.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        if host.lower().startswith('www.'):
            new_host = host[4:]
            return HttpResponsePermanentRedirect(f'https://{new_host}{request.get_full_path()}')
        return self.get_response(request)
