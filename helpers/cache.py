from django.core.cache import cache


def django_cached(ns, get_key=None, ttl=500):
    def decorator(fn):
        def cached_fn(*args, **kwargs):
            key = ns
            if get_key != None:
                key += '.' + str(get_key(*args, **kwargs))

            hit = cache.get(key)
            if hit is None:
                hit = fn(*args, **kwargs)
                cache.set(key, hit, ttl)

            return hit

        return cached_fn

    return decorator
