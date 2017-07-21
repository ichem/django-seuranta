from pytz import timezone, common_timezones
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions, serializers
from seuranta.models import (Competitor, Competition, Map, Route,
                             CompetitorToken)
from seuranta.utils.geo import GeoLocationSeries


class RelativeURLField(serializers.Field):
    """
    Field that returns a link to the relative url.
    """
    def to_representation(self, value):
        request = self.context.get('request')
        url = request and request.build_absolute_uri(value) or ''
        return url


class TimezoneField(serializers.ChoiceField):
    """
    Field that contain timezone data
    """
    def __init__(self, **kwargs):
        choices = [(tz, tz) for tz in common_timezones]
        super(TimezoneField, self).__init__(choices, **kwargs)

    def to_internal_value(self, value):
        return timezone(value)


class CompetitorMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competitor
        fields = ('id', 'name', 'short_name', 'start_time', )
        read_only = ('id', 'name', 'short_name', 'start_time', )


# class JsonRouteSerializer(serializers.CharField):
#     min_timestamp = None
#     max_timestamp = None
#
#     def to_representation(self, value):
#         timestamps = []
#         coordinates = []
#         min_timestamp = self.min_timestamp or float('-inf')
#         max_timestamp = self.max_timestamp or float('inf')
#         for point in value:
#             if point.timestamp < min_timestamp:
#                 continue
#             elif point.timestamp > max_timestamp:
#                 continue
#             else:
#                 timestamps.append(point.timestamp)
#                 coordinates.append((float(point.coordinates.latitude),
#                                     float(point.coordinates.longitude)))
#         return {
#             'timestamps': timestamps,
#             'coordinates': coordinates,
#         }
#
#     def to_internal_value(self, data):
#         pass


class EncodedRouteSerializer(serializers.CharField):
    min_timestamp = None
    max_timestamp = None

    def to_representation(self, value):
        if self.min_timestamp is None and self.max_timestamp is None:
            return str(value)
        min_timestamp = self.min_timestamp or float('-inf')
        max_timestamp = self.max_timestamp or float('inf')
        ret = GeoLocationSeries('')
        for point in value:
            if point.timestamp < min_timestamp:
                continue
            elif point.timestamp > max_timestamp:
                continue
            else:
                ret.insert(point)
        return str(ret)

    def to_internal_value(self, data):
        return GeoLocationSeries(data)


class CompetitorRouteSerializer(serializers.ModelSerializer):
    encoded_data = EncodedRouteSerializer(source='route')

    class Meta:
        model = Competitor
        fields = ('id', 'encoded_data')


class RouteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Route
        fields = ('created', 'competitor', 'encoded_data')


class CompetitorTokenSerializer(serializers.Serializer):
    competitor = serializers.CharField()
    access_code = serializers.CharField()

    def validate(self, attrs):
        competitor = attrs.get('competitor')
        access_code = attrs.get('access_code')
        if competitor and access_code:
            competitors = Competitor.objects.filter(pk=competitor,
                                                    access_code=access_code)
            if competitors.exists():
                competitor = competitors[0]
                if not competitor.approved:
                    msg = _('Competitor is not approved.')
                    raise exceptions.ValidationError(msg)
            else:
                msg = _('Unable to retrieve competitor with given'
                        ' credentials.')
                raise exceptions.ValidationError(msg)
        else:
            msg = _('Must include "competitor" and "access_code"')
            raise exceptions.ValidationError(msg)
        attrs['competitor'] = competitor
        return attrs


class PostRouteSerializer(RouteSerializer):
    token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        validated_data = super(PostRouteSerializer, self).validate(attrs)
        key = validated_data.get('token')
        competitor = validated_data.get('competitor')
        token = CompetitorToken.objects.filter(competitor=competitor, key=key)
        if not token.exists():
            msg = _('Invalid competitor token')
            raise exceptions.ValidationError(msg)
        validated_data.pop('token', None)
        return validated_data

    class Meta:
        model = Route
        fields = ('id', 'competitor', 'encoded_data', 'token')


class CompetitorSerializer(serializers.ModelSerializer):
    access_code = serializers.CharField(write_only=True, allow_blank=True)

    class Meta:
        model = Competitor
        fields = (
            'id',
            'updated',
            'competition',
            'name', 'short_name',
            'start_time',
            'approved',
            'access_code'
        )

    def validate_competition(self, value):
        if self.instance is not None and self.instance.competition != value:
            msg = _("Competitor cannot be moved to another competition")
            raise serializers.ValidationError(msg)
        return value

    def validate(self, data):
        start_time = data.get('start_time')
        competition = data.get('competition', self.instance.competition)
        if start_time and \
                (start_time < competition.start_date or
                 start_time > competition.end_date):
            msg = _('start_time does not respect competition schedule')
            raise serializers.ValidationError(msg)
        return super(CompetitorSerializer, self).validate(data)


class AnonCompetitorSerializer(CompetitorSerializer):
    token = serializers.CharField(write_only=True)

    class Meta:
        model = Competitor
        fields = (
            'id',
            'updated',
            'competition',
            'name', 'short_name',
            'start_time',
            'approved',
            'access_code',
            'token'
        )

    def validate(self, data):
        validated_data = super(AnonCompetitorSerializer, self).validate(data)
        key = validated_data.get('token')
        competitor_id = self.instance.id
        token = CompetitorToken.objects.filter(competitor_id=competitor_id,
                                               key=key)
        if not token.exists():
            msg = _('Invalid competitor token')
            raise exceptions.ValidationError(msg)
        return validated_data


class AdminCompetitorSerializer(CompetitorSerializer):
    access_code = serializers.CharField()


class MapSerializer(serializers.ModelSerializer):
    public_url = RelativeURLField(source='image_url', read_only=True)
    size = serializers.ReadOnlyField()

    class Meta:
        model = Map
        fields = (
            'updated',
            'is_calibrated',
            'public_url',
            'size',
            'top_left_lat',
            'top_left_lng',
            'top_right_lat',
            'top_right_lng',
            'bottom_right_lat',
            'bottom_right_lng',
            'bottom_left_lat',
            'bottom_left_lng',
            'display_mode',
            'background_tile_url',
        )


class MapFullSerializer(MapSerializer):
    data_uri = serializers.CharField(allow_blank=True)
    size = serializers.ReadOnlyField()
    top_left_lat = serializers.FloatField()
    top_left_lng = serializers.FloatField()
    top_right_lat = serializers.FloatField()
    top_right_lng = serializers.FloatField()
    bottom_right_lat = serializers.FloatField()
    bottom_right_lng = serializers.FloatField()
    bottom_left_lat = serializers.FloatField()
    bottom_left_lng = serializers.FloatField()

    class Meta:
        model = Map
        fields = (
            'updated',
            'is_calibrated',
            'data_uri',
            'public_url',
            'size',
            'top_left_lat',
            'top_left_lng',
            'top_right_lat',
            'top_right_lng',
            'bottom_right_lat',
            'bottom_right_lng',
            'bottom_left_lat',
            'bottom_left_lng',
            'display_mode',
            'background_tile_url',
        )


class CompetitionSerializer(serializers.ModelSerializer):
    timezone = TimezoneField(label=_('Local Timezone'))
    slug = serializers.ReadOnlyField()
    competitor_count = serializers.ReadOnlyField(
        source='approved_competitor_count'
    )
    pending_competitor_count = serializers.ReadOnlyField()
    map = MapSerializer(read_only=True, source='get_map')
    # publisher = serializers.ReadOnlyField(source='publisher_name')

    class Meta:
        model = Competition
        fields = (
            'id',
            'updated',
            # 'publisher',
            'name', 'slug',
            'live_delay',
            'latitude', 'longitude', 'zoom',
            'timezone',
            'publication_policy', 'signup_policy',
            'start_date', 'end_date',
            'map',
            'competitor_count', 'pending_competitor_count',
        )

    def validate(self, data):
        if data.get('start_date') >= data.get('end_date'):
            raise serializers.ValidationError(
                'Invalid schedule'
            )
        return data
