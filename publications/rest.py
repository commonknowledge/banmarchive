from base64 import urlsafe_b64encode
from hashlib import sha256
import json
import tempfile
from typing import final
import uuid
from pathlib import Path
from tempfile import TemporaryFile, tempdir

from django.core.files.base import File
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.text import slugify
from rest_framework import viewsets, permissions, exceptions, response, parsers
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from wagtail.core.models import Page
from wagtail.documents.models import Document

from publications import serializers, models
from helpers.rest import api_route


PERMISSIONS_RULES = (permissions.DjangoModelPermissionsOrAnonReadOnly,)


class CreateOrUpdateMixin:
    identitfier_keys = ('parent', 'slug')

    def create(self, request):
        request_data = request.data
        if 'slug' in self.identitfier_keys and 'slug' not in request_data:
            if 'title' in request_data:
                qs = self.queryset.filter(title=request_data['title'])

                if isinstance(request_data.get('parent'), int):
                    qs = qs.child_of(Page.objects.get(
                        pk=request_data['parent']))

                hit = qs.first()
                if hit is None:
                    request_data['slug'] = slugify(request_data['title'])
                else:
                    request_data['slug'] = hit.slug

        request_serializer = self.get_serializer(data=request.data)
        if not request_serializer.is_valid():
            return response.Response(json.dumps(request_serializer.errors), status=400)

        data = request_serializer.validated_data

        identifiers = {}
        for key in self.identitfier_keys:
            identifiers[key] = data.pop(key)

        res = self.update_or_create(**identifiers, defaults=data)

        response_serializer = self.get_serializer(instance=res)
        return response.Response(response_serializer.data)

    @transaction.atomic
    def update_or_create(self, defaults, **identifiers):
        queryset = self.get_queryset()
        parent = identifiers.pop('parent', None)

        if parent is not None:
            try:
                model = parent.get_children().get(**identifiers).specific
                for key, val in defaults.items():
                    setattr(model, key, val)

                model.save()

            except ObjectDoesNotExist:
                Model = queryset.model
                model = Model(**identifiers, **defaults)
                parent.add_child(instance=model)
                model.save()
        else:
            model, _ = queryset.update_or_create(
                defaults=defaults, **identifiers)

        return model


@api_route('articles')
class SimpleIssueApiView(CreateOrUpdateMixin, viewsets.GenericViewSet):
    permission_classes = PERMISSIONS_RULES
    serializer_class = serializers.ArticleSerializer
    queryset = models.Article.objects.all()


@api_route('issues/simple')
class SimpleIssueApiView(CreateOrUpdateMixin, viewsets.GenericViewSet):
    permission_classes = PERMISSIONS_RULES
    serializer_class = serializers.SimpleIssueSerializer
    queryset = models.SimpleIssue.objects.all()


@api_route('issues/multi')
class MultiIssueApiView(CreateOrUpdateMixin, viewsets.GenericViewSet):
    permission_classes = PERMISSIONS_RULES
    serializer_class = serializers.MultiArticleIssueSerializer
    queryset = models.MultiArticleIssue.objects.all()


@api_route('publications')
class PublicationApiView(CreateOrUpdateMixin, viewsets.GenericViewSet):
    permission_classes = PERMISSIONS_RULES
    serializer_class = serializers.PublicationSerializer
    queryset = models.Publication.objects.all()


@api_route('documents')
class DocumentsApiView(CreateOrUpdateMixin, viewsets.GenericViewSet):
    permission_classes = PERMISSIONS_RULES
    serializer_class = serializers.DocumentSerializer
    parser_classes = (parsers.MultiPartParser,)
    queryset = Document.objects.all()
    identitfier_keys = ('title',)

    def update_or_create(self, defaults, **identifiers):
        sha = sha256()
        # tmpfile = Path(tempdir) / uuid.uuid4().hex
        with TemporaryFile('wb+') as tmp:
            srcfile = defaults['file']

            for chunk in srcfile.chunks():
                sha.update(chunk)
                tmp.write(chunk)

            tmp.flush()
            tmp.seek(0)

            digest = urlsafe_b64encode(sha.digest()).decode('utf-8')
            ext = Path(srcfile.name).suffix

            defaults['file'] = File(tmp, name=digest + ext)
            return super().update_or_create(defaults, **identifiers)

    @action(url_path='query', detail=False)
    def check(self, request):
        res = get_object_or_404(self.get_queryset().filter(
            title=request.query_params.get('title')
        ))

        return response.Response(self.get_serializer(instance=res).data)
