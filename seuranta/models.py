from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import ugettext as _
from django.utils.timezone import utc, now
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe


from .utils import short_uuid
from .utils.validators import validate_latitude, validate_longitude
from .utils import gps_codec

from timezone_field import TimeZoneField

import datetime
import imghdr
import base64
import json

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
try:
    from PIL import Image
except ImportError:
    import Image

class Tracker(models.Model):
    uuid = models.CharField(
        _("uuid"),
        max_length=36,
        editable=False,
        default=lambda:short_uuid(),
        unique=True
    )

    publisher = models.ForeignKey(
        User,
        verbose_name=_("publisher"),
        related_name="trackers",
        editable=False
    )

    handle = models.CharField(
        _('handle'),
        max_length=52,
        blank=True
    )

    pref_name = models.CharField(
        _('prefered name'),
        max_length=52,
        blank=True
    )

    creation_date = models.DateTimeField(
        _("creation date"),
        auto_now_add=True
    )

    last_seen = models.DateTimeField(
        _("last date seen"),
        auto_now=True
    )

    def get_absolute_url(self):
        return "%s#%s"%(reverse("seuranta.views.tracker"), self.uuid)
    get_absolute_url.short_description = _("Link")
    absolute_url = property(get_absolute_url)

    def get_html_link(self):
        return "<a href='%s' class='tracker_link'>Link to tracker</a>"%self.absolute_url
    get_html_link.short_description = _('tracker link')
    get_html_link.allow_tags = _('tracker link')

    def __unicode__(self):
        return u"Tracker \"%s\", \"%s\""%(self.uuid, self.handle)

    class Meta:
        ordering = ["-creation_date"]
        verbose_name = _("tracker")
        verbose_name_plural = _("trackers")

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


PUBLICATION_POLICY_CHOICES = (
   ("private", _('Private')),
   ("secret", _('Secret')),
   ("public", _('Public')),
)

INSCRIPTION_POLICY_CHOICES = (
   ("intern", _('No')),
   ("open", _('Yes, but require approval from you')),
   ("anarchy", _('Yes, no need for approval')),
)

class Competition(models.Model):
    uuid = models.CharField(
        _('uuid'),
        max_length=36,
        editable=False,
        default=lambda:short_uuid(),
        unique=True
    )

    publisher = models.ForeignKey(
        User,
        verbose_name=_("publisher"),
        related_name="competitions",
        editable=False
    )

    publication_policy = models.CharField(
        _("publication policy"),
        max_length=8,
        choices=PUBLICATION_POLICY_CHOICES,
        default="public"
    )

    inscription_policy = models.CharField(
        _("open registration"),
        max_length=8,
        choices=INSCRIPTION_POLICY_CHOICES,
        default="intern"
    )

    last_update = models.DateTimeField(_("last update"), auto_now=True)

    name = models.CharField(
        _('name'),
        max_length=52,
        default="Untitled"
    )

    map = models.ImageField(
        _("map"),
        upload_to = map_upload_path,
        height_field = "map_height",
        width_field = "map_width"
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

    @property
    def map_format(self):
        type = imghdr.what(self.map.file)
        return "image/%s"%type

    @property
    def map_dataURI(self):
        return "data:%s;base64,%s"%(self.map_format, base64.b64encode(self.map.file.read()))

    calibration_string = models.CharField(
        _("calibration string"),
        max_length=255,
        help_text = mark_safe(_("<a href='http://rphl.net/files/calibrate_map.html'>Online tool</a>")),
    )

    @property
    def calibration_points(self):
        pts = self.calibration_string.split("|")
        if len(pts)==12:
            try:
                pts = [float(x) for x in pts]
            except:
                return []
            return [
                {"lat":pts[1], "lon":pts[0], "x":pts[2], "y":pts[3]},
                {"lat":pts[5], "lon":pts[4], "x":pts[6], "y":pts[7]},
                {"lat":pts[9], "lon":pts[8], "x":pts[10], "y":pts[11]}
            ]
        return []

    start_date = models.DateTimeField(
        _("start date"),
        default=lambda:now()
    )

    end_date = models.DateTimeField(
        _("end date"),
        default=lambda:now()+datetime.timedelta(days=1)
    )

    timezone = TimeZoneField(verbose_name=_("timezone"), default="UTC")

    @property
    def utc_start_date(self):
        return utc.localize(self.timezone.localize(self.start_date.replace(tzinfo=None)).astimezone(utc).replace(tzinfo=None))

    @utc_start_date.setter
    def utc_start_date(self, value):
        self.start_date = utc.localize(utc.localize(value.replace(tzinfo=None)).astimezone(self.timezone).replace(tzinfo=None))
    _utc_start_date = models.DateTimeField(
        _("start date (utc)"),
        editable=False
    )

    @property
    def utc_end_date(self):
        return utc.localize(self.timezone.localize(self.end_date.replace(tzinfo=None)).astimezone(utc).replace(tzinfo=None))

    @utc_end_date.setter
    def utc_end_date(self, value):
        self.end_date = utc.localize(utc.localize(value.replace(tzinfo=None)).astimezone(self.timezone).replace(tzinfo=None))
    _utc_end_date = models.DateTimeField(
        _("end date (utc)"),
        editable=False
    )

    @property
    def is_started(self):
        return self.utc_start_date<now()

    @property
    def is_completed(self):
        return self.utc_end_date<now()

    @property
    def is_current(self):
        return self.is_started and not self.is_completed

    def end_competition(self):
        self.utc_end_date = now()

    tile_url_template = models.URLField(
        _('tile url field'),
        blank=True,
        null=True
    )

    @models.permalink
    def get_absolute_url(self):
        return ("seuranta.views.race_view", (), {'uuid':self.uuid})
    absolute_url = property(get_absolute_url)

    @property
    def iso_start_date(self):
        return self.utc_start_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    @property
    def iso_end_date(self):
        return self.utc_end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    def serialize(self):
        result = {
            'uuid':self.uuid,
            'name':self.name,
            'start_date':self.iso_start_date,
            'end_date':self.iso_end_date,
            'timezone':str(self.timezone),
            'tile_url_template':self.tile_url_template,
            'url':self.absolute_url,
            'competitors':[]
        }
        if self.is_started:
            result['map_dataURI']=self.map_dataURI
            result['calibration_points']=self.calibration_points

        for c in self.competitors.approved():
            result['competitors'].append(c.serialize())
        return result

    @property
    def as_json(self):
        return json.dumps(self.serialize())

    def save(self, *args, **kwargs):
        self._utc_start_date = self.utc_start_date
        self._utc_end_date = self.utc_end_date
        super(Competition, self).save(*args, **kwargs)

    def __unicode__(self):
        return u"Competition \"%s\", \"%s\""%(self.uuid, self.name)

    class Meta:
        ordering = ["-_utc_start_date"]
        verbose_name = _("competition")
        verbose_name_plural = _("competitions")

@receiver(post_delete, sender=Competition)
def competition_post_delete_handler(sender, **kwargs):
    competition = kwargs['instance']
    storage, path = competition.map.storage, competition.map.path
    storage.delete(path)

class CompetitorManager(models.Manager):
    def approved(self):
        return self.get_queryset().filter(approved=True)

class Competitor(models.Model):
    objects = CompetitorManager()
    uuid = models.CharField(
        _("uuid"),
        max_length=36,
        editable=False,
        default=lambda:short_uuid(),
        unique=True
    )
    competition = models.ForeignKey(
        Competition,
        verbose_name=_('competition'),
        related_name="competitors"
    )
    name = models.CharField(
        _('name'),
        max_length=52
    )
    shortname = models.CharField(
        _('short name'),
        max_length=52
    )
    start_time = models.DateTimeField(
        _('start time'),
        null=True,
        blank=True
    )


    @property
    def utc_start_time(self):
        return utc.localize(self.competition.timezone.localize(self.start_time.replace(tzinfo=None)).astimezone(utc).replace(tzinfo=None))

    @utc_start_time.setter
    def utc_start_time(self, value):
        self.start_time = utc.localize(utc.localize(value.replace(tzinfo=None)).astimezone(self.competition.timezone).replace(tzinfo=None))
    _utc_start_time = models.DateTimeField(
        _("start time (utc)"),
        editable=False,
        default=lambda:now()
    )

    @property
    def iso_start_time(self):
        return self.utc_start_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    tracker = models.ForeignKey(
        Tracker,
        verbose_name=_('tracker'),
        related_name="competitors"
    )

    approved = models.BooleanField(
        _('approved'),
        default=True
    )

    @property
    def route(self):
        route_sections = self.route_sections.all()
        route = set()
        for route_section in route_sections:
            route = route.union(route_section.route)
        return sorted(route)

    def serialize(self):
        return {
            'uuid':self.uuid,
            'name':self.name,
            'shortname':self.shortname,
            'start_time':self.iso_start_time,
        }

    @property
    def as_json(self):
        return json.dumps(self.serialize())

    def save(self, *args, **kwargs):
        self._utc_start_time = self.utc_start_time
        super(Competitor, self).save(*args, **kwargs)

    def __unicode__(self):
        return u"Competitor \"%s\" in %s"%(self.name, self.competition)

    class Meta:
        ordering = ["competition", "start_time", "name"]
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

    @property
    def start_time(self):
        return self.bounds
    _start_time = models.DateTimeField(blank=True, null=True, editable=False)
    _end_time = models.DateTimeField(blank=True, null=True, editable=False)

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

        if len(route)==0:
            return None

        route=sorted(route)

        north=-90
        south=90
        east=-180
        west=180
        start=float('inf')
        end=0
        for p in route:
            if p['lat']>north:
                north=p['lat']
            if p['lat']<south:
                south=p['lat']
            if p['lon']<west:
                west=p['lon']
            if p['lon']>east:
                east=p['lon']
            if p['t']<start:
                start=p['t']
            if p['t']>end:
                end=p['t']

        return {
            'start_time':start,
            'end_time':end,
            'north':north,
            'south':south,
            'west':west,
            'east':east,
        }

    def save(self, *args, **kwargs):
        bounds = self.bounds
        if bounds:
            self._start_time=utc.localize(datetime.datetime.fromtimestamp(bounds['start_time']))
            self._end_time=utc.localize(datetime.datetime.fromtimestamp(bounds['end_time']))
            self._north=bounds['north']
            self._south=bounds['south']
            self._west=bounds['west']
            self._east=bounds['east']
        super(RouteSection, self).save(*args, **kwargs)

    class Meta:
        ordering = ["-last_update"]
        verbose_name = _("route section")
        verbose_name_plural = _("route sections")
