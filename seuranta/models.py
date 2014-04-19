from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import utc, now
from django.utils.safestring import mark_safe
from django.core.validators import MinLengthValidator
from django.conf import settings

from .utils import short_uuid, slugify, format_date_iso
from .utils import gps_codec

from .fields import ShortUUIDField

from timezone_field import TimeZoneField

from globetrotting.validators import validate_latitude, validate_longitude
from .utils.validators import validate_nice_slug

import datetime
import imghdr
import base64
import json

def map_upload_path(instance=None, filename=None):
    import os.path

    tmppath = [
        'seuranta',
        'maps'
    ]

    if not filename:
        # Filename already stored in database
        filename = instance.map.name
    else:
        filename = short_uuid()
    basename=os.path.basename(filename)
    tmppath.append(basename[0])
    tmppath.append(basename)
    return os.path.join(*tmppath)


class Competition(models.Model):
    uuid = ShortUUIDField(
        _("uuid"),
        primary_key = True
    )

    last_update = models.DateTimeField(_("last update"), auto_now=True)

    publisher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("publisher"),
        related_name="competitions",
        editable=False
    )

    PUBLICATION_POLICY_CHOICES = (
       ("private", _('Private')),
       ("secret", _('Secret')),
       ("public", _('Public')),
    )

    publication_policy = models.CharField(
        _("publication policy"),
        max_length=8,
        choices=PUBLICATION_POLICY_CHOICES,
        default="public"
    )

    name = models.CharField(
        _('name'),
        max_length = 50,
        default="Untitled",
        validators = [MinLengthValidator(4)]
    )

    slug = models.SlugField(
        _('slug'),
        validators = [validate_nice_slug],
        editable = False,
        max_length = 21,
        unique=True
    )

    timezone = TimeZoneField(
        verbose_name=_("timezone"),
        default="UTC",
    )

    map = models.ImageField(
        _("map"),
        upload_to = map_upload_path,
        height_field = "map_height",
        width_field = "map_width",
        blank=True, null=True
    )

    map_width = models.PositiveIntegerField(
        _("map width"),
        editable = False,
        blank=True, null=True
    )

    map_height = models.PositiveIntegerField(
        _("map height"),
        editable = False,
        blank=True, null=True
    )

    BLANK_SIZE = {'width':1, 'height':1}
    @property
    def map_size(self):
        if not self.map or not self.is_map_calibrated:
            return self.BLANK_SIZE
        else:
            return {'width':self.map_width, 'height':self.map_height}

    BLANK_FORMAT = "image/gif"
    @property
    def map_format(self):
        if not self.map or not self.is_map_calibrated:
            return self.BLANK_FORMAT
        type = imghdr.what(self.map.file)
        return "image/%s"%type


    BLANK_DATA_URI = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="
    @property
    def map_dataURI(self):
        if not self.map or not self.is_map_calibrated:
            return self.BLANK_DATA_URI
        return "data:%s;base64,%s"%(self.map_format, base64.b64encode(self.map.file.read()))

    calibration_string = models.CharField(
        _("calibration string"),
        max_length=255,
        blank=True, null=True,
        help_text = mark_safe(_("<a href='http://rphl.net/files/calibrate_map.html'>Online tool</a>")),
    )

    @property
    def is_map_calibrated(self):
        if self.calibration_string is not None:
            pts = self.calibration_string.split("|")
            if len(pts)==12:
                try:
                    pts = [float(x) for x in pts]
                except:
                    pass
                else:
                    return True
        return False

    BLANK_CALIBRATION_POINTS = [
        {"lat":45, "lon":-180, "x":0, "y":.25},
        {"lat":-45, "lon":0, "x":0.5, "y":.75},
        {"lat":0, "lon":180, "x":1, "y":0.5},
    ]

    @property
    def calibration_points(self):
        if self.map is not None and self.is_map_calibrated:
            pts = self.calibration_string.split("|")
            pts = [float(x) for x in pts]
            return [
                {"lat":pts[1], "lon":pts[0], "x":pts[2], "y":pts[3]},
                {"lat":pts[5], "lon":pts[4], "x":pts[6], "y":pts[7]},
                {"lat":pts[9], "lon":pts[8], "x":pts[10], "y":pts[11]}
            ]
        return self.BLANK_CALIBRATION_POINTS

    opening_date = models.DateTimeField(
        _("opening date (UTC)"),
    )

    closing_date = models.DateTimeField(
        _("closing date (UTC)"),
    )

    @property
    def is_started(self):
        return self.opening_date<now()

    @property
    def is_completed(self):
        return self.closing_date<now()

    @property
    def is_current(self):
        return self.is_started and not self.is_completed

    def close_competition(self):
        self.closing_date = now()

    DISPLAY_SETTINGS_CHOICES = (
       ("map+world", _('Map displayed over world map')),
       ("map", _('Map only')),
       ("world", _('World map only')),
    )

    display_settings = models.CharField(
        _("display type"),
        max_length=10,
        choices=DISPLAY_SETTINGS_CHOICES,
        default="map"
    )

    pref_tile_url_pattern = models.URLField(
        _('pref tile url pattern'),
        blank=True,
        null=True,
        help_text = _("Leave blank to use OpenStreetMap as default"),
    )

    @property
    def tile_url_pattern(self):
        if not self.pref_tile_url_pattern:
            return u"http://{s}.tile.osm.org/{z}/{x}/{y}.png"
        else:
            return self.pref_tile_url_pattern

    @models.permalink
    def get_absolute_url(self):
        kwargs = {'publisher':self.publisher.username, 'slug':self.slug}
        return ("seuranta.views.race_view", (), kwargs)
    absolute_url = property(get_absolute_url)

    def serialize(self, include_private_data = False):
        result = {
            'uuid':self.uuid,
            'last_update':format_date_iso(self.last_update),
            'name':self.name,
            'slug':self.slug,
            'publisher':self.publisher.username,
            'publication_policy':self.publication_policy,
            'timezone':str(self.timezone),
            'schedule':{
                'opening_date':format_date_iso(self.opening_date),
                'closing_date':format_date_iso(self.closing_date),
            },
            'competitors':[],
            'map':{
                'display_settings':self.display_settings,
                'tile_url_pattern':self.tile_url_pattern,
            },
        }
        if (self.is_started and self.publication_policy != "private") or include_private_data:
            result['map']['image_data_uri']=self.map_dataURI
            result['map']['calibration_points']=self.calibration_points
            result['map']['size']=self.map_size
            result['map']['format']=self.map_format
        else:
            result['map']['image_data_uri']=self.BLANK_DATA_URI
            result['map']['calibration_points']=self.BLANK_CALIBRATION_POINTS
            result['map']['size']=self.BLANK_SIZE
            result['map']['format']=self.BLANK_FORMAT

        competitor_set = self.competitors.all()

        for c in competitor_set:
            result['competitors'].append(c.serialize())

        return result

    def dump_json(self, include_private_data = False):
        return json.dumps(self.serialize())

    def load_json(self, value):
        #obj = json.load(value)
        return True

    def save(self, *args, **kwargs):
        orig_slug = slugify(self.name)
        desired_slug = orig_slug

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

        if len(desired_slug)==0:
            desired_slug = "noname"
        elif len(desired_slug)<5:
            desired_slug = "%s-%d"%(desired_slug, self.opening_date.year)

        next = 2
        ending = ""

        qs = Competition.objects.all()
        if self.pk is not None:
            qs = qs.exclude(pk=self.pk)

        qs = qs.filter(publisher_id=self.publisher_id)

        while qs.filter(slug = desired_slug)[:1]:
            desired_slug = "%s%s"%(orig_slug[:21-len(ending)], ending)
            ending = "-%d"%next
            next += 1

        self.slug = desired_slug
        super(Competition, self).save(*args, **kwargs)

    def __unicode__(self):
        return u"Competition \"%s\" created by %s, \"%s\""%(self.name, self.publisher, self.uuid)

    class Meta:
        ordering = ["-opening_date"]
        verbose_name = _("competition")
        verbose_name_plural = _("competitions")

@receiver(post_delete, sender=Competition)
def competition_post_delete_handler(sender, **kwargs):
    competition = kwargs['instance']
    if competition.map and competition.map.file:
        storage, path = competition.map.storage, competition.map.path
        storage.delete(path)

class Competitor(models.Model):
    uuid = ShortUUIDField(
        _("uuid"),
        primary_key = True
    )

    competition = models.ForeignKey(
        Competition,
        verbose_name=_('competition'),
        related_name="competitors"
    )

    name = models.CharField(
        _('name'),
        max_length=50
    )

    shortname = models.CharField(
        _('short name'),
        max_length=50
    )

    starting_time = models.DateTimeField(
        _('starting time (UTC)'),
        null=True,
        blank=True
    )

    tracker = ShortUUIDField(
        _("secret"),
        editable=False
    )

    @property
    def route(self):
        route_sections = self.route_sections.all()
        route = set()
        for route_section in route_sections:
            route = route.union(route_section.route)
        return sorted(route)

    def serialize(self):
        result = {
            'uuid':self.uuid,
            'data':{
                'name':self.name,
                'shortname':self.shortname,
                'starting_time':format_date_iso(self.starting_time) if self.starting_time is not None else None,
            }
        }
        return result

    def dump_json(self):
        return json.dumps(self.serialize())

    def save(self, *args, **kwargs):
        if self.tracker is None:
            self.tracker = short_uuid()
        super(Competitor, self).save(*args, **kwargs)

    def __unicode__(self):
        return u"Competitor \"%s\" in %s"%(self.name, self.competition)

    class Meta:
        unique_together = (("tracker", "competition"),)
        ordering = ["competition", "starting_time", "name"]
        verbose_name = _("competitor")
        verbose_name_plural = _("competitors")

class RouteSection(models.Model):
    competitor = models.ForeignKey(Competitor, verbose_name=_("competitor"), related_name="route_sections")

    encoded_data = models.TextField(_("encoded data"), blank=True)

    @property
    def route(self):
        try:
            return gps_codec.decode(self.encoded_data)
        except:
            return set()

    @route.setter
    def route(self, value):
        self.encoded_data = gps_codec.encode(value)

    last_update = models.DateTimeField(_("last update"), auto_now=True)

    _start_datetime = models.DateTimeField(blank=True, null=True, editable=False)
    _finish_datetime = models.DateTimeField(blank=True, null=True, editable=False)

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

    @property
    def bounds(self):
        route = self.route

        if route is None or len(route)==0:
            return None

        route=sorted(route)

        north=-90
        south=90
        east=-180
        west=180
        start_t=float('inf')
        end_t=-float('inf')
        for p in route:
            north = max(north, p.coordinates.latitude)
            south = min(south, p.coordinates.latitude)
            west = min(west, p.coordinates.longitude)
            east = max(east, p.coordinates.longitude)
            start_t = min(start_t, p.timestamp)
            end_t   = max(end_t,   p.timestamp)

        return {
            'start_timestamp':start_t,
            'finish_timestamp':end_t,
            'north':north,
            'south':south,
            'west':west,
            'east':east,
        }

    def save(self, *args, **kwargs):
        bounds = self.bounds
        if bounds:
            self._start_datetime=utc.localize(datetime.datetime.fromtimestamp(bounds['start_timestamp']))
            self._finish_datetime=utc.localize(datetime.datetime.fromtimestamp(bounds['finish_timestamp']))
            self._north=bounds['north']
            self._south=bounds['south']
            self._west=bounds['west']
            self._east=bounds['east']
        super(RouteSection, self).save(*args, **kwargs)

    class Meta:
        ordering = ["-last_update"]
        verbose_name = _("route section")
        verbose_name_plural = _("route sections")
