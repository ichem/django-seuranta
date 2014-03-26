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

from geoposition import Geoposition

from .models import Competition, Competitor, RouteSection, Tracker
from .utils import format_date_iso
from .utils import gps_codec

import datetime, time
import simplejson as json

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

@login_required
@never_cache
def dashboard(request):
	return render_to_response(
		'seuranta/dashboard.html',
		{},
		RequestContext(request)
	)

@login_required
@never_cache
def dashboard_edit_race(request, uuid=None):
    obj=None
    if uuid is not None:
    	obj = get_object_or_404(
	    	Competition,
		    uuid = uuid,
		)
        if obj.publisher != request.user:
            return HttpResponse(status=403)

    return render_to_response(
		'seuranta/competition_editor.html',
		{
		    'competition':obj,
		},
		RequestContext(request)
	)

def tracker(request):
    return render_to_response(
        'seuranta/tracker.html',
        {},
        RequestContext(request)
    )

def latest_competition_mod(request, uuid):
    c = Competition.objects.filter(uuid=uuid)
    if len(c)>0:
        c = c[0]
        tim = now()
        if c.last_update < c.opening_date and tim > c.opening_date:
            return c.opening_date
        return c.last_update
    return None

@condition(last_modified_func=latest_competition_mod, etag_func=None)
def race_view(request, uuid):
    obj = get_object_or_404(Competition, uuid=uuid)
    if obj.publication_policy == "private" and obj.publisher != request.user:
        return HttpResponse(status=403)

    tim = now()
    if tim < obj.opening_date:
        return render_to_response(
            'seuranta/pre_race.html',
            {
                'object':obj,
                'competition':obj,
            },
            RequestContext(request)
        )

    return render_to_response(
        'seuranta/race.html',
        {
            'object':obj,
            'competition':obj,
        },
        RequestContext(request)
    )

@csrf_exempt
@cache_page(5)
def api(request, action="tracker/update"):
    response = {
        "status":"KO",
        "code":400,
        "msg":"Invalid api request",
        "data":{
            "help":""
        }
    }

    if request.method == "POST":
        if action == "race/delete":
            uuid = request.POST.get('uuid')
            try:
                obj = Competition.objects.get(uuid = uuid)
            except Competiton.DoesNotExist:
                response = {
                    "status":"KO",
                    "code":404,
                    "msg":"Race do not exist",
                    "data":{
                        "uuid":uuid
                    }
                }
            else:
                if request.user.is_authenticated() and obj.publisher == request.user:
                    obj.delete()
                    response = {
                        "status":"OK",
                        "msg":"Race deleted",
                        "data":{
                            "uuid":uuid
                        }
                    }
                else:
                    response = {
                        "status":"KO",
                        "code":403,
                        "msg":"Unauthorized api call",
                        "data":{
                            "uuid":uuid
                        }
                    }
    # if request.method == "POST":
    	# if action == ...:
            # ...
    	elif action == "tracker/update":
            uuid = request.POST.get("uuid")
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
                if 'encoded_data' in request.POST:

                    encoded_data = request.POST.get("encoded_data")
                    
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

                elif 'latitude' in request.POST and 'longitude' in request.POST:
                    try:
                        lat = float(request.POST.get("latitude"))
                        lon = float(request.POST.get("longitude"))
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
                    
                    live_competitors = tracker.competitors.approved().filter(
                        competition__opening_date__lt=tim,
                        competition__closing_date__gt=tim,
                    )

                    need_approval_competitors = tracker.competitors.filter(
                        competition__opening_date__lt=tim,
                        competition__closing_date__gt=tim,
                        is_approved=False
                    )
                    
                    futur_competitor = tracker.competitors.approved().filter(
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
                            "live_competitors":len(live_competitors),
                            "pending_approvals":len(need_approval_competitors),
                            "next_competitor_opening":next_event_registered_opening,
                        }
                    }
        elif action == "clock/drift":
            try:
                timestamp = float(request.POST.get('timestamp'))
            except:
                response = {
                    "status":"KO",
                    "code":400,
                    "msg":"Invalid data",
                    "data":{
                        "timestamp":request.POST.get('timestamp'),
                    }
                }
            else:
                tim = time.time()
                drift = tim-timestamp

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
    else:
        if action == "clock/time":
            tim = time.time()

            response = {
                "status":"OK",
                "code":200,
                "msg":"",
                "data":{
                    "server_time":tim,
                }
            }

        elif action == "competitor/routes":
            uuids = request.GET.getlist('competitor_uuid[]')

            last_update_timestamp = request.GET.get("last_update_timestamp",None)
            
            min_timestamp = request.GET.get("min_timestamp",None)
            max_timestamp = request.GET.get("max_timestamp",None)

            last_update_datetime = None
            if last_update_timestamp is not None:
                try:
                    las_update_timestamp = float(last_update_timestamp)
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
                    mix_timestamp = float(mix_timestamp)
                    min_datetime = utc.localize(datetime.datetime.fromtimestamp(float(time_end_raw)/1e3))
                except ValueError:
                    pass

            if len(uuids)>0:
                query = reduce(lambda query,uuid:query|Q(uuid=uuid), uuids, Q())

                competitors = Competitor.objects.approved().filter(query)
                
                response = {
                    "status":"OK",
                    "code":200,
                    "msg":"",
                    "data":{
                        "routes":[]
                    }
                }

                if len(competitors)>0:
                    query = reduce(lambda q,competitor:q|Q(competitor_id=competitor.id), competitors, Q())

                    if last_update_datetime is not None:
                        query &= Q(last_update_date_time__gte=last_update)

                route_sections = RouteSection.objects.filter(query)

                for route_section in route_sections:
                    timestamp = (route_section.last_update.replace(tzinfo=None) - datetime.datetime.utcfromtimestamp(0)).total_seconds()
                    response['routes'].append({
                        'competitor':{
                            'uuid':route_section.competitor.uuid,
                        },
                        'udpate_timestamp':timestamp,
                        'encoded_data':route_section.encoded_data
                    })

    response_json = json.dumps(response, use_decimal=True)

    if 'callback' in request.GET:
        data = '%s(%s);' % (request.REQUEST['callback'], response_json)
        HttpResponse(response_json, content_type='application/json')
    return HttpResponse(response_json, content_type='application/json')
