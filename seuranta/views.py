from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.views.decorators.http import condition
from seuranta.models import BLANK_GIF, BLANK_FORMAT

from seuranta.models import Competition
from seuranta.utils.validators import validate_short_uuid

User = get_user_model()


def home(request):
    timestamp = now()
    qs = Competition.objects.filter(
        publication_policy="public"
    )
    live = qs.filter(
        start_date__lte=timestamp,
        end_date__gte=timestamp
    ).order_by('start_date')
    upcoming = qs.filter(
        start_date__gt=timestamp,
        end_date__gt=timestamp,
    ).order_by('start_date')
    past = qs.filter(
        start_date__lt=timestamp,
        end_date__lt=timestamp,
    ).order_by('-end_date')
    return render_to_response(
        'seuranta/index.html',
        {
            'live': live,
            'upcoming': upcoming,
            'past': past,
        },
        RequestContext(request)
    )


def user_home(request, publisher):
    timestamp = now()
    user = get_object_or_404(User, username__iexact=publisher)
    qs = Competition.objects.filter(publisher=user)
    live = qs.filter(
        start_date__lte=timestamp,
        end_date__gte=timestamp,
        publication_policy="public"
    )
    upcoming = qs.filter(
        start_date__gt=timestamp,
        end_date__gt=timestamp,
        publication_policy="public"
    )
    past = qs.filter(
        start_date__lt=timestamp,
        end_date__lt=timestamp,
        publication_policy="public"
    )
    return render_to_response(
        'seuranta/home.html',
        {
            'live': live,
            'upcoming': upcoming,
            'past': past,
            'owner': user,
        },
        RequestContext(request)
    )


def tracker(request, api_token=None):
    if api_token is not None:
        try:
            validate_short_uuid(api_token)
        except ValidationError:
            return HttpResponse(status=404)
        else:
            tracker_api_token = api_token
    else:
        tracker_api_token = None
    return render_to_response(
        'seuranta/tracker.html',
        {'api_token': tracker_api_token},
        RequestContext(request)
    )


def race_latest_mod(request, publisher, slug):
    try:
        user = User.objects.get(username__iexact=publisher)
    except User.DoesNotExist:
        return None
    try:
        competition = Competition.objects.get(
            publisher=user,
            slug=slug,
        )
    except Competition.DoesNotExist:
        return None
    if competition.update_date < competition.start_date < now():
        return competition.start_date
    return competition.update_date


@condition(last_modified_func=race_latest_mod, etag_func=None)
def race_view(request, publisher, slug):
    user = get_object_or_404(
        User,
        username__iexact=publisher
    )
    competition = get_object_or_404(
        Competition,
        slug=slug,
        publisher=user
    )
    if competition.publication_policy == 'private' \
       and competition.publisher != request.user \
       and not request.user.is_superuser:
        return HttpResponse(status=403)
    if competition.start_date > now():
        return render_to_response(
            'seuranta/pre_race.html',
            {
                'competition': competition,
            },
            RequestContext(request)
        )
    return render_to_response(
        'seuranta/race.html',
        {
            'competition': competition,
        },
        RequestContext(request)
    )


def map_latest_mod(request, pk):
    try:
        competition = Competition.objects.get(
            pk=pk
        )
    except Competition.DoesNotExist:
        return None
    if request.user == competition.publisher:
        if not competition.map.update_date:
            return competition.update_date
        else:
            return competition.map.update_date
    if not competition.map.update_date:
        if competition.update_date < competition.start_date < now():
            return competition.start_date
        else:
            return competition.update_date
    elif competition.map.update_date < competition.start_date < now():
        return competition.start_date
    return competition.map.update_date


@condition(last_modified_func=map_latest_mod, etag_func=None)
def download_map(request, pk):
    competition = get_object_or_404(Competition, pk=pk)
    if any([all([not request.user.is_anonymous(),
                 competition.publisher == request.user]),
            all([competition.publication_policy != 'private',
                 competition.is_started])]):
        response = competition.map.image_data
        mime = competition.map.format
        return HttpResponse(response, content_type=mime)
    else:
        return HttpResponse(status=403)


def admin_map_image(request, publisher, hash, pk):
    if request.user.is_anonymous() \
       or publisher != request.user.username:
        print request.user.username, publisher
        return HttpResponse(status=403)
    competition = get_object_or_404(Competition, pk=pk)
    response = competition.map.image_data
    mime = competition.map.format
    return HttpResponse(response, content_type=mime)
