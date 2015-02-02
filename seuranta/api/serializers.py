from pytz import timezone, common_timezones
from rest_framework import exceptions, serializers
from django.utils.translation import ugettext_lazy as _
from seuranta.models import Competitor, Competition, Map, Route
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


class RouteSerializer(serializers.CharField):
    min_timestamp = None
    max_timestamp = None

    def to_representation(self, value):
        timestamps = []
        coordinates = []
        min_timestamp = self.min_timestamp or float('-inf')
        max_timestamp = self.max_timestamp or float('inf')
        for point in value:
            if point.timestamp < min_timestamp:
                continue
            elif point.timestamp > max_timestamp:
                continue
            else:
                timestamps.append(point.timestamp)
                coordinates.append((float(point.coordinates.latitude),
                                    float(point.coordinates.longitude)))
        return {
            'timestamps': timestamps,
            'coordinates': coordinates,
        }

    def to_internal_value(self, data):
        pass


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
    encoded_route = EncodedRouteSerializer(source='route')

    class Meta:
        model = Competitor
        fields = ('id', 'encoded_route')


class RouteSerializer(serializers.ModelSerializer):
    received = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Route
        fields = ('received', 'competitor', 'encoded_data')


class PostRouteSerializer(RouteSerializer):
    token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        validated_data = super(PostRouteSerializer, self).validate(attrs)
        token = validated_data.get('token')
        competitor = validated_data.get('competitor')
        if competitor.api_token != token:
            msg = _('Invalid competitor token')
            raise exceptions.ValidationError(msg)
        return validated_data

    class Meta:
        model = Route
        fields = ('id', 'competitor', 'encoded_data', 'token')


class CompetitorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Competitor
        fields = ('id', 'competition', 'name', 'short_name', 'start_time',
                  'approved')

    def validate_competition(self, value):
        if self.instance is not None and self.instance.competition != value:
            raise serializers.ValidationError(
                "Competitor cannot be moved to another competition"
            )
        return value

    def validate(self, data):
        start_time = data.get('start_time')
        if start_time \
           and (start_time < data['competition'].start_date
                or start_time > data['competition'].end_date):
            raise serializers.ValidationError(
                'start_time does not respect competition schedule'
            )
        return data


class CompetitorFullSerializer(CompetitorSerializer):
    token = serializers.CharField(source='api_token',
                                  read_only=True, default="",
                                  allow_blank=True)
    access_code = serializers.CharField(read_only=True, default="",
                                        allow_blank=True)

    class Meta:
        model = Competitor
        fields = ('id', 'competition', 'name', 'short_name', 'start_time',
                  'approved', 'access_code', 'token', )


class MapSerializer(serializers.ModelSerializer):
    public_url = RelativeURLField(source='image_url', read_only=True)
    size = serializers.ReadOnlyField()

    class Meta:
        model = Map
        fields = ('update_date',
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
    data_uri = serializers.CharField()
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
        fields = ('update_date',
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
    timezone = TimezoneField()
    slug = serializers.ReadOnlyField()
    competitors = CompetitorMiniSerializer(
        many=True,
        read_only=True,
        source='approved_competitors',
    )
    pending_competitors = CompetitorMiniSerializer(
        many=True,
        read_only=True
    )
    map = MapSerializer(read_only=True, source='get_map')
    publisher = serializers.ReadOnlyField(source='publisher_name')

    class Meta:
        model = Competition
        fields = ('id',
                  'publisher',
                  'name', 'slug',
                  'live_delay',
                  'latitude', 'longitude', 'zoom',
                  'publication_policy', 'signup_policy',
                  'publish_date', 'update_date', 'start_date', 'end_date',
                  'timezone',
                  'map',
                  'competitors', 'pending_competitors')

    def validate(self, data):
        if data.get('start_date') >= data.get('end_date'):
            raise serializers.ValidationError(
                'Invalid schedule'
            )
        return data
