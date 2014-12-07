import simplejson as json
import time

from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import condition
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.utils.timezone import now
from django.contrib.sites.models import get_current_site
from django.contrib.auth import get_user_model
from seuranta.models import Competition, RouteSection
from seuranta.views import race_latest_mod


RERUN_TEMPLATE_URL = "http://3drerun.worldofo.com/2d/index.php" \
                     "?liveid=%s&lservice=dseu"

@condition(last_modified_func=race_latest_mod, etag_func=None)
def rerun_redirect(request, publisher, slug):
    user = get_object_or_404(
        get_user_model(),
        username__iexact=publisher
    )
    tim = now()
    obj = get_object_or_404(
        Competition,
        slug=slug,
        publisher=user,
        end_date__lt=tim
    )
    if obj.publication_policy == 'private' and obj.publisher != request.user:
        return HttpResponse(status=403)
    return HttpResponseRedirect(
        RERUN_TEMPLATE_URL % obj.id
    )



def rerun_time(request):
    response = {}
    timestamp = time.time()
    response['time'] = "%f" % timestamp
    response_json = json.dumps(response)
    if 'jsoncallback' in request.REQUEST \
       and request.REQUEST['jsoncallback'] != "":
        response_jsonp = '%s(%s);' % (request.REQUEST['jsoncallback'],
                                      response_json)
        return HttpResponse(response_jsonp,
                            content_type='application/javascript')
    return HttpResponse(response_json, content_type='application/json')


def rerun_init(request):
    response = {}
    if 'id' in request.REQUEST:
        obj_id = request.REQUEST['id']
        try:
            competition = Competition.objects.get(id=obj_id,
                                                  start_date__lte=now())
        except Competition.DoesNotExist:
            pass
        else:
            response['status'] = "OK"
            response['caltype'] = "3point"
            if competition.map is None or not competition.map.is_calibrated:
                response['mapw'] = "1"
                response['maph'] = "1"
            else:
                response['mapw'] = "%d" % competition.map.width
                response['maph'] = "%d" % competition.map.height
            protocol = "http"
            if request.is_secure():
                protocol += "s"
            domain = (get_current_site(request)).domain
            response['mapurl'] = "%s://%s%s?id=%s" % (
                protocol,
                domain,
                reverse("seuranta_rerun_map"),
                competition.pk
            )
            response['calibration'] = competition.map.calibration_string
            competitors = competition.competitors.all().order_by('id')
            list_competitors = []
            for competitor in competitors:
                start_time = competitor.start_time
                if start_time is None:
                    start_time = competition.start_date
                list_competitors.append(";".join([
                    competitor.id,
                    start_time.strftime("%Y%m%d%H%M%S"),
                    competitor.name
                ]))
            response['competitors'] = ":".join(list_competitors)
    response_json = json.dumps(response)
    if 'jsoncallback' in request.REQUEST \
       and request.REQUEST['jsoncallback'] != "":
        response_jsonp = '%s(%s);' % (request.REQUEST['jsoncallback'],
                                      response_json)
        return HttpResponse(response_jsonp,
                            content_type='application/javascript')
    return HttpResponse(response_json, content_type='application/json')


def rerun_data(request):
    response = {}
    if 'id' in request.REQUEST:
        obj_id = request.REQUEST['id']
        try:
            competition = Competition.objects.get(id=obj_id, start_date__lte=now())
        except Competition.DoesNotExist:
            pass
        else:
            response['status'] = "OK"
            competitors = competition.competitors.all().order_by('id')
            competitors_id = competitors.values_list('id', flat=True)
            sections = RouteSection.objects.filter(
                competitor_id__in=competitors_id
            ).order_by('update_date')
            points_count = 0
            list_points = []
            for section in sections:
                points = section.route
                for point in points:
                    points_count += 1
                    list_points.append(";".join([
                        section.competitor_id,
                        "%f" % point.timestamp,
                        "%f" % point.coordinates.latitude,
                        "%f" % point.coordinates.longitude
                    ]))
            try:
                offset = int(request.REQUEST.get('p', 0))
            except (ValueError, TypeError):
                offset = 0
            response['data'] = ":".join(list_points[offset:])
            response['lastpos'] = "%d" % points_count
    response_json = json.dumps(response)
    if 'jsoncallback' in request.REQUEST \
       and request.REQUEST['jsoncallback'] != "":
        response_jsonp = '{}({});'.format(request.REQUEST['jsoncallback'],
                                          response_json)
        return HttpResponse(response_jsonp,
                            content_type='application/javascript')
    return HttpResponse(response_json, content_type='application/json')


def rerun_map(request):
    obj_id = request.REQUEST.get('id', None)
    return download_map(request, obj_id)
