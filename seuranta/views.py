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

from .models import Competition, Competitor, RouteSection, Tracker
from .utils import gps_codec
from .forms import CompetitionForm, CompetitorForm, CompetitorFormSet

import datetime, time
import json

# Create your views here.
def home(request):
    tim = now()

    live = Competition.objects.filter(
        _utc_start_date__lte=tim,
        _utc_end_date__gte=tim,
        publication_policy="public"
    )
    upcoming = Competition.objects.filter(
        _utc_start_date__gt=tim,
        _utc_end_date__gt=tim,
        publication_policy="public"
    )
    past = Competition.objects.filter(
        _utc_start_date__lt=tim,
        _utc_end_date__lt=tim,
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
	competition_form = CompetitionForm()
	competitor_form = CompetitorForm()
	return render_to_response(
		'seuranta/dashboard.html',
		{
		    'competition_form':competition_form,
		    'competitor_form':competitor_form,
		},
		RequestContext(request)
	)

@login_required
@never_cache
def dashboard_edit_race(request, uuid):
	obj = get_object_or_404(
		Competition,
		uuid = uuid,
		publisher = request.user
	)
	if request.method == "POST":
		competition_form = CompetitionForm(request.POST, request.FILES, instance=obj)
		competitor_formset = CompetitorFormSet(request.POST, instance=obj)
		if competition_form.is_valid() and competitor_formset.is_valid():
			competition_form.save()
			competitor_formset.save()
			return HttpResponseRedirect(reverse('seuranta.views.dashboard'))
	else:
		competition_form = CompetitionForm(instance=obj)
		competitor_formset = CompetitorFormSet(instance=obj)

	return render_to_response(
		'seuranta/competition_editor.html',
		{
		    'competition':obj,
		    'form':competition_form,
		    'competitor_formset':competitor_formset,
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
        if c.last_update < c.utc_start_date and tim > c.utc_start_date:
            return c.utc_start_date
        return c.last_update
    return None

@condition(last_modified_func=latest_competition_mod, etag_func=None)
def race_view(request, uuid):
    obj = get_object_or_404(Competition, uuid=uuid)
    if obj.publication_policy == "private" and obj.publisher != request.user:
        return HttpResponse(status=403)

    tim = now()
    if tim < obj.utc_start_date:
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
def api(request, action="update_track"):
    if request.method == "POST":
        if action == "delete_race":
            if not request.user.is_authenticated():
                return HttpResponse(status=403)

            uuid = request.POST.get('uuid')
            obj = get_object_or_404(
                Competition,
                uuid = uuid,
            )
            if obj.publisher != request.user:
                return HttpResponse(status=403)

            obj.delete()
            return HttpResponse("OK")

    	elif action == "update_track":
            uuid = request.POST.get("secret")
            encoded_data = request.POST.get("encoded_data")

            if encoded_data is None or len(encoded_data)==0:
                try:
                    lat = float(request.POST.get("latitude"))
                    lon = float(request.POST.get("longitude"))
                    tim = time.time()
                    route = [{'t':tim, 'lat':lat, 'lon':lon}]
                except:
                    route = None
            else:
                try:
                    route = gps_codec.decode(encoded_data)
                except:
                    route = None

            if route is None:
                return HttpResponse("No route data")

            if uuid is not None and route is not None:
                try:
                    tracker = Tracker.objects.get(uuid=uuid)
                except Tracker.DoesNotExist:
                    return HttpResponse("Secret do not match any tracker")

                tim = now()
                competitors = tracker.competitors.filter(
                    competition___utc_start_date__lt=tim,
                    competition___utc_end_date__gt=tim
                )

                if len(competitors)==0:
                    return HttpResponse("No competitor assigned")

                for c in competitors:
                    section = RouteSection(competitor=c)
                    section.route = route
                    section.save()

                return HttpResponse("OK")
            return HttpResponse("Invalid parameters")
    else:
        if action == "get_time":
            server_time = time.time()*1e3
            response = {'time':server_time/1e3}
            try:
                request_time = float(request.GET.get("t"))*1e3
            except:
                request_time = None
            if request_time is not None:
                drift = server_time-request_time
                response['drift']=drift/1e3

            return HttpResponse(json.dumps(response), content_type='application/json')

        elif action == "get_route":
            uuids = request.GET.getlist('uuids[]')

            last_update_raw = request.GET.get("last_update",None)
            time_start_raw = request.GET.get("timestamp_start",None)
            time_end_raw = request.GET.get("timestamp_end",None)

            last_update = None
            if last_update_raw is not None:
                try:
                    last_update = utc.localize(datetime.datetime.fromtimestamp(float(last_update_raw)/1e3))
                except ValueError:
                    pass

            time_start = None
            if time_start_raw is not None:
                try:
                    time_start = utc.localize(datetime.datetime.fromtimestamp(float(time_start_raw)/1e3))
                except ValueError:
                    pass

            time_end = None
            if time_end_raw is not None:
                try:
                    time_end = utc.localize(datetime.datetime.fromtimestamp(float(time_end_raw)/1e3))
                except ValueError:
                    pass

            if len(uuids)>0:
                query = reduce(lambda query,uuid:query|Q(uuid=uuid), uuids, Q())

                competitors = Competitor.objects.filter(query)
                result = {'result':[]}
                if len(competitors)==0:
                    return HttpResponse(json.dumps(result), content_type='application/json')

                query = reduce(lambda q,competitor:q|Q(competitor_id=competitor.id), competitors, Q())

                if last_update is not None:
                    query &= Q(last_update__gte=last_update)

                route_sections = RouteSection.objects.filter(query)

                for route_section in route_sections:
                    timestamp = (route_section.last_update.replace(tzinfo=None) - datetime.datetime.utcfromtimestamp(0)).total_seconds()
                    result['result'].append({
                        'competitor_id':route_section.competitor.uuid,
                        'timestamp':timestamp,
                        'encoded_route':route_section.encoded_data
                    })
                return HttpResponse(json.dumps(result), content_type='application/json')

    return HttpResponse("")
