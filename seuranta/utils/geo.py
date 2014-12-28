from __future__ import unicode_literals
from bisect import bisect_left, bisect_right

import re
import calendar
from decimal import Decimal
from datetime import datetime

from django.utils.timezone import utc


YEAR2000 = 946684800


def encode_number(num):
    encoded = ""
    while num >= 0x20:
        encoded += chr((0x20 | (num & 0x1f)) + 63)
        num >>= 5
    encoded += chr(num + 63)
    return encoded


def encode_signed_number(num):
    sgn_num = num << 1
    if num < 0:
        sgn_num = ~sgn_num
    return encode_number(sgn_num)


def decode_number(encoded):
    enc_len = len(encoded)
    ii = 0
    shift = 0
    result = 0
    b = 0x20
    while b >= 0x20 and ii < enc_len:
        b = ord(encoded[ii]) - 63
        ii += 1
        result |= (b & 0x1f) << shift
        shift += 5
    if result & 1:
        return ~(result >> 1), encoded[ii:]
    else:
        return result >> 1, encoded[ii:]


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
        if isinstance(coordinates, GeoCoordinates):
            self.coordinates = coordinates
        elif isinstance(coordinates, (list, tuple)) and len(coordinates) == 2:
            self.coordinates = GeoCoordinates(coordinates[0], coordinates[1])
        else:
            print timestamp, coordinates, type(coordinates)
            print isinstance(coordinates, (list, tuple)), len(coordinates) == 2
            raise ValueError("Wrong parameter 'coordinates', "
                             "expecting GeoCoordinates or a tuple of length 2.")

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


class GeoLocationSeries(object):
    @staticmethod
    def check_instance(item):
        if not isinstance(item, GeoLocation):
            raise TypeError('item is not of type GeoLocation')

    def __init__(self, lst):
        if isinstance(lst, basestring):
            lst = self.decode_str(lst)
        decorated = sorted(lst)
        self._keys = [item.timestamp for item in decorated]
        self._items = [item for item in decorated]
        if isinstance(lst, basestring):
            lst = self.decode_str(lst)
        for item in lst:
            self.check_instance(item)

    def clear(self):
        self.__init__([])

    def copy(self):
        return self.__class__(self)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, i):
        return self._items[i]

    def __iter__(self):
        return iter(self._items)

    def __reversed__(self):
        return reversed(self._items)

    def __repr__(self):
        return '%s(%r)' % (
            self.__class__.__name__,
            self._items
        )

    def __reduce__(self):
        return self.__class__, self._items

    def __contains__(self, item):
        self.check_instance(item)
        k = item.timestamp
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return item in self._items[i:j]

    def index(self, item):
        """Find the position of an item.  Raise ValueError if not found."""
        self.check_instance(item)
        k = item.timestamp
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return self._items[i:j].index(item) + i

    def count(self, item):
        """Return number of occurrences of item"""
        self.check_instance(item)
        k = item.timestamp
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return self._items[i:j].count(item)

    def insert(self, item):
        """Insert a new item.  If equal keys are found, replace item"""
        self.check_instance(item)
        k = item.timestamp
        i = bisect_left(self._keys, k)
        if i < len(self._keys) and self._keys[i] == k:
            self._items[i] = item
        else:
            self._keys.insert(i, k)
            self._items.insert(i, item)

    def insert_right(self, item):
        """Insert a new item.  If equal keys are found, add to the right"""
        self.check_instance(item)
        k = item.timestamp
        i = bisect_right(self._keys, k)
        self._keys.insert(i, k)
        self._items.insert(i, item)

    def remove(self, item):
        """Remove first occurence of item.  Raise ValueError if not found"""
        self.check_instance(item)
        i = self.index(item)
        del self._keys[i]
        del self._items[i]

    def find(self, k):
        """Return first item with a key == k.
        Raise ValueError if not found."""
        i = bisect_left(self._keys, k)
        if i != len(self) and self._keys[i] == k:
            return self._items[i]
        raise ValueError('No item found with key equal to: %r' % (k,))

    def find_lte(self, k):
        """Return last item with a key <= k.  Raise ValueError if not found."""
        i = bisect_right(self._keys, k)
        if i:
            return self._items[i-1]
        raise ValueError('No item found with key at or below: %r' % (k,))

    def find_lt(self, k):
        """Return last item with a key < k.  Raise ValueError if not found."""
        i = bisect_left(self._keys, k)
        if i:
            return self._items[i-1]
        raise ValueError('No item found with key below: %r' % (k,))

    def find_gte(self, k):
        """Return first item with a key >= equal to k.
        Raise ValueError if not found"""
        i = bisect_left(self._keys, k)
        if i != len(self):
            return self._items[i]
        raise ValueError('No item found with key at or above: %r' % (k,))

    def find_gt(self, k):
        """Return first item with a key > k.  Raise ValueError if not found"""
        i = bisect_right(self._keys, k)
        if i != len(self):
            return self._items[i]
        raise ValueError('No item found with key above: %r' % (k,))

    def __str__(self):
        result = ""
        prev_tim = YEAR2000
        prev_lat = 0
        prev_lng = 0
        for pt in self:
            coord = pt.coordinates
            tim_d = int(round(float(pt.timestamp) - prev_tim))
            lat_d = int(round(1e5*(float(coord.latitude) - prev_lat)))
            lng_d = int(round(1e5*(float(coord.longitude) - prev_lng)))
            result += (encode_signed_number(tim_d)
                       + encode_signed_number(lat_d)
                       + encode_signed_number(lng_d))
            prev_tim += tim_d
            prev_lat += lat_d/1e5
            prev_lng += lng_d/1e5
        return result

    @staticmethod
    def decode_str(encoded):
        result = []
        tim = YEAR2000
        lat = 0
        lon = 0
        while len(encoded) > 0:
            tim_d, encoded = decode_number(encoded)
            lat_d, encoded = decode_number(encoded)
            lon_d, encoded = decode_number(encoded)
            tim += tim_d
            lat += lat_d
            lon += lon_d
            result.append(GeoLocation(tim, (lat/1e5, lon/1e5)))
        return result

    def __eq__(self, other):
        return isinstance(other, GeoLocationSeries)\
            and self._items == other._items

    def __ne__(self, other):
        return not self.__eq__(other)

    def union(self, other):
        out = self.copy()
        for item in other._items:
            out.insert(item)
        return out
