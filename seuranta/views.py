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

from globetrotting import GeoCoordinates, GeoLocation

from .models import Competition, Competitor, RouteSection, Tracker
from .utils import format_date_iso
from .utils import gps_codec

import datetime, time
import simplejson as json

from .utils.validators import validate_short_uuid

# Create your views here.
def home(request):
    tim = now()

    live = Competition.objects.filter(
        opening_date__lte=tim,
        closing_date__gte=tim,
        publication_policy="public"
    )
    upcoming = Competition.objects.filter(
        opening_date__gt=tim,
        closing_date__gt=tim,
        publication_policy="public"
    )
    past = Competition.objects.filter(
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

def tracker(request, uuid=None):
    tracker = None
    if uuid is not None:
        try:
            validate_short_uuid(uuid)
        except:
            return HttpResponse(status=404)
        else:
            if request.user.is_authenticated():
                tracker, created = Tracker.objects.get_or_create(uuid=uuid, defaults={'publisher_id':request.user.id})
                if created:
                    tracker.save()
            else:
                tracker = get_object_or_404(Tracker, uuid=uuid)

    return render_to_response(
        'seuranta/tracker.html',
        {'tracker':tracker},
        RequestContext(request)
    )

def latest_competition_mod(request, publisher, slug):
    c = Competition.objects.filter(slug=slug, publisher__username=publisher)

    if len(c)>0:
        c = c[0]
        tim = now()
        if c.last_update < c.opening_date and tim > c.opening_date:
            return c.opening_date
        return c.last_update
    return None

@condition(last_modified_func=latest_competition_mod, etag_func=None)
def race_view(request, publisher, slug):
    obj = get_object_or_404(Competition, slug=slug, publisher__username=publisher)

    if obj.publication_policy == 'private' and obj.publisher != request.user:
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

@csrf_exempt
@cache_page(5)
def api(request, action):
    response = {
        "status":"KO",
        "code":400,
        "msg":"Invalid api request",
        "data":{
            "help":""
        }
    }

    if action == "tracker/update":
        uuid = request.REQUEST.get("uuid")
        try:
            tracker = Tracker.objects.get(uuid=uuid)
        except Tracker.DoesNotExist:
            response = {
                "status":"KO",
                "code":404,
                "msg":"Tracker do not exist",
                "data":{
                    "uuid":uuid
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
                        "msg":"Invalid data",
                        "data":{
                            "uuid":uuid,
                            "encoded_data":encoded_data,
                        }
                    }
            elif 'latitude' in request.REQUEST and 'longitude' in request.REQUEST:
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
                            "uuid":uuid,
                            "encoded_data":encoded_data,
                        }
                    }
                else:
                    location = GeoLocation(tim, (lat, lon))
                    route = [location]

            if route is not None and len(route)>0:
                tim = now()
                tracker.last_location = route[len(route)-1]
                tracker.save()

                live_competitors = tracker.competitors.filter(
                    competition__opening_date__lt=tim,
                    competition__closing_date__gt=tim,
                )

                futur_competitor = tracker.competitors.filter(
                    competition__opening_date__gt=tim,
                )

                next_event_registered_opening = None
                if len(futur_competitor)>0:
                    next_event_registered_opening = futur_competitor.competition.opening_date
                    for f in futur_competitor:
                        if next_event_registered_opening > f.competition.opening_date:
                            next_event_registered_opening = f.competition.opening_date
                    next_event_registered_opening = format_date_iso(next_event_registered_opening)

                for c in live_competitors:
                    section = RouteSection(competitor=c)
                    section.route = route
                    section.save()

                response = {
                    "status":"OK",
                    "code":200,
                    "msg":"Data received",
                    "data":{
                        "uuid":uuid,
                        "last_location":{
                            "timestamp":tracker.last_location.timestamp,
                            "coordinates":{
                                "latitude":tracker.last_location.coordinates.latitude,
                                "longitude":tracker.last_location.coordinates.longitude,
                            }
                        },
                        "locations_received_count":len(route),
                        "live_competitors_count":len(live_competitors),
                        "next_competitor_opening":next_event_registered_opening,
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

        last_update_timestamp = request.REQUEST.get("last_update_timestamp",None)

        min_timestamp = request.REQUEST.get("min_timestamp",None)
        max_timestamp = request.REQUEST.get("max_timestamp",None)

        last_update_datetime = None
        if last_update_timestamp is not None:
            try:
                last_update_timestamp = float(last_update_timestamp)
                last_update_datetime = utc.localize(datetime.datetime.fromtimestamp(last_update_timestamp))
            except ValueError:
                pass

        max_datetime = None
        if max_timestamp is not None:
            try:
                max_timestamp = float(max_timestamp)
                max_datetime = utc.localize(datetime.datetime.fromtimestamp(max_timestamp))
            except ValueError:
                pass

        min_datetime = None
        if min_timestamp is not None:
            try:
                min_timestamp = float(min_timestamp)
                min_datetime = utc.localize(datetime.datetime.fromtimestamp(min_timestamp))
            except ValueError:
                pass

        if len(uuids)>0:
            # http://www.ibm.com/developerworks/opensource/library/os-django-models/index.html?ca=drs

            #query = reduce(lambda query,uuid:query|Q(uuid=uuid), uuids, Q())

            competitors_id = Competitor.objects.filter(uuid__in=uuids).values_list('pk', flat=True)

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
                #query &= reduce(lambda q,competitor:q|Q(competitor_id=competitor.id), competitors, Q())
                if last_update_datetime is not None:
                    extra_query &= Q(last_update__gte=last_update_datetime)


                route_sections = RouteSection.objects.filter(extra_query, competitor_id__in=competitors_id)

                for route_section in route_sections:
                    timestamp = (route_section.last_update.replace(tzinfo=None) - datetime.datetime.utcfromtimestamp(0)).total_seconds()
                    response['data']['routes'].append({
                        'competitor':{
                            'uuid':route_section.competitor.uuid,
                        },
                        'udpate_timestamp':timestamp,
                        'encoded_data':route_section.encoded_data
                    })

    else:
        response['msg']="API endpoint does not exist."
        response['data']['endpoint']=action

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

    if 'jsoncallback' in request.REQUEST and request.REQUEST['jsoncallback'] != "":
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

    if 'jsoncallback' in request.REQUEST and request.REQUEST['jsoncallback'] != "":
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
            rss = RouteSection.objects.filter(competitor_id__in=cuuids).order_by('last_update')
            
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

    if 'jsoncallback' in request.REQUEST and request.REQUEST['jsoncallback'] != "":
        data = '%s(%s);' % (request.REQUEST['jsoncallback'], response_json)
        return HttpResponse(data, content_type='application/javascript')
    return HttpResponse(response_json, content_type='application/json')

def rerun_map(request):
    id = request.REQUEST.get('id', None)
    
    c = get_object_or_404(Competition, uuid=id, opening_date__lte=now())
    
    if c.map is None or not c.is_map_calibrated:
        response = "R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==".decode('base64')
    else:
        response = c.map.file
        
    return HttpResponse(response, content_type=c.map_format)
    
