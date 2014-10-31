from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.decorators.http import condition
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.timezone import utc, now
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.views.decorators.cache import never_cache
from django.contrib.sites.models import get_current_site

from globetrotting import GeoLocation

from .models import Competition, Competitor, RouteSection
from django.contrib.auth.models import User
from .utils import format_date_iso
from .utils import gps_codec

import datetime, time
import simplejson as json

from .utils.validators import validate_short_uuid

RERUN_TEMPLATE_URL = "http://3drerun.worldofo.com/2d/index.php" \
                     "?liveid=%s&lservice=dseu"
BLANK_GIF = "R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="

def home(request):
    tim = now()
    qs = Competition.objects.all()
    live = qs.filter(
        opening_date__lte=tim,
        closing_date__gte=tim,
        publication_policy="public"
    ).order_by('opening_date')
    upcoming = qs.filter(
        opening_date__gt=tim,
        closing_date__gt=tim,
        publication_policy="public"
    ).order_by('opening_date')
    past = qs.filter(
        opening_date__lt=tim,
        closing_date__lt=tim,
        publication_policy="public"
    ).order_by('-closing_date')
    return render_to_response(
        'seuranta/home.html',
        {
            'live':live,
            'upcoming':upcoming,
            'past':past,
        },
        RequestContext(request)
    )


def user_home(request, publisher):
    tim = now()
    user = get_object_or_404(User, username__iexact=publisher)
    qs = Competition.objects.filter(publisher=user)
    live = qs.filter(
        opening_date__lte=tim,
        closing_date__gte=tim,
        publication_policy="public"
    )
    upcoming = qs.filter(
        opening_date__gt=tim,
        closing_date__gt=tim,
        publication_policy="public"
    )
    past = qs.filter(
        opening_date__lt=tim,
        closing_date__lt=tim,
        publication_policy="public"
    )
    return render_to_response(
        'seuranta/home.html',
        {
            'live':live,
            'upcoming':upcoming,
            'past':past,
        },
        RequestContext(request)
    )


@login_required
def dashboard(request):
    if request.REQUEST.get('id') and request.REQUEST.get('view')=='trackers':
        c = get_object_or_404(
            Competition,
            publisher=request.user,
            pk=request.REQUEST.get('id'),
        )
        return render_to_response(
            'seuranta/dashboard_trackers.html',
            {
                "competition":c
            },
            RequestContext(request)
        )
    if request.REQUEST.get('id') and request.POST.get('action')=='delete':
        id = request.REQUEST.get('id')
        c = get_object_or_404(
            Competition,
            publisher=request.user,
            pk=id,
        )
        c.delete()
        return HttpResponse(
            json.dumps({
                "status":"OK",
                "code":200,
                "msg":"Race deleted!"
            }),
            content_type='application/json'
        )
    return render_to_response(
        'seuranta/dashboard.html',
        {
        },
        RequestContext(request)
    )



def tracker(request, uuid=None):
    if uuid is not None:
        try:
            validate_short_uuid(uuid)
        except:
            return HttpResponse(status=404)
        else:
            tracker = uuid
    else:
        tracker = None

    return render_to_response(
        'seuranta/tracker.html',
        {'uuid':tracker},
        RequestContext(request)
    )


def race_latest_mod(request, publisher, slug):
    try:
        user = User.objects.get(username__iexact=publisher)
    except User.DoesNotExist:
        return None
    try:
        c = Competition.objects.get(
            publisher=user,
            slug=slug,
        )
    except:
        return None
    tim = now()
    if c.last_update < c.opening_date and tim > c.opening_date:
        return c.opening_date
    return c.last_update


@condition(last_modified_func=race_latest_mod, etag_func=None)
def race_view(request, publisher, slug):
    user = get_object_or_404(
        User,
        username__iexact=publisher
    )
    obj = get_object_or_404(
        Competition,
        slug=slug,
        publisher=user
    )
    if obj.publication_policy == 'private' and obj.publisher != request.user \
       and not request.user.is_superuser:
        return HttpResponse(status=403)
    tim = now()
    if tim < obj.opening_date:
        return render_to_response(
            'seuranta/pre_race.html',
            {
                'competition':obj,
            },
            RequestContext(request)
        )
    return render_to_response(
        'seuranta/race.html',
        {
            'competition':obj,
        },
        RequestContext(request)
    )


@condition(last_modified_func=race_latest_mod, etag_func=None)
def race_rerun_view(request, publisher, slug):
    user = get_object_or_404(
        User,
        username__iexact=publisher
    )
    tim = now()
    obj = get_object_or_404(
        Competition,
        slug=slug,
        publisher=user,
        closing_date__lt=tim
    )
    if obj.publication_policy == 'private' and obj.publisher != request.user:
        return HttpResponse(status=403)
    return HttpResponseRedirect(
        RERUN_TEMPLATE_URL % obj.uuid
    )


@csrf_exempt
@cache_page(5)
def api_v1(request, action):
    response = {
        "status":"KO",
        "code":400,
        "msg":"Invalid api request",
        "data":{
            "help":""
        }
    }
    if action == "competitor/update":
        uuid = request.REQUEST.get("secret")
        try:
            validate_short_uuid(uuid)
        except:
            response = {
                "status":"KO",
                "code":404,
                "msg":"Invalid secret",
                "data":{
                    "secret":uuid
                }
            }
        else:
            route = None
            if 'encoded_data' in request.REQUEST:
                encoded_data = request.REQUEST.get("encoded_data")
                try:
                    route = gps_codec.decode(encoded_data)
                except:
                    response = {
                        "status":"KO",
                        "code":400,
                        "msg":"Invalid encoded data",
                        "data":{
                            "secret":uuid,
                            "encoded_data":encoded_data,
                        }
                    }
            elif 'latitude' in request.REQUEST \
            and 'longitude' in request.REQUEST:
                try:
                    lat = float(request.REQUEST.get("latitude"))
                    lon = float(request.REQUEST.get("longitude"))
                    tim = time.time()
                except:
                    response = {
                        "status":"KO",
                        "code":400,
                        "msg":"Invalid data",
                        "data":{
                            "secret":uuid,
                        }
                    }
                else:
                    location = GeoLocation(tim, (lat, lon))
                    route = [location]
            if route is not None and len(route)>0:
                tim = now()
                live_competitors = Competitor.objects.filter(
                    tracker = uuid,
                    competition__opening_date__lte=tim,
                    competition__closing_date__gte=tim,
                )
                futur_competitors = Competitor.objects.filter(
                    tracker = uuid,
                    competition__opening_date__gt=tim,
                )
                next_start = None
                if len(futur_competitors)>0:
                    next_competitor = futur_competitors.order_by(
                        'competition__opening_date'
                    )[0]
                    next_start = format_date_iso(
                        next_competitor.competition.opening_date
                    )
                for c in live_competitors:
                    section = RouteSection(competitor=c)
                    section.route = route
                    section.save()
                last_location = route[-1]
                response = {
                    "status":"OK",
                    "code":200,
                    "msg":"Data received",
                    "data":{
                        "secret":uuid,
                        "last_location":{
                            "timestamp":last_location.timestamp,
                            "coordinates":{
                                "latitude":last_location.coordinates.latitude,
                                "longitude":last_location.coordinates.longitude,
                            }
                        },
                        "locations_received_count":len(route),
                        "live_competitors_count":live_competitors.count(),
                        "next_competition_start":next_start,
                    }
                }
    elif action == "clock/drift":
        try:
            timestamp = float(request.REQUEST.get('timestamp'))
        except:
            response = {
                "status":"KO",
                "code":400,
                "msg":"Invalid data",
                "data":{
                    "timestamp":request.REQUEST.get('timestamp'),
                }
            }
        else:
            tim = time.time()
            response = {
                "status":"OK",
                "code":200,
                "msg":"",
                "data":{
                    "server_time":tim,
                    "timestamp":timestamp,
                    "drift":tim-timestamp,
                }
            }
    elif action == "competitors/routes":
        uuids = request.REQUEST.getlist('uuid[]')
        last_update_timestamp = request.REQUEST.get(
            "last_update_timestamp", None
        )
        min_timestamp = request.REQUEST.get("min_timestamp",None)
        max_timestamp = request.REQUEST.get("max_timestamp",None)
        last_update_datetime = None
        if last_update_timestamp is not None:
            try:
                last_update_timestamp = float(last_update_timestamp)
                last_update_datetime = utc.localize(
                    datetime.datetime.fromtimestamp(last_update_timestamp)
                )
            except ValueError:
                pass
        max_datetime = None
        if max_timestamp is not None:
            try:
                max_timestamp = float(max_timestamp)
                max_datetime = utc.localize(
                    datetime.datetime.fromtimestamp(max_timestamp)
                )
            except ValueError:
                pass
        min_datetime = None
        if min_timestamp is not None:
            try:
                min_timestamp = float(min_timestamp)
                min_datetime = utc.localize(
                    datetime.datetime.fromtimestamp(min_timestamp)
                )
            except ValueError:
                pass
        if len(uuids)>0:
            competitors_id = Competitor.objects.filter(
                uuid__in=uuids
            ).values_list('pk', flat=True)
            response = {
                "status":"OK",
                "code":200,
                "msg":"",
                "data":{
                    "routes":[]
                }
            }
            if len(competitors_id)>0:
                # extra param as view bound, last update...
                extra_query = Q()
                if last_update_datetime is not None:
                    extra_query &= Q(last_update__gte=last_update_datetime)
                route_sections = RouteSection.objects.filter(
                    extra_query, competitor_id__in=competitors_id
                )
                for route_section in route_sections:
                    timestamp = (
                        route_section.last_update.replace(tzinfo=None)
                        - datetime.datetime.utcfromtimestamp(0)
                    ).total_seconds()
                    response['data']['routes'].append({
                        'competitor':{
                            'uuid':route_section.competitor.uuid,
                        },
                        'udpate_timestamp':timestamp,
                        'encoded_data':route_section.encoded_data
                    })
    else:
        response["msg"]="API endpoint does not exist."
        response["data"]["endpoint"]=action
    response_json = json.dumps(response, use_decimal=True)
    if 'callback' in request.REQUEST and request.REQUEST['callback'] != "":
        data = '%s(%s);' % (request.REQUEST['callback'], response_json)
        return HttpResponse(data, content_type='application/javascript')
    return HttpResponse(response_json, content_type='application/json')


def rerun_time(request):
    response = {}
    tim = time.time()
    response['time'] = "%f"%tim
    response_json = json.dumps(response)
    if 'jsoncallback' in request.REQUEST \
    and request.REQUEST['jsoncallback'] != "":
        data = '%s(%s);' % (request.REQUEST['jsoncallback'], response_json)
        return HttpResponse(data, content_type='application/javascript')
    return HttpResponse(response_json, content_type='application/json')


def rerun_init(request):
    response = {}
    if 'id' in request.REQUEST:
        id = request.REQUEST['id']
        try:
            c = Competition.objects.get(uuid=id, opening_date__lte=now())
        except Competition.DoesNotExist:
            pass
        else:
            response['status'] = "OK"
            response['caltype'] = "3point"
            if c.map is None or not c.is_map_calibrated:
                response['mapw'] = "1"
                response['maph'] = "1"
            else:
                response['mapw'] = "%d"%c.map_width
                response['maph'] = "%d"%c.map_height
            proto = "http"
            if request.is_secure():
                proto += "s"
            domain = (get_current_site(request)).domain
            response['mapurl'] = "%s://%s%s?id=%s"%(
                proto,
                domain,
                reverse("seuranta.views.rerun_map"),
                id
            )
            cp = c.calibration_points
            response['calibration'] = ";".join([
                "%f"%cp[0]['lon'], "%f"%cp[0]['lat'],
                "%f"%cp[0]['x'], "%f"%cp[0]['y'],
                "%f"%cp[1]['lon'], "%f"%cp[1]['lat'],
                "%f"%cp[1]['x'], "%f"%cp[1]['y'],
                "%f"%cp[2]['lon'], "%f"%cp[2]['lat'],
                "%f"%cp[2]['x'], "%f"%cp[2]['y']
            ])
            comp = c.competitors.all().order_by('uuid')
            comps = []
            n = 0
            for cc in comp:
                n += 1
                stime = cc.starting_time
                if stime is None:
                    stime = c.opening_date
                comps.append(";".join([
                    "xx%02d"%n,
                    stime.strftime("%Y%m%d%H%M%S"),
                    cc.name
                ]))
            response['competitors'] = ":".join(comps)
    response_json = json.dumps(response)
    if 'jsoncallback' in request.REQUEST\
    and request.REQUEST['jsoncallback'] != "":
        data = '%s(%s);' % (request.REQUEST['jsoncallback'], response_json)
        return HttpResponse(data, content_type='application/javascript')
    return HttpResponse(response_json, content_type='application/json')


def rerun_data(request):
    response = {}
    if 'id' in request.REQUEST:
        id = request.REQUEST['id']
        try:
            c = Competition.objects.get(uuid=id, opening_date__lte=now())
        except:
            pass
        else:
            response['status'] = "OK"
            comp = c.competitors.all().order_by('uuid')
            n = 0
            cids={}
            cuuids = []
            for cc in comp:
                n += 1
                cids[cc.uuid] = "xx%02d"%n
                cuuids.append(cc.uuid)
            pts_count = 0
            data = []
            rss = RouteSection.objects.filter(
                competitor_id__in=cuuids
            ).order_by('last_update')
            for rs in rss:
                pts = rs.route
                for pt in pts:
                    pts_count += 1
                    data.append(";".join([
                        cids[rs.competitor_id],
                        "%f"%pt.timestamp,
                        "%f"%pt.coordinates.latitude,
                        "%f"%pt.coordinates.longitude
                    ]))
            try:
                offset = int(request.REQUEST.get('p', 0))
            except:
                offset = 0
            response['data'] = ":".join(data[offset:])
            response['lastpos'] = "%d"%pts_count
    response_json = json.dumps(response)
    if 'jsoncallback' in request.REQUEST \
    and request.REQUEST['jsoncallback'] != "":
        data = '%s(%s);' % (request.REQUEST['jsoncallback'], response_json)
        return HttpResponse(data, content_type='application/javascript')
    return HttpResponse(response_json, content_type='application/json')


def rerun_map(request):
    id = request.REQUEST.get('id', None)
    c = get_object_or_404(Competition, uuid=id, opening_date__lte=now())
    if c.map is None or not c.is_map_calibrated:
        response = BLANK_GIF.decode('base64')
    else:
        response = c.map.file
    return HttpResponse(response, content_type=c.map_format)
