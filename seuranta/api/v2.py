import logging

from django.db.models import Q

from rest_framework import serializers
from rest_framework import generics
from rest_framework import permissions
from rest_framework.generics import get_object_or_404

from seuranta.models import Competitor, Competition
from seuranta.serializers import (CompetitorSerializer,
                                  CompetitorFullSerializer,
                                  CompetitionSerializer,
                                  MapSerializer, MapFullSerializer)
from seuranta.views import download_map as orig_download_map_view


logger = logging.getLogger(__name__)


def download_map(request, pk):
    orig_download_map_view(request, pk)


class CompetitionPermission(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == 'POST':
            return not request.user.is_anonymous
        return (obj.publisher == request.user) or request.user.is_superuser


class MapPermission(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return any([
            (obj.competition.publisher == request.user),
            request.user.is_superuser
        ])


class CompetitionListView(generics.ListCreateAPIView):
    """
    List and Create Competition
    ---------------------------

    Optional query parameters:

      - id -- Select single **competition** by its id
      - id[] -- Select multiple **competition** by their id
      - q -- Search terms
      - page -- Page number (Default: 1)
      - results_per_page -- Number of result per page (Default:20 Max: 1000)
    """
    queryset = Competition.objects.all()
    permission_classes = (CompetitionPermission, )
    serializer_class = CompetitionSerializer

    def get_queryset(self):
        qs = super(CompetitionListView, self).get_queryset()
        query = Q(publication_policy='public')
        if not self.request.user.is_anonymous:
            query |= Q(publisher=self.request.user)
        qs.filter(query)
        return qs

    def perform_create(self, serializer):
        if self.request.user.is_anonymous():
            self.permission_denied(self.request)
        serializer.save(publisher=self.request.user)
        super(CompetitionListView, self).perform_create(serializer)


class CompetitionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Competition.objects.all()
    permission_classes = (CompetitionPermission, )
    serializer_class = CompetitionSerializer


class MapDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Competition.objects.all()
    permission_classes = (MapPermission, )
    serializer_class = MapSerializer

    def get_serializer_class(self):
        if any([self.request.user.is_superuser,
                self.request.user == self.get_object().competition.publisher]):
            return MapFullSerializer
        return MapSerializer

    def get_object(self):
        """
        Returns the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        competition = get_object_or_404(queryset, **filter_kwargs)
        obj = competition.map
        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj


class CompetitorListView(generics.ListCreateAPIView):
    """
    List and Create Competitor
    --------------------------

    Optional query parameters:

      - id -- Select single **competitor** by its id
      - id[] -- Select multiple **competitor** by their id
      - q -- Search terms
      - competition_id -- Select **competitors** in a single **competition**
      - competition_id[] -- Select **competitors** in multiple **competition**
      - access_code -- Given with competition_id to access full details
      - page -- Page number (Default: 1)
      - results_per_page -- Number of result per page (Default:20 Max: 1000)
    """
    queryset = Competitor.objects.all()
    permission_classes = (permissions.AllowAny, )
    lookup_fields = ('name', )

    def __init__(self):
        self.paginate_by = 20
        self.paginate_by_param = 'results_per_page'
        self.max_paginate_by = 1000
        super(CompetitorListView, self).__init__()

    def get_serializer_class(self):
        competition_id = self.request.query_params.get("competition_id")
        access_code = self.request.query_params.get("access_code")
        open_competitions = Competition.objects.all()
        if self.request.user.is_superuser:
            return CompetitorFullSerializer
        elif competition_id:
            open_competitions = open_competitions.filter(pk=competition_id)
        elif self.request.user.is_anonymous():
            open_competitions = open_competitions.filter(
                publication_policy='public'
            ).exclude(signup_policy='closed')
        else:
            open_competitions = open_competitions.filter(
                Q(publisher=self.request) | (Q(publication_policy='public')
                                             & ~Q(signup_policy='closed'))
            )

        class CustomSerializer(CompetitorSerializer):
            competition = serializers.PrimaryKeyRelatedField(
                queryset=open_competitions
            )

        class CustomFullSerializer(CompetitorFullSerializer):
            competition = serializers.PrimaryKeyRelatedField(
                queryset=open_competitions
            )

        if self.request.user.is_anonymous() or not competition_id:
            return CustomSerializer
        is_publisher = False
        has_token = False
        if not self.request.user.is_anonymous():
            is_publisher = (Competition.objects.filter(
                publisher=self.request.user,
                id=competition_id
            ).count() == 1)
        if access_code and not is_publisher:
            has_token = (Competitor.objects.filter(
                access_code=access_code,
                competition_id=competition_id
            ).count() == 1)
        if has_token or is_publisher:
            return CustomFullSerializer
        return CompetitorSerializer

    def get_queryset(self):
        qs = super(CompetitorListView, self).get_queryset()
        competition_id = self.request.query_params.get("competition_id")
        competition_ids = self.request.query_params.getlist("competition_id[]")
        access_code = self.request.query_params.get("access_code")
        competitor_id = self.request.query_params.get("id")
        competitor_ids = self.request.query_params.getlist("id[]")
        search_text = self.request.query_params.get('q', '').strip()
        if competition_id:
            qs = qs.filter(competition_id=competition_id)
            if access_code:
                qs = qs.filter(access_code=access_code)
        if competitor_id:
            qs = qs.filter(id=competitor_id)
        elif competitor_ids:
            qs = qs.filter(id__in=competitor_ids)
        if not (competition_ids or competition_id
                or competitor_id or competitor_ids):
            query = Q(publication_policy='public')
            if not self.request.user.is_anonymous:
                query |= Q(publisher=self.request.user)
            competition_ids = Competition.objects.filter(
                query
            ).values_list('pk', flat=True)
        if competition_ids:
            qs.filter(competition_id__in=competition_ids)
        if search_text:
            query = Q()
            search_terms = search_text.split(' ')
            for search_term in search_terms:
                sub_query = Q()
                for field_name in self.lookup_fields:
                    kwargs = {'%s__icontains' % field_name: search_term}
                    sub_query |= Q(**kwargs)
                query &= sub_query
            qs = qs.filter(query)
        return qs

    def perform_create(self, serializer):
        obj = serializer.validated_data
        competition_signup_policy = obj.get('competition').signup_policy
        is_publisher = (obj.get('competition').publisher == self.request.user)
        if not (self.request.user.is_superuser
                or is_publisher
                or competition_signup_policy != 'closed'):
            self.permission_denied(self.request)
        if competition_signup_policy != 'open' and not is_publisher:
            serializer.validated_data['approved'] = False
        super(CompetitorListView, self).perform_create(serializer)


class CompetitorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Update or Delete Competitor
    --------------------------

    Optional query parameters:

      - api_token -- Specify the api_token for this competitor
    """
    queryset = Competitor.objects.all()
    permission_classes = (permissions.AllowAny, )

    def get_serializer_class(self):
        if self.request.user.is_superuser:
            return CompetitorFullSerializer
        obj = self.get_object()
        api_token = self.request.query_params.get('api_token')
        is_publisher = (obj.competition.publisher == self.request.user)
        has_api_key = (obj.api_token == api_token)
        if is_publisher or has_api_key:
            return CompetitorFullSerializer
        return CompetitorSerializer

    def perform_update(self, serializer):
        obj = serializer.instance
        api_token = self.request.query_params.get('api_token')
        competition_signup_policy = obj.competition.signup_policy
        is_publisher = (obj.competition.publisher == self.request.user)
        has_api_token = (obj.api_token == api_token)
        if not (self.request.user.is_superuser
                or is_publisher
                or has_api_token):
            self.permission_denied(self.request)
        if competition_signup_policy != 'open':
            serializer.validated_data['approved'] = False
        super(CompetitorDetailView, self).perform_update(serializer)

    def perform_destroy(self, instance):
        is_publisher = (instance.competition.publisher == self.request.user)
        api_token = self.request.query_params.get('api_token')
        competition_signup_policy = instance.competition.signup_policy
        has_api_token = (instance.api_token == api_token)
        if not (self.request.user.is_superuser
                or is_publisher
                or (has_api_token and competition_signup_policy == 'open')):
            self.permission_denied(self.request)
        super(CompetitorDetailView, self).perform_destroy(instance)

