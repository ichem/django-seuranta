import datetime
import base64
import json
import re
from decimal import Decimal
from PIL import Image
from django.core.files.base import ContentFile

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import utc, now
from django.utils.safestring import mark_safe
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError

from django.conf import settings
from seuranta.storage import OverwriteStorage

from timezone_field import TimeZoneField

from seuranta.fields import ShortUUIDField
from seuranta.utils import (short_uuid, slugify, format_date_iso,
                            make_random_code, gps_codec)
from seuranta.utils.validators import (validate_nice_slug, validate_latitude,
                                       validate_longitude)


BLANK_SIZE = {'width': 1, 'height': 1}
BLANK_FORMAT = "image/gif"
BLANK_GIF = "R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="
BLANK_DATA_URI = "data:" + BLANK_FORMAT + ";base64," + BLANK_GIF
BLANK_CALIBRATION_STRING = [90, -180,
                            90, 180,
                            -90, -180,
                            -90, 180]
PUBLICATION_POLICY_CHOICES = (
    ("private", _('Private')),
    ("secret", _('Secret')),
    ("public", _('Public')),
)
SIGNUP_POLICY_CHOICES = (
    ("closed", _('Closed')),
    ("org_val", _('Organizer Validated')),
    ("open", _('Open')),
)
MAP_DISPLAY_CHOICES = (
    ("map+bck", _('Map displayed over background')),
    ("map", _('Map only')),
    ("bck", _('Background')),
)
FLOAT_RE = re.compile(r'^(\-?[0-9]{1,3}(\.[0-9]+)?)$')
LAT_IDX = 0
LNG_IDX = 1
TOP_L_IDX = 0
TOP_R_IDX = 1
BOT_R_IDX = 2
BOT_L_IDX = 3


def map_upload_path(instance=None, file_name=None):
    import os.path
    tmp_path = [
        'seuranta',
        'maps'
    ]
    if file_name:
        pass
    filename = instance.competition.pk
    basename = os.path.basename(filename)
    tmp_path.append(instance.competition.publisher.username)
    tmp_path.append(basename[0])
    tmp_path.append(basename)
    return os.path.join(*tmp_path)


class Competition(models.Model):
    id = ShortUUIDField(_("identifier"), primary_key=True)
    publish_date = models.DateTimeField(_('publication date'),
                                        auto_now_add=True)
    update_date = models.DateTimeField(_("last update"), auto_now=True)
    timezone = TimeZoneField(
        verbose_name=_("timezone"),
        default="UTC",
    )
    start_date = models.DateTimeField(
        _("opening date (UTC)"),
    )
    end_date = models.DateTimeField(
        _("closing date (UTC)"),
    )
    publisher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("publisher"),
        related_name="competitions",
        editable=False
    )
    name = models.CharField(
        _('name'),
        max_length=50,
        default="Untitled",
        validators=[MinLengthValidator(4), ]
    )
    slug = models.SlugField(
        _('url friendly name'),
        validators=[validate_nice_slug, ],
        editable=False,
        max_length=21,
        unique=True
    )
    publication_policy = models.CharField(
        _("publication policy"),
        max_length=8,
        choices=PUBLICATION_POLICY_CHOICES,
        default="public"
    )
    signup_policy = models.CharField(
        _("signup policy"),
        max_length=8,
        choices=SIGNUP_POLICY_CHOICES,
        default="open",
    )

    @property
    def publisher_name(self):
        return self.publisher.username

    @property
    def is_started(self):
        return self.start_date < now()

    @property
    def is_completed(self):
        return self.end_date < now()

    @property
    def is_current(self):
        return self.is_started and not self.is_completed

    @property
    def approved_competitors(self):
        if self.signup_policy != 'open':
            return self.competitors.filter(approved=True)
        else:
            return self.competitors

    def get_map(self):
        if hasattr(self, 'defined_map'):
            return self.defined_map
        return Map(competition_id=self.pk)

    map = property(get_map)

    def pending_competitors(self):
        if self.signup_policy == 'open':
            return self.competitors.none()
        else:
            return self.competitors.filter(approved=False)

    def close_competition(self):
        self.end_date = now()

    @models.permalink
    def get_absolute_url(self):
        kwargs = {'publisher': self.publisher.username, 'slug': self.slug}
        return "seuranta.views.race_view", (), kwargs

    absolute_url = property(get_absolute_url)

    def derive_slug(self):
        orig_slug = slugify(self.name)
        desired_slug = orig_slug[:21]
        while desired_slug[0] in '-_':
            desired_slug = desired_slug[1:]
        while desired_slug[-1] in '-_':
            desired_slug = desired_slug[:-1]
        while ('--' or '__' or '-_' or '_-') in desired_slug:
            desired_slug = desired_slug.replace(
                '--', '-'
            ).replace(
                '__', '_'
            ).replace(
                '-_', '-'
            ).replace(
                '_-', '_'
            )
        if len(desired_slug) == 0:
            desired_slug = "undefined"
        elif len(desired_slug) < 5:
            desired_slug = "%s-%d" % (desired_slug, self.start_date.year)
        orig_slug = desired_slug
        counter = 2
        qs = Competition.objects.all()
        if self.pk is not None:
            qs = qs.exclude(pk=self.pk)
        qs = qs.filter(publisher_id=self.publisher_id)
        while qs.filter(slug=desired_slug)[:1].count() > 0:
            ending = "-%d" % counter
            desired_slug = "%s%s" % (orig_slug[:21 - len(ending)], ending)
            counter += 1
        self.slug = desired_slug

    def clean(self):
        super(Competition, self).clean()
        if self.start_date > self.end_date:
            raise ValidationError('Invalid schedule')

    def save(self, *args, **kwargs):
        self.derive_slug()
        super(Competition, self).save(*args, **kwargs)

    def __unicode__(self):
        return u"{} \"{}\" by {}".format(_(u"Competition"),
                                         self.name,
                                         self.publisher)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = _("competition")
        verbose_name_plural = _("competitions")

    def serialize(self, include_private_data=False):
        result = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'publisher': self.publisher.username,
            'publish_date': format_date_iso(self.publish_date),
            'update_date': format_date_iso(self.update_date),
            'publication_policy': self.publication_policy,
            'signup_policy': self.signup_policy,
            'timezone': str(self.timezone),
            'schedule': {
                'start_date': format_date_iso(self.start_date),
                'end_date': format_date_iso(self.end_date),
            },
            'competitors': [],
            'map': {},
        }
        if (self.is_started or include_private_data) and self.map:
            result['map']['image_data_uri'] = self.map.data_uri
            result['map']['calibration'] = self.map.calibration_string
            result['map']['size'] = self.map.size
            result['map']['format'] = self.map.format
        else:
            result['map']['image_data_uri'] = self.map.data_uri
            result['map']['calibration'] = BLANK_CALIBRATION_STRING
            result['map']['size'] = BLANK_SIZE
            result['map']['format'] = BLANK_FORMAT
        competitor_set = self.competitors.all()
        if not include_private_data and self.signup_policy != "open":
            competitor_set = competitor_set.filter(approved=True)
        for competitor in competitor_set:
            result['competitors'].append(
                competitor.serialize(include_private_data)
            )
        return result

    def dump_json(self, include_private_data=False):
        return json.dumps(self.serialize(include_private_data))


class Map(models.Model):
    competition = models.OneToOneField(Competition, related_name='defined_map',
                                       primary_key=True)
    update_date = models.DateTimeField(auto_now=True)
    image = models.ImageField(
        _("image"),
        upload_to=map_upload_path,
        height_field="height",
        width_field="width",
        storage=OverwriteStorage(),
        blank=True, null=True
    )
    width = models.PositiveIntegerField(
        _("width"),
        editable=False,
        blank=True, null=True
    )
    height = models.PositiveIntegerField(
        _("height"),
        editable=False,
        blank=True, null=True
    )
    calibration_string = models.CharField(
        _("calibration string"),
        max_length=255,
        blank=True,
        null=True,
        help_text=mark_safe(
            "<a"
            " target='_blank'"
            " href='https://rphl.net/dropbox/calibrate_map2.html'"
            ">" + force_unicode(_("Online calibration tool")) + "</a>"
        ),
    )
    display_mode = models.CharField(
        _("display mode"),
        max_length=8,
        choices=MAP_DISPLAY_CHOICES,
        default="map"
    )
    background_tile_url = models.URLField(
        _('background tile url'),
        blank=True,
        help_text=''.join([
            force_unicode(_("e.g")) +
            " https://{s}.example.com/{x}_{y}_{z}.png, " +
            force_unicode(_("Leave blank to use OpenStreetMap"))
        ]),
    )

    @property
    def size(self):
        if not self.image:
            return BLANK_SIZE
        else:
            return {'width': self.width, 'height': self.height}

    @property
    def format(self):
        if not self.image:
            return BLANK_FORMAT
        return "image/jpeg"

    @property
    def image_data(self):
        if not self.image:
            return BLANK_GIF.decode('base64')
        compressed_file = self.image.name + '_l'
        if not self.image.storage.exists(compressed_file):
            with self.image.storage.open(self.image.file, 'rb') as fp_in, \
                    self.image.storage.open(compressed_file, 'wb') as fp_out:
                buf = StringIO()
                im = Image.open(fp_in)
                im.save(buf, 'JPEG', quality=40)
                fp_out.write(buf.getvalue())
                im.close()
                buf.close()
        with self.image.storage.open(compressed_file, 'rb') as fp:
            data = fp.read()
            return data

    @property
    def data_uri(self):
        return "data:%s;base64,%s" % (self.format,
                                      base64.b64encode(self.image_data))

    @data_uri.setter
    def data_uri(self, value):
        data_matched = re.match(
            r'^data\:image/(?P<format>jpeg|png|gif);base64,'
            r'(?P<data_b64>(?:[A-Za-z0-9+/]{4})*'
            r'(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?)$',
            value
        )
        if data_matched:
            compressed_file = self.image.name + '_l'
            if self.image.storage.exists(compressed_file):
                self.image.storage.delete(compressed_file)
            self.image.save(
                'filename',
                ContentFile(
                    base64.b64decode(data_matched.group('data_b64'))
                )
            )
        else:
            raise ValueError('Not a base 64 encoded data URI of an image')

    @models.permalink
    def get_image_url(self):
        kwargs = {'pk': self.competition.pk, }
        return "seuranta_api_v2_map_download", (), kwargs
    image_url = property(get_image_url)

    @property
    def is_calibrated(self):
        if not self.calibration_string:
            return False
        values = self.calibration_string.split('|')
        if len(values) != 8:
            return False
        for val in values:
            if not FLOAT_RE.match(val):
                return False
        return True

    @property
    def calibration(self):
        return {'top_left': dict(lat=self.top_left_lat, lng=self.top_left_lng),
                'top_right': dict(lat=self.top_right_lat,
                                  lng=self.top_right_lng),
                'bottom_right': dict(lat=self.bottom_right_lat,
                                     lng=self.bottom_right_lng),
                'bottom_left': dict(lat=self.bottom_left_lat,
                                    lng=self.bottom_left_lng)}

    def _get_corner(self, n, coord):
        if self.image is not None and self.is_calibrated:
            return self.calibration_string.split("|")[2 * n + coord]
        return BLANK_CALIBRATION_STRING[2 * n + coord]

    def _set_corner(self, n, coord, value):
        if self.image is not None:
            corner_coords = [
                self.top_left_lat,
                self.top_left_lng,
                self.top_right_lat,
                self.top_right_lng,
                self.bottom_right_lat,
                self.bottom_right_lng,
                self.bottom_left_lat,
                self.bottom_left_lng,
            ]
            corner_coords[2 * n + coord] = value
            self.calibration_string = "|".join([str(x) for x in corner_coords])

    # Top Left
    @property
    def top_left_lat(self):
        return self._get_corner(TOP_L_IDX, LAT_IDX)

    @top_left_lat.setter
    def top_left_lat(self, value):
        self._set_corner(TOP_L_IDX, LAT_IDX, value)

    @property
    def top_left_lng(self):
        return self._get_corner(TOP_L_IDX, LNG_IDX)

    @top_left_lng.setter
    def top_left_lng(self, value):
        self._set_corner(TOP_L_IDX, LNG_IDX, value)

    # Top Right
    @property
    def top_right_lat(self):
        return self._get_corner(TOP_R_IDX, LAT_IDX)

    @top_right_lat.setter
    def top_right_lat(self, value):
        self._set_corner(TOP_R_IDX, LAT_IDX, value)

    @property
    def top_right_lng(self):
        return self._get_corner(TOP_R_IDX, LNG_IDX)

    @top_right_lng.setter
    def top_right_lng(self, value):
        self._set_corner(TOP_R_IDX, LNG_IDX, value)

    # Bottom Right
    @property
    def bottom_right_lat(self):
        return self._get_corner(BOT_R_IDX, LAT_IDX)

    @bottom_right_lat.setter
    def bottom_right_lat(self, value):
        self._set_corner(BOT_R_IDX, LAT_IDX, value)

    @property
    def bottom_right_lng(self):
        return self._get_corner(BOT_R_IDX, LNG_IDX)

    @bottom_right_lng.setter
    def bottom_right_lng(self, value):
        self._set_corner(BOT_R_IDX, LNG_IDX, value)

    # Bottom Left
    @property
    def bottom_left_lat(self):
        return self._get_corner(BOT_L_IDX, LAT_IDX)

    @bottom_left_lat.setter
    def bottom_left_lat(self, value):
        self._set_corner(BOT_L_IDX, LAT_IDX, value)

    @property
    def bottom_left_lng(self):
        return self._get_corner(BOT_L_IDX, LNG_IDX)

    @bottom_left_lng.setter
    def bottom_left_lng(self, value):
        self._set_corner(BOT_L_IDX, LNG_IDX, value)


@receiver(post_delete, sender=Map)
def map_post_delete_handler(sender, **kwargs):
    if sender:
        pass
    map_obj = kwargs['instance']
    if map_obj.image and map_obj.image.file:
        storage, path = map_obj.image.storage, map_obj.image.path
        storage.delete(path)


class Competitor(models.Model):
    id = ShortUUIDField(_("identifier"), primary_key=True)
    competition = models.ForeignKey(
        Competition,
        verbose_name=_('competition'),
        related_name="competitors",
    )
    name = models.CharField(
        _('name'),
        max_length=50,
    )
    short_name = models.CharField(
        _('short name'),
        max_length=50,
    )
    start_time = models.DateTimeField(
        _('start time (UTC)'),
        null=True,
        blank=True,
    )
    api_token = ShortUUIDField(
        _("api token"),
        editable=False,
        blank=False,
        null=True,
    )
    access_code = models.CharField(
        _('access code'),
        max_length=8,
        blank=True,
        null=False,
        editable=False,
        default='',
    )
    approved = models.BooleanField(
        _('approved'),
        default=False,
        null=False,
        blank=False,
    )

    @models.permalink
    def get_absolute_url(self):
        kwargs = {'pk': self.pk}
        return "seuranta_api_v2_competitor_detail", (), kwargs

    absolute_url = property(get_absolute_url)

    @property
    def route(self):
        route_sections = self.route_sections.all()
        route = set()
        for route_section in route_sections:
            route = route.union(route_section.route)
        return sorted(route)

    def reset_access_code(self):
        while True:
            code = make_random_code(5)
            existing = Competitor.objects.filter(
                access_code=code,
                competition_id=self.competition_id
            ).count()
            if existing == 0:
                self.access_code = code
                break

    def reset_api_token(self):
        self.api_token = short_uuid()

    def clean(self):
        super(Competitor, self).clean()
        if self.start_time \
           and not (self.competition.start_date <= self.start_time
                    <= self.competition.end_date):
            raise ValidationError(
                'start_time does not respect competition schedule'
            )

    def save(self, *args, **kwargs):
        if not self.api_token:
            self.reset_api_token()
        if not self.access_code:
            self.reset_access_code()
        super(Competitor, self).save(*args, **kwargs)

    def __unicode__(self):
        return u"{} \"{}\" > {}".format(_(u"Competitor"), self.name,
                                        self.competition)

    class Meta:
        unique_together = (
            ("api_token", "competition"),
            ("access_code", "competition"),
        )
        ordering = ["competition", "start_time", "name"]
        verbose_name = _("competitor")
        verbose_name_plural = _("competitors")

    def serialize(self, include_private_data=False):
        if self.start_time is not None:
            start_time = format_date_iso(self.start_time)
        else:
            start_time = None
        result = {
            'id': self.id,
            'name': self.name,
            'short_name': self.short_name,
            'starting_time': start_time,
        }
        if include_private_data:
            result['access_code'] = self.access_code
        return result

    def dump_json(self):
        return json.dumps(self.serialize())


class RouteSection(models.Model):
    competitor = models.ForeignKey(Competitor,
                                   verbose_name=_("competitor"),
                                   related_name="route_sections")
    encoded_data = models.TextField(_("encoded data"), blank=True)
    update_date = models.DateTimeField(_("last update date"), auto_now=True)
    _start_datetime = models.DateTimeField(blank=True, null=True,
                                           editable=False)
    _finish_datetime = models.DateTimeField(blank=True, null=True,
                                            editable=False)
    _north = models.FloatField(
        blank=True, null=True,
        validators=[validate_latitude], editable=False
    )
    _south = models.FloatField(
        blank=True, null=True,
        validators=[validate_latitude], editable=False
    )
    _east = models.FloatField(
        blank=True, null=True,
        validators=[validate_longitude], editable=False
    )
    _west = models.FloatField(
        blank=True, null=True,
        validators=[validate_longitude], editable=False
    )
    _point_nb = models.PositiveIntegerField(
        default=0
    )

    @property
    def route(self):
        return gps_codec.decode(self.encoded_data)

    @route.setter
    def route(self, value):
        self.encoded_data = gps_codec.encode(value)

    @property
    def bounds(self):
        route = self.route
        if route is None or len(route) == 0:
            return None
        route = sorted(route)
        north = -90
        south = 90
        east = -180
        west = 180
        start_t = float('inf')
        end_t = -float('inf')
        for p in route:
            north = max(north, p.coordinates.latitude)
            south = min(south, p.coordinates.latitude)
            west = min(west, p.coordinates.longitude)
            east = max(east, p.coordinates.longitude)
            start_t = min(start_t, p.timestamp)
            end_t = max(end_t, p.timestamp)
        return {
            'start_timestamp': start_t,
            'finish_timestamp': end_t,
            'north': north,
            'south': south,
            'west': west,
            'east': east,
        }

    def save(self, *args, **kwargs):
        bounds = self.bounds
        if bounds:
            self._start_datetime = utc.localize(
                datetime.datetime.fromtimestamp(bounds['start_timestamp'])
            )
            self._finish_datetime = utc.localize(
                datetime.datetime.fromtimestamp(bounds['finish_timestamp'])
            )
            self._north = bounds['north']
            self._south = bounds['south']
            self._west = bounds['west']
            self._east = bounds['east']
        self._point_nb = len(self.route)
        super(RouteSection, self).save(*args, **kwargs)

    class Meta:
        ordering = ["-update_date"]
        verbose_name = _("route section")
        verbose_name_plural = _("route sections")
