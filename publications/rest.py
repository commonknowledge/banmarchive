from rest_framework import viewsets, permissions, exceptions, response

from publications import serializers, models
from helpers.rest import api_route


PERMISSIONS_RULES = (permissions.IsAuthenticatedOrReadOnly,)


class CreateOrUpdateMixin:
    def create(self, request):
        request_serializer = self.get_serializer(data=request.POST)
        if not request_serializer.is_valid():
            raise exceptions.ParseError(request_serializer.error_message)

        queryset = self.get_queryset()
        data = request_serializer.validated_data
        tags = data.pop('tags')

        res, _ = queryset.update_or_create(
            parent=data['parent'], slug=data['slug'], defaults=data)

        res.tags.set(tags)

        response_serializer = self.get_serializer(instance=res)
        return response.Response(response_serializer.data)


@api_route('issues/simple/')
class SimpleIssueApiView(CreateOrUpdateMixin, viewsets.GenericViewSet):
    permission_classes = PERMISSIONS_RULES
    serializer_class = serializers.SimpleIssueSerializer
    queryset = models.SimpleIssue.objects.all()


@api_route('issues/multi/')
class MultiIssueApiView(CreateOrUpdateMixin, viewsets.GenericViewSet):
    permission_classes = PERMISSIONS_RULES
    serializer_class = serializers.MultiArticleIssueSerializer
    queryset = models.MultiArticleIssue.objects.all()


@api_route('publications')
class PublicationApiView(CreateOrUpdateMixin, viewsets.GenericViewSet):
    permission_classes = PERMISSIONS_RULES
    serializer_class = serializers.PublicationSerializer
    queryset = models.Publication.objects.all()
