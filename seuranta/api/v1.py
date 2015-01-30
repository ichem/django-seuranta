import datetime
import json
import time

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.utils.timezone import utc, now
from django.views.decorators.cache import cache_page
from django.core.exceptions import ValidationError

from seuranta.models import Competition, Competitor, Route
from seuranta.utils import format_date_iso
from seuranta.utils.validators import validate_short_uuid
from seuranta.utils.geo import GeoLocation, GeoLocationSeries


def competition_list(request):
    competitions = Competition.objects.filter(
        end_date__gt=now(),
    ).values_list('name', 'id', 'start_date', 'end_date')
    data = [{
        "name": x[0],
        "id": x[1],
        "start_date": format_date_iso(x[2]),
        "end_date": format_date_iso(x[3])
    } for x in competitions]
    return {
        "status": "OK",
        "code": 200,
        "msg": "",
        "data": {
            "results": data
        },
    }


def competitor_get_token(request):
    competition_id = request.REQUEST.get("competition_uuid")
    code = request.REQUEST.get("code")
    competitors = Competitor.objects.filter(competition_id=competition_id,
                                            quick_setup_code=code)
    if competitors.count() == 0:
        response = {
            "status": "KO",
            "code": 404,
            "msg": "Does not exist",
            "data": {}
        }
    else:
        competitor = competitors[0]
        response = {
            "status": "OK",
            "code": 200,
            "msg": "Data received",
            "data": {
                "api_token": competitor.api_token
            }
        }
    return response


def receive_data(request):
    api_token = request.REQUEST.get("secret")
    try:
        validate_short_uuid(api_token)
    except ValidationError:
        return {
            "status": "KO",
            "code": 404,
            "msg": "Invalid secret",
            "data": {
                "secret": api_token
            }
        }
    else:
        route = None
        if 'encoded_data' in request.REQUEST:
            encoded_data = request.REQUEST.get("encoded_data")
            try:
                route = GeoLocationSeries(encoded_data)
            except (TypeError, ValueError):
                 return {
                    "status": "KO",
                    "code": 400,
                    "msg": "Encoded data corrupted",
                    "data": {
                        "secret": api_token,
                        "encoded_data": encoded_data,
                    }
                }
        elif 'latitude' in request.REQUEST \
             and 'longitude' in request.REQUEST:
            try:
                lat = float(request.REQUEST.get("latitude"))
                lon = float(request.REQUEST.get("longitude"))
                tim = time.time()
            except (ValueError, TypeError):
                return {
                    "status": "KO",
                    "code": 400,
                    "msg": "Invalid data latitude/longitude",
                    "data": {
                        "secret": api_token,
                    }
                }
            else:
                location = GeoLocation(tim, (lat, lon))
                route = [location]
        if route is not None and len(route) > 0:
            tim = now()
            live_competitors = Competitor.objects.filter(
                api_token=api_token,
                competition__start_date__lte=tim,
                competition__end_date__gte=tim,
            )
            future_competitors = Competitor.objects.filter(
                api_token=api_token,
                competition__start_date__gt=tim,
            )
            next_start = None
            if len(future_competitors) > 0:
                next_competitor = future_competitors.order_by(
                    'competition__start_date'
                )[0]
                next_start = format_date_iso(
                    next_competitor.competition.start_date
                )
            for competitor in live_competitors:
                if competitor.approved \
                   or competitor.competition.signup_policy == "open":
                    section = Route(competitor=competitor)
                    section.route = route
                    section.save()
            last_location = route[-1]
            last_location_obj = {
                "timestamp": last_location.timestamp,
                "coordinates": {
                    "latitude": last_location.coordinates.latitude,
                    "longitude": last_location.coordinates.longitude,
                }
            }
            return {
                "status": "OK",
                "code": 200,
                "msg": "Data received",
                "data": {
                    "secret": api_token,
                    "last_location": last_location_obj,
                    "locations_received_count": len(route),
                    "live_competitors_count": live_competitors.count(),
                    "next_competition_start": next_start,
                }
            }
    return None


def clock_drift(request):
    try:
        timestamp = float(request.REQUEST.get('timestamp'))
    except (ValueError, TypeError):
        return {
            "status": "KO",
            "code": 400,
            "msg": "Invalid data",
            "data": {
                "timestamp": request.REQUEST.get('timestamp'),
            }
        }
    else:
        tim = time.time()
        return {
            "status": "OK",
            "code": 200,
            "msg": "",
            "data": {
                "server_time": tim,
                "timestamp": timestamp,
                "drift": tim-timestamp,
            }
        }


def competitors_routes(request):
    raw_competitors_id = request.REQUEST.getlist('uuid[]')
    last_update_timestamp = request.REQUEST.get(
        "last_update_timestamp", None
    )
    last_update_datetime = None
    if last_update_timestamp is not None:
        try:
            last_update_timestamp = float(last_update_timestamp)
            last_update_datetime = utc.localize(
                datetime.datetime.fromtimestamp(last_update_timestamp)
            )
        except ValueError:
            pass
    # min_timestamp = request.REQUEST.get("min_timestamp", None)
    # max_timestamp = request.REQUEST.get("max_timestamp", None)
    # max_datetime = None
    # if max_timestamp is not None:
    #     try:
    #         max_timestamp = float(max_timestamp)
    #         max_datetime = utc.localize(
    #             datetime.datetime.fromtimestamp(max_timestamp)
    #         )
    #     except ValueError:
    #         pass
    # min_datetime = None
    # if min_timestamp is not None:
    #     try:
    #         min_timestamp = float(min_timestamp)
    #         min_datetime = utc.localize(
    #             datetime.datetime.fromtimestamp(min_timestamp)
    #         )
    #     except ValueError:
    #         pass
    if len(raw_competitors_id) > 0:
        valid_competitors_id = Competitor.objects.filter(
            uuid__in=raw_competitors_id
        ).values_list('pk', flat=True)
        response = {
            "status": "OK",
            "code": 200,
            "msg": "",
            "data": {
                "routes": []
            }
        }
        if len(valid_competitors_id) > 0:
            # extra param as view bound, last update...
            extra_query = Q()
            if last_update_datetime is not None:
                extra_query &= Q(last_update__gte=last_update_datetime)
            route_sections = Route.objects.filter(
                extra_query, competitor_id__in=valid_competitors_id
            )
            for route_section in route_sections:
                timestamp = (
                    route_section.last_update.replace(tzinfo=None)
                    - datetime.datetime.utcfromtimestamp(0)
                ).total_seconds()
                response['data']['routes'].append({
                    'competitor': {
                        'uuid': route_section.competitor.uuid,
                    },
                    'udpate_timestamp': timestamp,
                    'encoded_data': route_section.encoded_data
                })
        return response


@csrf_exempt
@cache_page(5)
def api_v1(request, action):
    response = {
        "status": "KO",
        "code": 400,
        "msg": "Invalid api request",
        "data": {
            "help": ""
        }
    }
    if action == "competition/list":
        response = competition_list(request)
    elif action == "competitor/retrieve":
        response = competitor_get_token(request)
    elif action == "competitor/update":
        result = receive_data(request)
        if result is not None:
            response = result
    elif action == "clock/drift":
        response = clock_drift(request)
    elif action == "competitors/routes":
        result = competitors_routes(request)
        if result is not None:
            response = result
    else:
        response["msg"] = "API endpoint does not exist."
        response["data"]["endpoint"] = action
    response_json = json.dumps(response, use_decimal=True)
    if 'callback' in request.REQUEST and request.REQUEST['callback'] != "":
        response_jsonp = '%s(%s);' % (request.REQUEST['callback'],
                                      response_json)
        return HttpResponse(response_jsonp,
                            content_type='application/javascript')
    return HttpResponse(response_json, content_type='application/json')
