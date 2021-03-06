from random import randint, shuffle
from django.contrib.contenttypes.models import ContentType
from django.db import models


def get_children_of_type(parent, *types):
    if len(types) == 1:
        t = types[0]
        return t.objects.live().child_of(parent).specific()

    content_types = tuple(ContentType.objects.get_for_model(t) for t in types)
    return parent.get_children().filter(content_type__in=content_types).specific()


def random_model(qs, count=None):
    if count == None:
        res = random_model(qs, count=1)
        return res[0] if len(res) != 0 else None

    qs_count = qs.count()
    indexes = list(range(0, max(qs_count, count)))
    shuffle(indexes)

    try:
        return tuple(qs[i].specific for i in indexes[:min(qs_count, count)])
    except:
        return None


def get_page(request):
    page = request.GET.get('page', 1)
    return max(safe_to_int(page), 1)


def safe_to_int(x):
    try:
        return int(x)
    except:
        pass
