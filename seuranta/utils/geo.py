from __future__ import unicode_literals

import re
import calendar
from decimal import Decimal
from datetime import datetime

from django.utils.timezone import utc


class GeoCoordinates(object):
    LATITUDE_MAX_LENGTH = 4 + 16
    LONGITUDE_MAX_LENGTH = 5 + 16
    MAX_LENGTH = LATITUDE_MAX_LENGTH + LONGITUDE_MAX_LENGTH + 1
    repr_re = re.compile(
        r'^(?P<latitude>^\-?\d{1,2}(\.\d+)?),'
        r'(?P<longitude>\-?1?\d{1,2}(\.\d+)?$)'
    )
    _latitude = None
    _longitude = None

    def __init__(self, *args):
        if len(args) > 2:
            raise TypeError('Too many arguments')
        elif len(args) == 2:
            self.latitude = args[0]
            self.longitude = args[1]
        elif len(args) == 1:
            value = args[0]
            if isinstance(value, basestring):
                match = self.repr_re.match(value)
                if match is None:
                    raise ValueError("Incorrect argument '{}'".format(value))
                self.latitude = match.group('latitude')
                self.longitude = match.group('longitude')
            if isinstance(value, (tuple, list)):
                self.latitude = value[0]
                self.longitude = value[1]
        else:
            raise TypeError('')

    @property
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, value):
        if isinstance(value, (float, int)):
            value = str(value)
        # Put value in a correct range
        lat_mod = ((Decimal(value) + 90) % 360 + 360) % 360
        lat = 270 - lat_mod if lat_mod >= 180 else lat_mod - 90
        if str(lat) > self.LATITUDE_MAX_LENGTH:
            lat = Decimal(str(lat)[:self.LATITUDE_MAX_LENGTH])
        self._latitude = lat

    @property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, value):
        if isinstance(value, (float, int)):
            value = str(value)
        # Put value in a correct range
        lon = ((Decimal(value) + 180) % 360 + 360) % 360 - 180
        if str(lon) > self.LONGITUDE_MAX_LENGTH:
            lon = Decimal(str(lon)[:self.LONGITUDE_MAX_LENGTH])
        self._longitude = lon

    def __str__(self):
        return ",".join([str(self.latitude), str(self.longitude)])

    def __repr__(self):
        return "GeoCoordinates(%s)" % str(self)

    def __len__(self):
        return len(str(self))

    def __eq__(self, other):
        return (isinstance(other, GeoCoordinates)
                and self.latitude == other.latitude
                and self.longitude == other.longitude)

    def __ne__(self, other):
        return not self.__eq__(other)


class GeoLocation(object):
    TIMESTAMP_MAX_LENGTH = 17
    MAX_LENGTH = GeoCoordinates.MAX_LENGTH + TIMESTAMP_MAX_LENGTH + 1

    def __init__(self, timestamp, coordinates):
        self._timestamp = None
        self.timestamp = timestamp
        if isinstance(coordinates, GeoLocation):
            self.coordinates = coordinates
        elif isinstance(coordinates, (list, tuple)) and len(coordinates) == 2:
            self.coordinates = GeoLocation(coordinates[0], coordinates[1])
        else:
            raise ValueError("Wrong parameter 'coordinates', "
                             "expecting a GeoLocation or a tuple of length 2.")

    def get_datetime(self):
        return datetime.fromtimestamp(self._timestamp, utc)

    def get_timestamp(self):
        return self._timestamp

    def set_timestamp(self, value):
        if isinstance(value, datetime):
            value = str(calendar.timegm(value.timetuple()))
        elif isinstance(value, float) or isinstance(value, int):
            value = str(value)
        timestamp = Decimal(value)
        if len(str(int(timestamp))) > self.TIMESTAMP_MAX_LENGTH:
            raise ValueError('value must be less than {}'.format(
                '9'*self.TIMESTAMP_MAX_LENGTH
            ))
        self._timestamp = timestamp

    timestamp = property(get_timestamp, set_timestamp)

    def __str__(self):
        data = "%s:%s" % (self._timestamp, self.coordinates)
        if len(data) <= self.MAX_LENGTH:
            return data
        return "%s,%s" % (("%s" % self._timestamp)[:17], self.coordinates)

    def __repr__(self):
        return "GeoLocation(%s)" % str(self)

    def __len__(self):
        return len(str(self))

    def __eq__(self, other):
        return (isinstance(other, GeoLocation)
                and self.coordinates == other.coordinates
                and self.timestamp == other.timestamp)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        if not isinstance(other, GeoLocation):
            raise TypeError('Can only compare to other instances of '
                            'GeoLocation')
        return cmp(self.timestamp, other.timestamp)
