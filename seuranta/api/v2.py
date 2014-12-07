import logging

from django.db.models import Q

from rest_framework import generics
from rest_framework import permissions

from seuranta.models import Competitor, Competition, Map
from seuranta.serializers import (CompetitorSerializer,
                                  CompetitorFullSerializer,
                                  CompetitionSerializer,
                                  MapSerializer)
from seuranta.views import download_map


logger = logging.getLogger(__name__)


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
        if request.method == 'POST':
            return not request.user.is_anonymous
        return (obj.competition.publisher == request.user) or request.user.is_superuser


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


class CompetitionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Competition.objects.all()
    permission_classes = (CompetitionPermission, )
    serializer_class = CompetitionSerializer


class MapDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Map.objects.all()
    permission_classes = (MapPermission, )
    serializer_class = MapSerializer


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
        if self.request.user.is_superuser:
            return CompetitorFullSerializer
        competition_id = self.request.query_params.get("competition_id")
        access_code = self.request.query_params.get("access_code")
        is_publisher = False
        has_token = False
        if not competition_id:
            return CompetitorSerializer
        if not self.request.user.is_anonymous:
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
            return CompetitorFullSerializer
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

