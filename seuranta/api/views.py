import logging
import time
import re
import datetime
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework import generics
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import parsers
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.generics import get_object_or_404
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from rest_framework.exceptions import ParseError, PermissionDenied, NotFound
from rest_framework import status
from rest_framework.views import APIView
from seuranta.api.pagination import RouteDataPagination
from seuranta.models import Competition, Competitor, CompetitorToken, Route
from seuranta.api.serializers import (
    AnonCompetitorSerializer,
    AdminCompetitorSerializer,
    CompetitionSerializer,
    MapSerializer,
    MapFullSerializer,
    CompetitorRouteSerializer,
    EncodedRouteSerializer,
    RouteSerializer,
    PostRouteSerializer,
    CompetitorSerializer,
    CompetitorTokenSerializer
)


logger = logging.getLogger(__name__)


class DestroyAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser,
                      parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)

    def post(self, request):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = Token.objects.filter(user=user)
        if token.exists():
            token.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_404_NOT_FOUND)


class ObtainCompetitorToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser,
                      parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)

    def post(self, request):
        serializer = CompetitorTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        competitor = serializer.validated_data['competitor']
        token, created = CompetitorToken.objects.get_or_create(
            competitor=competitor
        )
        return Response({'token': token.key})


class DestroyCompetitorToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser,
                      parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)

    def post(self, request):
        serializer = CompetitorTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        competitor = serializer.validated_data['competitor']
        token = CompetitorToken.objects.filter(competitor=competitor)
        if token.exists():
            token.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_404_NOT_FOUND)


class JPEGRenderer(renderers.BaseRenderer):
    media_type = 'image/jpeg'
    format = 'jpg'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return data


@api_view(['GET', ])
@renderer_classes((JPEGRenderer, ))
def download_map(request, pk):
    competition = get_object_or_404(Competition, pk=pk)
    # Check if competition is started or private
    if ((competition.publication_policy == 'private' and
         competition.publisher != request.user) or
            not competition.is_started()):
        raise PermissionDenied
    return Response(competition.map.image_data)


@api_view(['GET', ])
def get_time(request):
    now = time.time()
    return Response({
        "time": now,
    })


class CompetitionPermission(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == 'POST':
            return not request.user.is_anonymous()
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
      - publisher -- Select competition from publisher using its username
      - status[] -- Competition status ("live", "archived", "upcoming")
      - page -- Page number (Default: 1)
      - results_per_page -- Number of result per page (Default:20 Max: 1000)
      - reverse_order -- "true" to reverse the ordering (Default: false)
    """
    queryset = Competition.objects.all()
    permission_classes = (CompetitionPermission, )
    serializer_class = CompetitionSerializer

    def get_queryset(self):
        qs = super(CompetitionListView, self).get_queryset()
        competition_id = self.request.query_params.get("id")
        competition_ids = self.request.query_params.getlist("id[]")
        publisher = self.request.query_params.get("publisher")
        states = self.request.query_params.getlist("status[]")
        reverse_order = self.request.query_params.get("reverse_order", "false")
        if competition_id:
            qs = qs.filter(pk=competition_id)
        elif competition_ids:
            qs = qs.filter(pk__in=competition_ids)
        else:
            query = Q(publication_policy='public')
            if not self.request.user.is_anonymous():
                query |= Q(publisher=self.request.user)
            qs = qs.filter(query)
        if publisher:
            qs = qs.filter(publisher__username=publisher)
        if states:
            states = set(states)
            current_date = timezone.now()
            state_filter = Q()
            state_filters = {
                'live': Q(start_date__lte=current_date,
                          end_date__gte=current_date),
                'archived': Q(end_date__lt=current_date),
                'upcoming': Q(start_date__gt=current_date)
            }
            for state in states:
                if state not in ('live', 'archived', 'upcoming'):
                    raise ParseError("Invalid value for parameter status")
                state_filter |= state_filters[state]
            qs = qs.filter(state_filter)
        if reverse_order not in ('true', 'false'):
            raise ParseError("Invalid value for parameter reverse_order")
        if reverse_order == "true":
            qs = qs.order_by('end_date', 'name')
        else:
            qs = qs.order_by('-end_date', 'name')
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
      - approval_status -- Filter based on approval ("approved", "pending")
      - page -- Page number (Default: 1)
      - results_per_page -- Number of result per page (Default:20 Max: 1000)
    """
    queryset = Competitor.objects.all()
    permission_classes = (permissions.AllowAny, )
    lookup_fields = ('name', )

    def get_serializer_class(self):
        competition_id = self.request.query_params.get("competition_id")
        open_competitions = Competition.objects.all()
        if self.request.user.is_superuser:
            return AdminCompetitorSerializer
        elif competition_id:
            open_competitions = open_competitions.filter(pk=competition_id)
        elif self.request.user.is_anonymous():
            open_competitions = open_competitions.filter(
                publication_policy='public'
            ).exclude(signup_policy='closed')
        else:
            open_competitions = open_competitions.filter(
                Q(publisher=self.request.user) |
                (Q(publication_policy='public') & ~Q(signup_policy='closed'))
            )

        class CustomCompetitorSerializer(CompetitorSerializer):
            competition = serializers.PrimaryKeyRelatedField(
                queryset=open_competitions
            )

        class CompetitorCustomFullSerializer(AdminCompetitorSerializer):
            competition = serializers.PrimaryKeyRelatedField(
                queryset=open_competitions
            )

        if self.request.user.is_anonymous() or not competition_id:
            return CustomCompetitorSerializer
        if not self.request.user.is_anonymous():
            is_publisher = Competition.objects.filter(
                publisher=self.request.user,
                id=competition_id
            ).exists()
            if is_publisher:
                return CompetitorCustomFullSerializer
        return CompetitorSerializer

    def get_queryset(self):
        qs = super(CompetitorListView, self).get_queryset()
        competition_id = self.request.query_params.get("competition_id")
        competition_ids = self.request.query_params.getlist("competition_id[]")
        competitor_id = self.request.query_params.get("id")
        competitor_ids = self.request.query_params.getlist("id[]")
        search_text = self.request.query_params.get('q', '').strip()
        approval_state = self.request.query_params.get("approval_status")
        if competition_id:
            qs = qs.filter(competition_id=competition_id)
        if competitor_id:
            qs = qs.filter(id=competitor_id)
        elif competitor_ids:
            qs = qs.filter(id__in=competitor_ids)
        if not (competition_ids or competition_id or competitor_id or
                competitor_ids):
            query = Q(publication_policy='public')
            if not self.request.user.is_anonymous():
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
        if approval_state:
            if approval_state not in ('approved', 'pending'):
                raise ParseError("Invalid value for parameter status")
            if approval_state == "approved":
                qs = qs.filter(approved=True)
            else:
                qs = qs.filter(approved=False)
        return qs

    def perform_create(self, serializer):
        obj = serializer.validated_data
        competition_signup_policy = obj.get('competition').signup_policy
        is_publisher = (obj.get('competition').publisher == self.request.user)
        if not (self.request.user.is_superuser or is_publisher) \
           and competition_signup_policy == 'closed':
            raise PermissionDenied
        if competition_signup_policy == 'open':
            serializer.validated_data['approved'] = True
        elif not (self.request.user.is_superuser or is_publisher):
            serializer.validated_data['approved'] = False
        super(CompetitorListView, self).perform_create(serializer)


class CompetitorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Update or Delete Competitor
    --------------------------
    """
    queryset = Competitor.objects.all()
    permission_classes = (permissions.AllowAny, )

    def get_serializer_class(self):
        if self.request.user.is_superuser:
            return AdminCompetitorSerializer
        instance = self.get_object()
        is_publisher = (instance.competition.publisher == self.request.user)
        if is_publisher:
            return AdminCompetitorSerializer
        return AnonCompetitorSerializer

    def perform_update(self, serializer):
        instance = serializer.instance
        competition_signup_policy = instance.competition.signup_policy
        is_publisher = (instance.competition.publisher == self.request.user)
        approval = serializer.validated_data.get('approved')
        approval_changed = all([approval is not None,
                                approval != instance.approved])
        if competition_signup_policy == 'open':
            serializer.validated_data['approved'] = True
        elif (not (self.request.user.is_superuser or is_publisher) and
                approval_changed):
            serializer.validated_data['approved'] = instance.approved
        super(CompetitorDetailView, self).perform_update(serializer)

    def perform_destroy(self, instance):
        is_publisher = (instance.competition.publisher == self.request.user)
        if not (self.request.user.is_superuser or is_publisher):
            self.permission_denied(self.request)
        super(CompetitorDetailView, self).perform_destroy(instance)


class RouteListView(generics.ListCreateAPIView):
    """
    List Routes API
    ---------------

    Optional query parameters:

      - competitor_id -- Select single **competitor** by its id
      - competitor_id[] -- Select multiple **competitor** by their id
      - competition_id -- Select **competitors** in a single **competition**
      - competition_id[] -- Select **competitors** in multiple **competition**
      - created_after -- Minimum time of route data creation (unix timestamp)
    """
    queryset = Route.objects.all()
    permission_classes = (permissions.AllowAny, )
    pagination_class = RouteDataPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            if self.request.user.is_superuser:
                return PostRouteSerializer
            if self.request.user.is_anonymous():
                possible_competition_ids = Competition.objects.filter(
                    publication_policy='public'
                )
            else:
                possible_competition_ids = Competition.objects.filter(
                    Q(publisher=self.request.user) |
                    Q(publication_policy='public')
                ).values_list('pk', flat=True)
            possible_competitor = Competitor.objects.filter(
                competition_id__in=possible_competition_ids
            )

            class CustomPostRouteSerializer(PostRouteSerializer):
                competitor = serializers.PrimaryKeyRelatedField(
                    queryset=possible_competitor
                )

            return CustomPostRouteSerializer
        else:
            return RouteSerializer

    def get_queryset(self):
        qs = super(RouteListView, self).get_queryset()
        competition_id = self.request.query_params.get("competition_id")
        competition_ids = self.request.query_params.getlist("competition_id[]")
        competitor_id = self.request.query_params.get("competitor_id")
        competitor_ids = self.request.query_params.getlist("competitor_id[]")
        created_after = self.request.query_params.get("created_after")
        if competitor_id:
            qs = qs.filter(competitor_id=competitor_id)
        if competition_id:
            competitor_ids = Competitor.objects.filter(
                competition_id=competition_id
            ).values_list('pk', flat=True)
        elif competition_ids:
            competitor_ids = Competitor.objects.filter(
                competition_id__in=competition_ids
            ).values_list('pk', flat=True)
        if not (competition_ids or competition_id or competitor_id or
                competitor_ids):
            query = Q(publication_policy='public')
            if not self.request.user.is_anonymous():
                query |= Q(publisher=self.request.user)
            competition_ids = Competition.objects.filter(
                query
            ).values_list('pk', flat=True)
            competitor_ids = Competitor.objects.filter(
                competition_id__in=competition_ids
            ).values_list('pk', flat=True)
        if competitor_ids:
            qs = qs.filter(competitor_id__in=competitor_ids)
        if created_after is not None:
            from django.utils.timezone import utc
            try:
                start_epoch = float(created_after)
            except ValueError:
                raise ParseError()
            start_datetime = datetime.datetime.fromtimestamp(start_epoch)
            start = utc.localize(start_datetime)
            qs = qs.filter(created__gt=start)
        return qs


class CompetitorRouteDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or Update competitor Route
    -----------------------------------
    Optional query parameters:
      - start -- Minimum time of route data (unix timestamp)
      - end -- Maximum time of route data (unix timestamp)
    """
    queryset = Competitor.objects.all()
    permission_classes = (permissions.AllowAny, )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            min_timestamp = self.request.query_params.get("start", '-inf')
            max_timestamp = self.request.query_params.get("end", '+inf')
            if (min_timestamp != '-inf' and
                not re.match(r'\d+(\.\d+)?', min_timestamp)) or \
                    (max_timestamp != '+inf' and
                        not re.match(r'\d+(\.\d+)?', max_timestamp)):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            min_timestamp_arg = float(min_timestamp)
            max_timestamp_arg = float(max_timestamp)

            class CustomCompetitorRouteSerializer(CompetitorRouteSerializer):
                class CustomRouteSerializer(EncodedRouteSerializer):
                    min_timestamp = min_timestamp_arg
                    max_timestamp = max_timestamp_arg
                encoded_data = CustomRouteSerializer(source='route')
            return CustomCompetitorRouteSerializer
        return CompetitorRouteSerializer


class GPXRenderer(renderers.BaseRenderer):
    media_type = 'application/gpx+xml'
    format = 'gpx'
    charset = 'utf-8'
    render_style = 'text'

    def render(self, data, media_type=None, renderer_context=None):
        return data


@api_view(['GET', ])
@renderer_classes((GPXRenderer, ))
def download_gpx(request, pk):
    competitor = get_object_or_404(Competitor, pk=pk)
    # Check if competition is completed
    if not competitor.competition.is_completed():
        raise NotFound
    return Response(competitor.gpx)


destroy_auth_token = DestroyAuthToken.as_view()
obtain_competitor_token = ObtainCompetitorToken.as_view()
destroy_competitor_token = DestroyCompetitorToken.as_view()
competitions_view = CompetitionListView.as_view()
competition_view = CompetitionDetailView.as_view()
competition_map_view = MapDetailView.as_view()
competitors_view = CompetitorListView.as_view()
competitor_view = CompetitorDetailView.as_view()
routes_view = RouteListView.as_view()
competitor_route_view = CompetitorRouteDetailView.as_view()