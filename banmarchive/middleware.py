from django.conf import settings
from django.http.request import HttpRequest
from django.http.response import HttpResponseRedirect
from urllib.parse import urlparse


def canonical_host_redirect(get_response):
    '''
    Redirect to the primary host if reached via another
    '''

    # One-time configuration and initialization.

    def middleware(request: HttpRequest):
        if request.get_host() == settings.PRIMARY_HOST:
            return get_response(request)

        protocol = 'http' if settings.DEBUG else 'https'
        path = request.get_full_path()
        url = f'{protocol}://{settings.PRIMARY_HOST}{path}'

        return HttpResponseRedirect(url, 301 if settings.REDIRECT_PERMANENT else 302)

    return middleware
