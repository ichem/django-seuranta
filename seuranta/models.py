import datetime
import base64
import re
from PIL import Image
from pytz import common_timezones
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils.timezone import utc, now
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from seuranta.conf import settings
from seuranta.storage import OverwriteStorage
from seuranta.fields import ShortUUIDField
from seuranta.utils import (slugify, make_random_code)
from seuranta.utils.geo import GeoLocationSeries
from seuranta.utils.validators import (validate_nice_slug, validate_latitude,
                                       validate_longitude)


BLANK_SIZE = {'width': 1, 'height': 1}
BLANK_FORMAT = "image/gif"
BLANK_GIF_B64 = "R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="
BLANK_DATA_URI = "data:" + BLANK_FORMAT + ";base64," + BLANK_GIF_B64
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
    ("bck", _('Background only')),
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
    tmp_path.append(basename[1])
    tmp_path.append(basename)
    return os.path.join(*tmp_path)


class Competition(models.Model):
    id = ShortUUIDField(primary_key=True)
    updated = models.DateTimeField(auto_now=True)
    timezone = models.CharField(
        verbose_name=_("local timezone"),
        help_text=_("timezone used at competition center"),
        max_length=50,
        default="UTC",
        choices=[(tz, tz) for tz in common_timezones]
    )
    start_date = models.DateTimeField(
        _("opening date") + " (%s)" % settings.TIME_ZONE,
    )
    end_date = models.DateTimeField(
        _("closing date") + " (%s)" % settings.TIME_ZONE,
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
    latitude = models.FloatField(_('latitude'),
                                 validators=[validate_latitude],
                                 default=0.0)
    longitude = models.FloatField(_('longitude'),
                                  validators=[validate_longitude],
                                  default=0.0)
    zoom = models.PositiveIntegerField(_('default zoom'),
                                       default=1)

    live_delay = models.PositiveIntegerField(
        _('live delay'), default=30, help_text=_('delay of live in seconds')
    )

    @property
    def publisher_name(self):
        return self.publisher.username

    def is_started(self):
        return self.start_date < now()

    def is_completed(self):
        return self.end_date < now()

    def is_live(self):
        return self.is_started() and not self.is_completed()

    @property
    def approved_competitors(self):
        if self.signup_policy != 'open':
            return self.competitors.filter(approved=True)
        else:
            return self.competitors

    @property
    def approved_competitor_count(self):
        return self.approved_competitors.count()

    def get_map(self):
        if hasattr(self, 'defined_map'):
            return self.defined_map
        return Map(competition_id=self.pk)

    map = property(get_map)

    @property
    def pending_competitors(self):
        if self.signup_policy == 'open':
            return self.competitors.none()
        else:
            return self.competitors.filter(approved=False)

    @property
    def pending_competitor_count(self):
        return self.pending_competitors.count()

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
        return u"{} \"{}\"".format(_(u"Competition"), self.name)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = _("competition")
        verbose_name_plural = _("competitions")


class Map(models.Model):
    competition = models.OneToOneField(Competition,
                                       related_name='defined_map',
                                       primary_key=True)
    updated = models.DateTimeField(auto_now=True)
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
        help_text=_("Use online calibration tool if unsure"),
    )
    display_mode = models.CharField(
        _("display mode"),
        max_length=8,
        choices=MAP_DISPLAY_CHOICES,
        default="map+bck"
    )
    background_tile_url = models.URLField(
        _('background tile url'),
        blank=True,
        help_text=''.join([
            ugettext("e.g") +
            " https://{s}.example.com/{x}_{y}_{z}.png, " +
            ugettext("Leave blank to use OpenStreetMap")
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
            return BLANK_GIF_B64.decode('base64')
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
            r'^data:image/(?P<format>jpeg|png|gif);base64,'
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
        return "seuranta_api_competition_map_download", (), kwargs
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

    class Meta:
        verbose_name = _("map")
        verbose_name_plural = _("maps")


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
    updated = models.DateTimeField(auto_now=True)
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
        _('start time') + " (%s)" % settings.TIME_ZONE,
        null=True,
        blank=True,
    )
    access_code = models.CharField(
        _('access code'),
        max_length=8,
        blank=True,
        null=False,
        default='',
    )
    approved = models.BooleanField(
        _('approved'),
        default=False,
        null=False,
        blank=False,
    )

    def get_full_route(self):
        result = GeoLocationSeries('')
        for route in self.defined_routes.all():
            result = result.union(route.data)
        return result

    def set_full_route(self, value):
        if self.defined_routes.exists():
            self.defined_routes.all().delete()
        if len(value) > 0:
            new_route = Route(competitor_id=self.pk)
            new_route.data = value
            new_route.save()

    route = property(get_full_route, set_full_route)

    def merge_route(self):
        route = self.get_full_route()
        self.set_full_route(route)

    @property
    def token(self):
        if hasattr(self, 'set_token'):
            return self.set_token.key
        return None

    @token.setter
    def token(self, value):
        if hasattr(self, 'set_token'):
            self.set_token.key = value
            self.set_token.save()
        c = CompetitorToken(key=value, competitor=self, created=timezone.now())
        c.save()

    @staticmethod
    def generate_access_code():
        return make_random_code(settings.SEURANTA_ACCESS_CODE_LENGTH)

    def reset_access_code(self):
        while True:
            code = self.generate_access_code()
            existing = Competitor.objects.filter(
                access_code=code,
                competition_id=self.competition_id
            ).count()
            if existing == 0:
                self.access_code = code
                break

    def clean(self):
        super(Competitor, self).clean()
        if self.start_time \
           and not (self.competition.start_date <= self.start_time
                    <= self.competition.end_date):
            raise ValidationError(
                'start_time does not respect competition schedule'
            )

    def __unicode__(self):
        return u"{} \"{}\" > {}".format(_(u"Competitor"), self.name,
                                        self.competition)

    class Meta:
        ordering = ["competition", "start_time", "name"]
        verbose_name = _("competitor")
        verbose_name_plural = _("competitors")


class CompetitorToken(models.Model):
    key = models.CharField(max_length=40, primary_key=True)
    competitor = models.OneToOneField(Competitor, related_name='set_token')
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(CompetitorToken, self).save(*args, **kwargs)

    @staticmethod
    def generate_key():
        return make_random_code(32)

    def __str__(self):
        return self.key

    class Meta:
        verbose_name = _("competitor publishing token")
        verbose_name_plural = _("competitor publishing tokens")


class Route(models.Model):
    id = ShortUUIDField(_("identifier"), primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    competitor = models.ForeignKey(Competitor,
                                   verbose_name=_("route"),
                                   related_name="defined_routes",)
    encoded_data = models.TextField(_("encoded route points"))
    _start_datetime = models.DateTimeField(editable=False)
    _finish_datetime = models.DateTimeField(editable=False)
    _north = models.FloatField(validators=[validate_latitude], editable=False)
    _south = models.FloatField(validators=[validate_latitude], editable=False)
    _east = models.FloatField(validators=[validate_longitude], editable=False)
    _west = models.FloatField(validators=[validate_longitude], editable=False)
    _count = models.PositiveIntegerField(editable=False)

    @property
    def data(self):
        return GeoLocationSeries(self.encoded_data)

    @data.setter
    def data(self, value):
        if not isinstance(value, GeoLocationSeries):
            value = GeoLocationSeries(value)
        self.encoded_data = str(value)

    def get_bounds(self):
        if not self.encoded_data:
            return None
        return self.data.get_bounds()

    def save(self, *args, **kwargs):
        bounds = self.get_bounds()
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
        self._count = len(self.data)
        super(Route, self).save(*args, **kwargs)

    # define token property to use with serializer
    @property
    def token(self):
        return None

    class Meta:
        ordering = ["-_start_datetime", 'competitor']
        verbose_name = _("route")
        verbose_name_plural = _("routes")
