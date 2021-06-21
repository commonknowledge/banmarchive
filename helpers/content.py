from random import randint, shuffle
from django.contrib.contenttypes.models import ContentType
from django.db import models


def get_children_of_type(parent, *types):
    content_types = tuple(ContentType.objects.get_for_model(t) for t in types)
    return parent.get_children().filter(content_type__in=content_types)


def random_model(qs, count=None):
    if count == None:
        res = random_model(qs, count=1)
        return res[0] if len(res) != 0 else None

    qs_count = qs.count()
    indexes = list(range(0, max(qs_count, count)))
    shuffle(indexes)

    return tuple(qs[i].specific for i in indexes[:min(qs_count, count)])
