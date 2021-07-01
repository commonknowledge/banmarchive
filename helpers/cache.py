from django.core.cache import cache


def django_cached(ns, ttl=500):
    def decorator(fn):
        def cached_fn(*args, **kwargs):
            hit = cache.get(ns)
            if hit is None:
                hit = fn(*args, **kwargs)
                cache.set(ns, hit, ttl)

            return hit

        return cached_fn

    return decorator
