from rest_framework import routers

_router = routers.DefaultRouter()


def api_route(path):
    def decorate(viewset):
        _router.register(path, viewset)

    return decorate


def get_urls():
    import publications.rest

    return _router.urls
